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
EBAY_CLIENT_ID=
EBAY_CLIENT_SECRET=
```

**eBay 키 구조 (KAN-110, KAN-122):**
- `EBAY_CLIENT_ID` = eBay Developer Portal → App ID (Client ID)
- `EBAY_CLIENT_SECRET` = eBay Developer Portal → Cert ID (Client Secret)
- `EBAY_ACCESS_TOKEN`은 더 이상 사용하지 않음. `ebay_auth.py`가 Client ID + Secret으로 토큰을 자동 발급·2시간마다 갱신함.
- Client ID에 `SBX` 포함 시 Sandbox URL(`api.sandbox.ebay.com`) 자동 선택, 없으면 Production(`api.ebay.com`) 자동 선택.
- Sandbox는 실제 상품 데이터 없음 → 검색 결과 0개가 정상.

**동작 확인 완료:** 네이버 쇼핑 API ✅, eBay Production API ✅, USD→KRW 환율 변환 ✅

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

하드웨어 업그레이드 후보 가격 조회 모듈. `src/recommendation/recommendation_assembler.py` → `report_generator.py`를 통해 보고서에 연결 완료 (KAN-140~142). 단, `price_candidate_storage.py`(가격 캐시)와 eBay 검색은 아직 파이프라인에 미사용 — 네이버 쇼핑 API만 연결됨.

| File | Role |
|------|------|
| `src/pricing/price_fetcher.py` | 네이버 쇼핑 API / eBay Browse API 검색 및 후보 추출; `_ebay_search_url()`로 Sandbox/Production URL 자동 선택 |
| `src/pricing/ebay_auth.py` | `get_ebay_access_token()` — Client Credentials로 eBay 토큰 자동 발급·캐시·갱신; `_is_sandbox(client_id)`로 환경 자동 감지 |
| `src/pricing/product_matcher.py` | `is_matching_product(title, part)` — 제품명이 부품 스펙과 일치하는지 판별 |
| `src/pricing/price_candidate_storage.py` | 가격 후보 JSON 저장/로드 (`data/prices/`) |
| `src/pricing/exchange_rate.py` | open.er-api.com에서 USD→KRW 환율 조회; `convert_usd_to_krw()` |
| `src/pricing/passmark_tiering.py` | PassMark 웹 크롤링으로 CPU/GPU 벤치마크 점수 수집 → `performance_tier`(1~29) 계산 후 specs DB에 저장; `update_cpu_gpu_with_passmark()` 진입점 |

**product_matcher.py 주요 로직 (KAN-94, KAN-102):**
- `_MANUFACTURER_ALIASES` — 제조사 한/영 별칭 매핑 (삼성→삼성전자, lg→엘지 등). 네이버 쇼핑 한국어 제목 대응.
- `_manufacturer_matches()` — 별칭 포함 제조사 일치 검사.
- `_GPU_VARIANT_SUFFIXES = {"super", "ti", "xt", "xtx", "ultra", "gre"}` — GPU 변형 모델 접미사 목록.
- `_chipset_matches()` — chipset 문자열 뒤에 variant 접미사가 오면 다른 모델로 판단해 `False` 반환. RTX 4070이 RTX 4070 SUPER를 오매칭하던 문제 수정.
- GPU 섹션: `chipset`이 None이면 조건 건너뜀 (KAN-94 반전 버그 수정).

**passmark_tiering.py 주의사항 (KAN-122 버그 수정):**
- `enrich_parts_with_passmark()`: PassMark 미매칭 부품은 필드 추가 없이 원본 그대로 보존 (이전: 삭제 버그).
- `find_matching_passmark_data()`: `part_name=None`이면 조기 반환 (이전: 빈 문자열 오매칭 버그).
- 환율 조회는 루프 밖에서 1회만 실행 (이전: 부품마다 HTTP 요청 버그).
- tier 공식: `int((passmark_score / max_score) * 29)`, CPU max=80000, GPU max=41588.

**`.env` API 키 누락 시:** `price_fetcher.search_naver_shopping()`은 `NAVER_CLIENT_ID`/`NAVER_CLIENT_SECRET`이 없으면 `ValueError`를 던지지만, `price_resolver._safe_naver_search()`가 이를 잡아 빈 리스트(`[]`)를 반환해 파이프라인은 중단되지 않음 — 추천 카드(우선순위/목표 사양)는 정상 표시되고 "추천 제품/가격" 부분만 비어 보임. 인스톨러 배포본에서 `.env`를 채우지 않은 경우 흔히 발생.

**⚠ 알려진 환경 의존 문제 — PassMark 403 차단 시 CPU/GPU 추천 후보가 비어 보임 (2026-06-09 확인):**
`spec_candidate_filter.py`는 보고서를 생성할 때마다 `load_cpu_passmark_items()`/`load_gpu_passmark_items()`로
PassMark(`cpubenchmark.net`/`videocardbenchmark.net`)를 **실시간 크롤링**해 CPU/GPU 후보·가격을 만든다
(RAM/SSD/HDD는 PassMark 없이 스펙 기반 검색어만 생성하므로 영향 없음). 네트워크 환경에 따라 PassMark이
`HTTP 403 Forbidden`으로 요청을 차단하면:
- `_cpu_items`/`_gpu_items`가 빈 리스트가 되어 `candidates: []`
- 검색어도 `cands[0]["name"] if cands else "CPU"`처럼 의미 없는 한 단어(`"CPU"`/`"GPU"`)로 폴백
- 결과적으로 보고서의 CPU/GPU 추천 카드는 표시되지만(우선순위 %, 목표 Tier 등) 실제 후보 제품·검색어가 비어 보임

코드 버그가 아니라 **외부 사이트 차단 정책에 의한 데이터 소스 장애**이며, 재현하려면:
```python
from src.pricing.passmark_tiering import load_cpu_passmark_items
load_cpu_passmark_items()  # → RuntimeError: PassMark 페이지 요청 실패 (403 Forbidden)
```
`data/specs/cpu_specs.json`/`gpu_specs.json`에는 `performance_tier` 필드가 아직 채워져 있지 않음
(`update_cpu_gpu_with_passmark()` 미실행 상태) — 향후 캐싱/사전 적재 방식으로 개선한다면
미연결 상태인 `price_candidate_storage.py`를 활용하는 방안을 고려할 것.

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

**디자인 테마 (KAN-112):** 앱 UI와 통일된 다크 테마. 배경 `#0F1117`, 카드 `#161B2E`, 액센트 `#00D4AA`(teal), 경고 `#FF5252`. `chart_builder.py`의 matplotlib 차트도 동일 팔레트 적용 (`_BG`, `_AX_BG`, `_TEXT`, `_GRID` 상수).

