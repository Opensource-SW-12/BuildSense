# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the app

```
python main.py
```

Requires Windows (uses `ctypes.windll`, WMI/PowerShell, `nvidia-smi`). Dependencies: `pip install -r requirements.txt`.

## Environment variables

API 키는 프로젝트 루트의 `.env` 파일에 설정. `.env`는 `.gitignore`에 포함되어 GitHub에 올라가지 않음.

```
NAVER_CLIENT_ID=
NAVER_CLIENT_SECRET=
EBAY_ACCESS_TOKEN=
```

`.env.example`을 복사해 `.env`로 이름을 바꾸고 키를 채우면 됨. `main.py`에서 `load_dotenv()`로 자동 로드.

**주의:** eBay Access Token에 `#` 문자가 포함되어 있으면 python-dotenv가 주석으로 처리해 잘립니다. 반드시 따옴표로 감싸야 합니다.
```
EBAY_ACCESS_TOKEN="v^1.1#i^1#..."
```

eBay Application Token 유효기간은 **2시간**. 만료 시 Developer Portal에서 재발급하거나 Client Credentials 자동 갱신 로직 추가 필요 (미구현).

## Architecture overview

BuildSense is a Windows Tkinter desktop app that monitors system resource usage over a user-defined period and produces hardware upgrade recommendations with an HTML report.

**Startup flow** (`main.py`):
1. `load_dotenv(_base / ".env")` — EXE 빌드 시 `sys.executable` 기준, 개발 시 `__file__` 기준으로 `.env` 로드 (KAN-107).
2. Acquire a Windows Named Mutex (`BuildSense_SingleInstance_Mutex`) via `background.acquire_single_instance_lock()` — if already running, show status window (`instance_status.py`) and exit.
3. `storage.ensure_app_directories()` creates `data/`, `logs/`, `reports/`, `results/`, `exports/`, `data/specs/`, `data/prices/` relative to the project root.
4. `detect_startup_state()` → `FRESH` / `RESUME` / `ANALYZE` 판별.
5. `BuildSenseApp(startup_state).run()` enters the Tkinter main loop.

**재부팅 후 자동 재개:**  
EXE 빌드 시 `startup_registry.py`가 `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`에 등록. 재부팅 후 자동 실행 → `RESUME` 상태면 동의 화면 없이 모니터링 화면으로 바로 진입. Named Mutex는 커널 객체이므로 재부팅 시 자동 소멸되어 중복 실행 방지가 정상 동작함.

**UI model** (`src/app.py`):  
Single `tk.Tk` root window. Screen transitions work by destroying all children (`_clear_window()`) and rebuilding. Screens in order: consent → (hardware loading in daemon thread) → settings → review dialog → monitoring.

**Monitoring** (`src/monitor.py`):  
Background daemon thread polls every 60 s (`MONITOR_INTERVAL_SECONDS`). Each tick calls `collect_monitoring_snapshot()` — CPU%, RAM%, NVIDIA GPU%/VRAM via `nvidia-smi`, top-15 processes by CPU+RAM, disk partitions, uptime — and appends one JSON line to `logs/usage.jsonl`. Abort is signaled via a sentinel file (`data/buildsense_abort.signal`) so the monitoring process can be stopped from a second-instance window.

**Key data files** (all paths in `src/config.py`):
- `data/user_profile.json` — saved after settings review; contains consent, knowledge level, analysis days, per-part options.
- `logs/usage.jsonl` — one monitoring snapshot per line (JSONL).
- `data/process_categories.json` — 프로세스 이름 → 카테고리 매핑; `PROCESS_CATEGORIES_PATH`로 참조, `process_usage.py`에서 모듈 레벨에 캐시.