**데모 스크립트:**
- `demo_report.py` — 더미 로그(KST 기준 매일 dev 10-15시 + idle 15-17시 + game 18-24시 세션, 7일 약 1,500스냅샷, CPU/RAM/GPU/VRAM/디스크 jitter 포함)로 가벼운 HTML 미리보기 생성 (`hw_info`/`recommendations` 미포함). `_generate_logs(gpu_name=None)`은 `simulate_user_answers.py`와 공유. `python demo_report.py`로 실행.
- `simulate_user_answers.py` / `.bat` — `demo_report._generate_logs()`의 더미 로그로 실제 `BuildSenseApp(StartupState.ANALYZE)`를 구동해 "추가 정보 입력" 다이얼로그 → 실제 `generate_report()`(hw_info+추천 포함)까지 전체 UI/보고서 흐름을 시연. 실행 전 기존 `logs/usage.jsonl` 등 사용자 데이터를 `.orig`로 백업하고 종료 시 자동 복원. BuildSense 프로젝트 루트에서 `.\simulate_user_answers.bat`으로 실행.

## 추천 시스템 (`src/recommendation/`) — 구현 완료, 보고서에 연결됨 (KAN-135~150)

사용자 유형·점수 기반 하드웨어 업그레이드 추천. 7단계 파이프라인 구현 완료, `recommendation_assembler.assemble_recommendations()`가 진입점이며 `report_generator.py`에서 호출됨.

| # | 단계 | 모듈 | 키워드 |
|---|------|------|--------|
| 1 | 입력 수집 | `user_input_dialog.py` | 예산·브랜드·RGB·색상, 미분류 프로세스 입력 |
| 2 | 티어 매핑 | `chipset_tier_mapper.py` | chipset 파싱, PassMark `performance_tier` 조회 |
| 3 | 추천 대상 선정 | `upgrade_target_selector.py` | score × weight, grade 필터, 복합 유형 혼합 |
| 4 | 목표 티어 결정 | `target_tier_calculator.py` | grade별 점프 폭(high +2~3, medium +1), 예산 조정 |
| 5 | 후보 필터링 | `spec_candidate_filter.py` | specs DB → PassMark 후보 최대 5개, 플랫폼/소켓 호환성 쿼리 |
| 6 | 가격 조회 | `price_resolver.py` | 네이버 쇼핑 API, product_matcher 검증 (eBay·캐시는 미사용) |
| 7 | 결과 조립 | `recommendation_assembler.py` | PSU 의존성 검사, 이유 문구 생성, 최종 출력 |

**메인보드 추천 (KAN-144~150):** `data/specs/board_specs.json`(2,152개) 기반. `user_preferences.json`의 `upgrade_motherboard: bool`에 따라 keep(현재 소켓 제약 필터) / recommend(소켓 무관 CPU + 메인보드 후보) 분기.

**티어 데이터:** `data/chipset_tiers.json` 대신 `passmark_tiering.py`의 `update_cpu_gpu_with_passmark()`로 specs DB에 `performance_tier` 필드 자동 주입. 수동 관리 불필요.

**가중치 설계 근거:** CPU/RAM 점수의 `_W_P80=0.4`, `_W_HIGH_LOAD=0.4`, `_W_SUSTAINED=0.2`는 휴리스틱 초기값. 추후 PassMark/Tom's Hardware 벤치마크 데이터 기반으로 보완 예정 (발표 피드백). 가중치는 각 모듈 상단 상수로 분리되어 있어 수정 용이.

## 빌드 및 배포 (PyInstaller + Inno Setup, KAN-173)

`KAN-173-feature-pyinstaller-build-setup` 브랜치에서 Windows 배포용 EXE/인스톨러 빌드 체계 완성 (pytest 153개 통과 + 빌드된 EXE/인스톨러 설치·실행·제거까지 직접 검증 완료, PR 대기 중).

- **`src/config.py`**: `BASE_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent` — frozen 빌드에서 `data/`/`logs/`/`reports/`/`results/`/`exports/` 등 모든 경로가 EXE 옆을 가리키도록 수정 (`main.py`의 `.env` 로드 패턴(KAN-107)과 동일한 방식).
- **배포 형태**: `--onedir` (onefile 아님 — 부팅 시 자동 재시작되는 앱 특성상 매번 재압축 해제되는 지연을 피하기 위함). `BuildSense.spec`으로 빌드 → `dist/BuildSense/BuildSense.exe` + `_internal/`.
- **`build.ps1`**: 빌드 후 `data/specs/`, `data/process_categories.json`, `data/process_path_overrides.json`, `data/.gitkeep`, `.env.example`을 `dist/BuildSense/`로 복사. `.env`(API 키)는 복사하지 않음 — 사용자가 직접 채워야 함.
- **`main.py --unregister-startup`**: `startup_registry.unregister_startup()` 호출 후 즉시 종료하는 CLI 플래그. Inno Setup `[UninstallRun]`에서 부팅 자동실행 레지스트리 정리용으로 사용.
- **`installer/BuildSense.iss`** (Inno Setup): `DefaultDirName={localappdata}\Programs\BuildSense`, `PrivilegesRequired=lowest` — 관리자 권한 없이 사용자별 설치. `dist/BuildSense/*` 전체 복사 + 시작 메뉴 바로가기, 제거 시 `BuildSense.exe --unregister-startup` 실행.