**Module responsibilities:**
| File | Role |
|------|------|
| `src/app.py` | All UI and screen-transition logic |
| `src/monitor.py` | Monitoring loop + snapshot assembly; uses `get_boot_and_uptime()` for single `psutil.boot_time()` call |
| `src/hardware.py` | One-time hardware detection (WMI/psutil/nvidia-smi); `_get_disks_by_type()` runs PowerShell **once** for both SSD and HDD |
| `src/gpu.py` | NVIDIA GPU metrics via `nvidia-smi`; `collect_gpu_snapshot()` is the sole public entry point |
| `src/process_tracker.py` | Top-15 processes snapshot; `get_boot_and_uptime()` returns boot time and uptime from a single `psutil.boot_time()` call |
| `src/background.py` | Daemon thread lifecycle + Windows Named Mutex |
| `src/storage.py` | All file I/O (profile, log, abort signal); tracks log line count in memory via `_log_line_count` — call `init_log_line_count()` on RESUME, `get_log_line_count()` to read |
| `src/config.py` | Path constants — single source of truth for file locations; `ANALYSIS_DIR = results/`, `PROCESS_CATEGORIES_PATH = data/process_categories.json` |
| `src/settings.py` | UI constants (parts list, knowledge levels, descriptions) and default state builder |
| `src/validators.py` | `ValidationResult` dataclass + validation functions; new error codes go in `ErrorCode` enum |
| `src/instance_status.py` | Window shown when a second instance is launched |
| `src/startup_state.py` | Detects startup mode (`FRESH` / `RESUME` / `ANALYZE`) by comparing profile and first log timestamp |
| `src/startup_registry.py` | Windows registry operations for auto-startup registration (frozen/EXE build only — `sys.frozen` 확인) |
| `src/analysis/resource_usage.py` | CPU/RAM/GPU/VRAM analysis with high-load ratios |
| `src/analysis/usage_pattern_summary.py` | Time-of-day and weekday patterns, continuous usage segments (2-hour gap = new segment); `parsed_times` is sorted once inside `create_usage_pattern_summary()` and shared with all helpers |
| `src/analysis/disk_usage.py` | Per-drive capacity stats; detects SSD/HDD/NVMe via PowerShell WMI |
| `src/analysis/process_usage.py` | Top processes by frequency/CPU/memory; `process_categories.json` is loaded once and cached at module level |
| `src/analysis/user_type.py` | Classifies user type (game, development, etc.) from process categories and hardware signals |
| `src/analysis/score_disk_base.py` | Shared disk scoring constants (`_W_PERCENT_P80`, `_W_DANGER`, `_W_FREE_PENALTY`, penalty bounds) and `capacity_score()` used by both SSD and HDD scorers |
| `src/analysis/score_cpu.py` | CPU upgrade score and grade (low/medium/high) |
| `src/analysis/score_ram.py` | RAM upgrade score and grade |
| `src/analysis/score_gpu_vram.py` | GPU/VRAM upgrade score and grade; returns `"unknown"` grade when GPU not detected |
| `src/analysis/score_ssd.py` | SSD upgrade score; imports `capacity_score` from `score_disk_base` |
| `src/analysis/score_hdd.py` | HDD upgrade score with floor of 0.3 (minimum medium); imports `capacity_score` from `score_disk_base` |
| `src/analysis/score_psu.py` | PSU efficiency tier recommendation (gold/platinum/titanium) based on uptime; gold=낮음, platinum=보통, titanium=높음 |
| `src/normalization/core.py` | Basic stats (min/max/avg/median/p80), 3σ outlier removal, min-max normalization |

**Parts tracked:** CPU, GPU, RAM, SSD, HDD, 파워 (PSU). PSU cannot be auto-detected — always returns "확인할 수 없음".

**Knowledge levels:** `beginner` / `intermediate` / `advanced` — controls which description text is shown per part and whether per-part radio buttons are enabled (beginners are forced to "recommend" for all parts).

**Per-part options:** `recommend` / `exclude` / `keep` (show current hardware) / `decided` (manual text input). Validation rule: at least one part must not be `keep`.

## Pricing module (`src/pricing/`)

하드웨어 업그레이드 후보 가격 조회 모듈. UI와 아직 미연결 (추후 연결 예정).

| File | Role |
|------|------|
| `src/pricing/price_fetcher.py` | 네이버 쇼핑 API / eBay Browse API 검색 및 후보 추출 |
| `src/pricing/product_matcher.py` | `is_matching_product(title, part)` — 제품명이 부품 스펙과 일치하는지 판별 |
| `src/pricing/price_candidate_storage.py` | 가격 후보 JSON 저장/로드 (`data/prices/`) |
| `src/pricing/exchange_rate.py` | open.er-api.com에서 USD→KRW 환율 조회; `convert_usd_to_krw()` |

**product_matcher.py 주요 로직 (KAN-94, KAN-102):**
- `_MANUFACTURER_ALIASES` — 제조사 한/영 별칭 매핑 (삼성→삼성전자, lg→엘지 등). 네이버 쇼핑 한국어 제목 대응.
- `_manufacturer_matches()` — 별칭 포함 제조사 일치 검사.
- `_GPU_VARIANT_SUFFIXES = {"super", "ti", "xt", "xtx", "ultra", "gre"}` — GPU 변형 모델 접미사 목록.
- `_chipset_matches()` — chipset 문자열 뒤에 variant 접미사가 오면 다른 모델로 판단해 `False` 반환. RTX 4070이 RTX 4070 SUPER를 오매칭하던 문제 수정.
- GPU 섹션: `chipset`이 None이면 조건 건너뜀 (KAN-94 반전 버그 수정).