**다른 컴퓨터에 배포 시 주의점:**
- 핵심 로직(하드웨어 감지·점수·보고서)은 머신 독립적 — `get_hardware_info()`/`_get_gpu()`는 PowerShell/WMI/`nvidia-smi`를 그 컴퓨터에서 직접 호출하고, 실패 시 `"확인할 수 없음"`/`"unknown"` 등급으로 안전하게 폴백하므로 사양이 다른 PC에서도 정상 동작.
- **`.env` 미동봉**: 새 컴퓨터마다 `.env.example`을 복사해 NAVER/eBay 키를 직접 채워야 가격 조회가 동작 (안 채워도 크래시는 없음 — 위 "`.env` API 키 누락 시" 참고).
- **코드 미서명**: 처음 실행하는 PC에서 Windows SmartScreen("Windows에서 PC를 보호함") 경고가 뜰 수 있음 — "추가 정보 → 실행"으로 우회 필요.
- **데모 스크립트 미포함**: `demo_report.py`/`simulate_user_answers.py`는 개발용이며 인스톨러 EXE에는 포함되지 않음 — 설치본은 `main.py`의 정상 FRESH/RESUME/ANALYZE 흐름(실제 7일 모니터링)으로만 동작.
- **범위 외 (향후 과제)**: 앱 아이콘(.ico), 버전 리소스, 코드 서명, API 키/specs DB를 옮기는 프록시 서버.

## 브랜치 현황 (2026-06-09 기준)

### main에 머지 완료
- KAN-84~87: 하드웨어 탐지 최적화
- KAN-93~100: HTML 보고서 생성기
- KAN-102 (PR #75): product_matcher GPU variant·제조사 별칭 수정
- KAN-107 (PR #79): main.py EXE 경로 기반 .env 로드
- KAN-109 (PR #81): passmark_tiering.py — PassMark 크롤링 기반 tier 산출
- KAN-110 (PR #83): ebay_auth.py — eBay 토큰 자동 발급·갱신
- KAN-112 (PR #84): 보고서 다크 테마 + demo_report.py
- KAN-135~141: 추천 파이프라인 (사용자 입력 → tier 매핑 → 대상 선정 → tier 계산 → 후보 필터링 → 가격 조회 → 최종 조립)
- KAN-142 (PR #94/#95): HTML 보고서 추천 섹션 + falsy 체크 수정

### PR 대기 중
- `KAN-173-feature-pyinstaller-build-setup` (2026-06-11): PyInstaller onedir 빌드 + Inno Setup 인스톨러 (위 "빌드 및 배포" 섹션 참고). pytest 153개 통과 + EXE/인스톨러 설치·실행·제거 직접 검증 완료.
- `KAN-122-fix-ebay-sandbox-passmark-bugs`: passmark_tiering 버그 3개 수정 + eBay Sandbox/Production URL 자동 감지
- `KAN-144-normalize-motherboard-specs-db`: board_specs.json (메인보드 2,152개)
- `KAN-145-148-motherboard-recommendation-system`: 메인보드 추천 시스템 + 플랫폼 호환성 쿼리
- `KAN-149-fix-chipset-rank-lookup`: 칩셋 rank 조회 버그 수정
- `KAN-154-ui-sync-custom-tkinter` (PR 미생성, origin에 푸시 완료): UI 다크 테마 동기화 + 보고서 사용자 입력/예산 가이드 개선 (아래 "완료" 항목 참고). PR 생성 링크: https://github.com/Opensource-SW-12/BuildSense/pull/new/KAN-154-ui-sync-custom-tkinter

### 완료 — KAN-154-ui-sync-custom-tkinter (커밋 ff2ce48, origin에 push 완료, 2026-06-09)
KAN-150 브랜치의 작업 상태(미커밋 변경분 전체)를 그대로 분기해 커밋·푸시함. 포함된 수정 사항:
- 예산 "설정 안 함" 체크박스: 다크 테마 Entry 색상 유지(`disabledbackground`/`disabledforeground`), 값은 "-"로 표시
- 지식 수준(`knowledge_level`)에 따라 RGB 선호도 설명 텍스트 조건부 표시 (advanced는 생략) — `_RGB_DESCRIPTIONS` in `user_input_dialog.py`
- 다크 테마 회색 텍스트 전반 밝기 조정: `app.py`/`user_input_dialog.py`의 `GRAY` `#7A8099`→`#9AA1C2`, 보고서 쪽 `#8892A4`→`#A6AEC8`
- `chart_builder.build_disk_chart()`: 드라이브 1개일 때 figsize를 `(6.5, 3.6)`로 별도 지정해 과대 확대 방지
- **메인보드 추천 누락 버그 수정**: `hw_info["CPU_socket"]`이 None인 노트북 등에서 PassMark 조회 실패(403) 시 메인보드 추천이 통째로 빠지던 문제 → `recommendation_assembler.py`에서 `infer_socket_from_cpu_name()` 폴백 추가, `platform_mapper.infer_socket_from_cpu_name()`은 "(R)"/"(TM)" 같은 상표 표기를 제거하는 정규식 보정 추가
- `html_builder.py`: 업그레이드 추천 퍼센트 표시 100% 상한 처리(`min(int(priority*100), 100)`)
- `html_builder.py`: 새 섹션 `_section_user_input()` 추가 — 최초 입력(설정 화면 동의/지식수준/분석기간/부품옵션)과 최종 입력(예산/RGB선호/미분류 프로세스)을 모두 표시. `report_generator.py`에서 `data["user_preferences"] = load_user_preferences()` 연결
- `html_builder.py`: `_rec_budget_guide_html()` 추가 — 추천 후보 최저가 기반 "권장 예산 가이드" 표시 + 입력 예산이 부족할 때 경고 문구
- `user_input_dialog.py`: 예산이 0보다 크고 `_MIN_REASONABLE_BUDGET`(100,000원) 미만이면 `messagebox.askyesno`로 저예산 경고

### 작업 중 — KAN-150-motherboard-in-settings-parts (KAN-154 분기 이전 브랜치, 계속 진행 중)
- 메인보드를 초기 설정 화면의 "추천 부품 선택"에 추가, 부품 옵션을 추천/유지 2가지로 통일 (제외·이미 결정·수동 입력 제거)
- **UI 다크 테마 전면 재설계** (`src/app.py`, `src/recommendation/user_input_dialog.py`, `src/settings.py`)
  - 모듈 레벨 다크 테마 팔레트 상수(`BG`/`CARD`/`TEAL`/`BLUE`/`RED`/`WHITE`/`GRAY`/`DIVIDER` 등)와 캔버스 기반 위젯 팩토리 `_pill()`/`_make_toggle()`/`_badge()` 도입
  - `_pill()`/`_make_toggle()`은 내부 Canvas/Frame 배경색을 부모 컨테이너에 맞추도록 `bg` 매개변수 지원 (기본 `BG`, `CARD` 컨테이너 안에서는 `bg=CARD` 전달)
  - 다이얼로그/창 크기는 고정값 대신 `winfo_reqheight()` 기반으로 동적 계산해 콘텐츠 잘림·여백 문제 방지 (`_show_review_dialog`의 동적 높이, `_show_monitoring_screen`의 `_resize_to_content()` — 중도 종료 카드 토글마다 재호출)
  - 스크롤 영역의 `<MouseWheel>` 바인딩은 `bind_all`/`unbind_all`을 `<Enter>`/`<Leave>`에 스코프 지정해 화면 전환 시 `TclError: invalid command name` 방지

### 다음에 추가로 진행할 부분 (TODO)
- **KAN-154 PR 생성**: 위 링크에서 base를 `main`(또는 `KAN-150-motherboard-in-settings-parts`)으로 PR 오픈 필요
- **GitHub 협력자/참여자 추가 (Kim-Jiyu, https://github.com/Kim-Jiyu)**: 사용자가 "협력자"라고 했다가 "participant를 의미했다"고 정정함 — 정확히 어떤 의미인지 미확정 상태로 대화 종료됨. 다음 세션에서 아래 중 무엇을 원하는지 먼저 확인할 것:
  1. KAN-154 PR의 reviewer/assignee로 지정 (저장소 접근 권한 필요할 수 있음)
  2. Jira/Linear 등 이슈 트래커에서 해당 티켓의 participant(담당자/관전자)로 등록 — GitHub이 아닌 트래커에서 진행
  3. GitHub 저장소 Settings → Collaborators에 초대 (기존에 안내한 방법, `gh` CLI 미설치라 직접 웹에서 진행 필요)
- 가격 모듈의 `price_candidate_storage.py`(캐시)와 eBay 검색은 여전히 추천 파이프라인에 미연결 (네이버 API만 사용 중)