## Report module (`src/report/`)

분석 결과를 HTML 보고서로 출력. `generate_report()` 1개 함수가 진입점.

```python
from src.report.report_generator import generate_report
generate_report()  # 로그 로드 → 분석 → 차트 12개 생성 → HTML 저장 → 브라우저 오픈
```

보고서는 `reports/report_YYYYMMDD_HHMMSS.html`로 저장. 단독 HTML 파일 (base64 이미지 인라인 포함, 외부 의존 없음).

| File | Role |
|------|------|
| `src/report/font_config.py` | `setup_korean_font()` — `malgun.ttf` 자동 탐지 후 matplotlib 폰트 설정 |
| `src/report/report_data_collector.py` | `collect_report_data(logs, profile)` — 기존 analysis 모듈 전부 호출해 단일 dict 반환; `raw_series`(시계열), `pattern_series`(시·요일 집계) 포함 |
| `src/report/chart_builder.py` | matplotlib 차트 함수 12개 → base64 PNG 반환 |
| `src/report/html_builder.py` | `build_html(report_data, charts)` — 인라인 CSS + 6개 섹션 HTML 조립 |
| `src/report/report_generator.py` | `generate_report()` 진입점 |

**차트 목록:**

| 함수 | 섹션 |
|------|------|
| `build_cpu/ram/gpu/vram_chart` | 통계 바 + 시계열 꺾은선 (각 2열) |
| `build_time_pattern_chart` | 시간대별(0-23시) + 요일별 막대 |
| `build_usage_heatmap` | 요일 × 시간 히트맵 (YlOrRd) |
| `build_segment_summary_chart` | 활성 비율·연속 사용·비활성 구간 |
| `build_disk_chart` | 드라이브별 도넛 (사용률 색상) |
| `build_process_chart` | 출현빈도/CPU/메모리 Top 10 수평 막대 3열 |
| `build_category_chart` | 프로세스 카테고리 파이 |
| `build_score_radar_chart` | 5개 부품 레이더 |
| `build_score_summary_chart` | 부품별 점수 수평 막대 + 등급 경계선 |

**보고서 섹션:** 분석 요약 → 리소스 사용량 → 사용 패턴 → 디스크 현황 → 프로세스 분석 → 업그레이드 필요도

**디자인 테마 (KAN-108):** 앱 UI와 통일된 다크 테마. 배경 `#0F1117`, 카드 `#161B2E`, 액센트 `#00D4AA`(teal), 경고 `#FF5252`. `chart_builder.py`의 matplotlib 차트도 동일 팔레트 적용 (`_BG`, `_AX_BG`, `_TEXT`, `_GRID` 상수).

**데모 스크립트:** `demo_report.py` — 더미 데이터(7일, 1500 스냅샷, 게임+개발 혼합 세션)로 보고서 생성. `python demo_report.py`로 실행.

## 추천 시스템 (`src/recommendation/`) — 미구현, 설계 완료

사용자 유형·점수 기반 하드웨어 업그레이드 추천. 7단계 파이프라인으로 설계됨.

| # | 단계 | 키워드 |
|---|------|--------|
| 1 | 입력 수집 | 자동수집, 예산·브랜드·RGB·색상 설정 |
| 2 | 티어 매핑 | chipset 파싱, `data/chipset_tiers.json` 조회 |
| 3 | 추천 대상 선정 | score × weight, grade 필터, 복합 유형 혼합 |
| 4 | 목표 티어 결정 | grade별 점프 폭(high +2~3, medium +1), 예산 조정 |
| 5 | 후보 필터링 | specs DB → 브랜드·RGB·색상·예산 순 필터 |
| 6 | 가격 조회 | 캐시 우선, 네이버/eBay API, product_matcher 검증 |
| 7 | 결과 조립 | PSU 의존성 검사, 이유 문구 생성, 최종 출력 |

**필요 데이터 파일 (미생성):**
- `data/chipset_tiers.json` — GPU/CPU/RAM chipset → tier 번호 매핑 (수동 관리)

**가중치 설계 근거:** CPU/RAM 점수의 `_W_P80=0.4`, `_W_HIGH_LOAD=0.4`, `_W_SUSTAINED=0.2`는 휴리스틱 초기값. 추후 PassMark/Tom's Hardware 벤치마크 데이터 기반으로 보완 예정. 가중치는 각 모듈 상단 상수로 분리되어 있어 수정 용이.
