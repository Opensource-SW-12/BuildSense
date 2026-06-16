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

로딩 화면 스레드 안전성 (KAN-199): 백그라운드 스레드는 `_done[0] = True`와 `_progress[0] = 100`만 갱신하고, 메인 스레드의 `_tick()`이 `_done[0]`을 확인해 `status_lbl.config()` 및 `self.root.after(250, ...)` 호출 — Tk 위젯은 반드시 메인 스레드에서만 조작.

**설정 화면 알약형 토글 (KAN-199):**  
3버튼 토글("추천"/"유지"/"보유")은 `toggle_seg_w=56`, `desc_wraplength=260`; 2버튼 토글은 `toggle_seg_w=64`, `desc_wraplength=340`. 버튼 수에 따라 너비를 달리해 오버플로 방지.

**Monitoring** (`src/monitor.py`):  
Background daemon thread polls every 60 s (`MONITOR_INTERVAL_SECONDS`). Each tick calls `collect_monitoring_snapshot()` — CPU%, RAM%, NVIDIA GPU%/VRAM via `nvidia-smi`, top-15 processes by CPU+RAM, disk partitions, uptime — and appends one JSON line to `logs/usage.jsonl`. Abort is signaled via a sentinel file (`data/buildsense_abort.signal`) so the monitoring process can be stopped from a second-instance window.

**Key data files** (all paths in `src/config.py`):
- `data/user_profile.json` — saved after settings review; contains consent, knowledge level, analysis days, per-part options.
- `data/user_preferences.json` — 추가 입력 다이얼로그에서 저장; 예산·RGB선호(`rgb_preference`)·색상선호(`color_preference`)·미분류 프로세스 포함.
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
| `src/version.py` | `__version__ = "1.0.0"` — 앱 UI 하단 및 HTML 보고서 푸터에 표시 (KAN-196) |
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

**Knowledge levels:** `beginner` / `intermediate` / `advanced` — controls which description text is shown per part.

**Per-part options:** `recommend` / `keep` / `owned` (보유 예정 제품 검색·선택). `owned`는 CPU·GPU에만 적용 (`OWNED_CAPABLE_PARTS`). Validation rule: at least one part must not be `keep`.

**보유(owned) 부품 처리 (KAN-195):**
- 사용자가 "보유" 선택 후 텍스트 입력 → `chipset_tier_mapper.search_passmark_candidates(query, category)` 호출 → PassMark DB에서 토큰 일치율 기반 후보 최대 5개 반환.
- CPU "보유" + 메인보드 "추천": `recommendation_assembler.py`에서 보유 CPU 소켓(`infer_socket_from_cpu_name()`)을 기반으로 메인보드 후보 항목 자동 추가.
- 결과는 `user_profile.json`의 `parts.<PART>.owned_product: {name, score, tier}` 필드에 저장.

## Pricing module (`src/pricing/`)

하드웨어 업그레이드 후보 가격 조회 모듈. `recommendation_assembler.py` → `report_generator.py`를 통해 보고서에 연결 완료 (KAN-140~142).

| File | Role |
|------|------|
| `src/pricing/price_fetcher.py` | 네이버 쇼핑 API / eBay Browse API 검색 및 후보 추출; `_ebay_search_url()`로 Sandbox/Production URL 자동 선택 |
| `src/pricing/ebay_auth.py` | `get_ebay_access_token()` — Client Credentials로 eBay 토큰 자동 발급·캐시·갱신; `_is_sandbox(client_id)`로 환경 자동 감지 |
| `src/pricing/product_matcher.py` | `is_matching_product(title, part)` — 제품명이 부품 스펙과 일치하는지 판별 |
| `src/pricing/price_candidate_storage.py` | 가격 후보 JSON 저장/로드 (`data/prices/`) |
| `src/pricing/exchange_rate.py` | open.er-api.com에서 USD→KRW 환율 조회; `convert_usd_to_krw()` |
| `src/pricing/passmark_tiering.py` | `cpu_passmark_static.json`/`gpu_passmark_static.json`(KAN-166, CPU 294개/GPU 368개) 정적 PassMark DB 로드 + tier 계산(`calculate_cpu_tier`/`calculate_gpu_tier`, 공식 `int((score/max)*29)`, CPU max=80000/GPU max=41588) |

**product_matcher.py 주요 로직 (KAN-94, KAN-102):**
- `_MANUFACTURER_ALIASES` — 제조사 한/영 별칭 매핑 (삼성→삼성전자, lg→엘지 등).
- `_GPU_VARIANT_SUFFIXES = {"super", "ti", "xt", "xtx", "ultra", "gre"}` — GPU 변형 모델 접미사 목록.
- `_chipset_matches()` — chipset 문자열 뒤에 variant 접미사가 오면 다른 모델로 판단해 `False` 반환.

**`.env` API 키 누락 시:** `price_fetcher.search_naver_shopping()`은 `NAVER_CLIENT_ID`/`NAVER_CLIENT_SECRET`이 없으면 `ValueError`를 던지지만, `price_resolver._safe_naver_search()`가 이를 잡아 빈 리스트(`[]`)를 반환해 파이프라인은 중단되지 않음 — 추천 카드(우선순위/목표 사양)는 정상 표시되고 "추천 제품/가격" 부분만 비어 보임.

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
| `src/report/report_data_collector.py` | `collect_report_data(logs, profile)` — 기존 analysis 모듈 전부 호출해 단일 dict 반환 |
| `src/report/chart_builder.py` | matplotlib 차트 함수 12개 → base64 PNG 반환 |
| `src/report/html_builder.py` | `build_html(report_data, charts)` — 인라인 CSS + 섹션 HTML 조립; `_section_user_input()` 포함 |
| `src/report/report_generator.py` | `generate_report()` 진입점 |

**보고서 섹션:** 분석 요약 → 리소스 사용량 → 사용 패턴 → 디스크 현황 → 프로세스 분석 → 업그레이드 필요도 → 사용자 입력 요약

**디자인 테마 (KAN-112):** 다크 테마. 배경 `#0F1117`, 카드 `#161B2E`, 액센트 `#00D4AA`(teal), 경고 `#FF5252`. `chart_builder.py`의 matplotlib 차트도 동일 팔레트.

**데모 스크립트:**
- `demo_report.py` — 더미 로그로 가벼운 HTML 미리보기 생성. `python demo_report.py`로 실행.
- `simulate_user_answers.py` / `.bat` — 더미 로그로 실제 `BuildSenseApp(StartupState.ANALYZE)`를 구동해 전체 UI/보고서 흐름 시연. 실행 전 기존 사용자 데이터를 `.orig`로 백업하고 종료 시 자동 복원. BuildSense 프로젝트 루트에서 `.\simulate_user_answers.bat`으로 실행.

## 추천 시스템 (`src/recommendation/`) — KAN-135~200

사용자 유형·점수 기반 하드웨어 업그레이드 추천. 7단계 파이프라인, `recommendation_assembler.assemble_recommendations()`가 진입점.

| # | 단계 | 모듈 | 키워드 |
|---|------|------|--------|
| 1 | 입력 수집 | `user_input_dialog.py` | 예산·브랜드·RGB·색상, 미분류 프로세스 입력 |
| 2 | 티어 매핑 | `chipset_tier_mapper.py` | PassMark `performance_tier` 조회, X3D 토큰 분리 |
| 3 | 추천 대상 선정 | `upgrade_target_selector.py` | score × weight, grade 필터, 복합 유형 혼합 |
| 4 | 목표 티어 결정 | `target_tier_calculator.py` | grade별 점프 폭(high +2~3, medium +1), 예산 조정 |
| 5 | 후보 필터링 | `spec_candidate_filter.py` | PassMark 후보 최대 5개, 플랫폼 호환성, X3D 게임 부스트 |
| 6 | 가격 조회 | `price_resolver.py` | 네이버 쇼핑 API, product_matcher 검증 |
| 7 | 결과 조립 | `recommendation_assembler.py` | PSU 의존성 검사, 이유 문구 생성, 최종 출력 |

**메인보드 추천 (KAN-144~150):** `data/specs/board_specs.json`(2,152개) 기반. `upgrade_motherboard: bool`에 따라 keep(현재 소켓 제약 필터) / recommend(소켓 무관 CPU + 메인보드 후보) 분기. AM4+Ryzen5000 조합 시 X370/B350/A320 미지원 칩셋 자동 제외.

**X3D CPU 게임 보정 (KAN-200):**
- PassMark는 멀티스레드 범용 연산 기준이라 3D V-Cache의 게임 이점을 반영하지 못함.
- `_X3D_GAME_BOOST = 1.45` — 게임 사용자에게 X3D CPU 실효 점수 45% 상향.
- `_apply_x3d_boost(items, is_game)` — `recommendation_assembler`에서 `primary_user_type == "game"`일 때 활성화.
- X3D 토큰 분리: `normalize_text()`와 `_clean_hw_name()` 모두 `re.sub(r"(\d)(x3d)", r"\1 x3d", ...)` 적용 — "9800X3D"가 단일 토큰으로 묶여 검색 미매칭되던 문제 수정.

**검색 쿼리 생성 (`spec_candidate_filter.py`):**
- `_ram_query(spec, socket, color_pref, rgb_pref)` — `rgb_preference == "yes"`이면 " RGB" 접미사 추가, `color_preference`에 따라 " 블랙"/" 화이트" 추가.
- `_ssd_query(spec, socket)` / `_hdd_query(spec, socket)` — SSD/HDD는 색상 선호 미적용.
- 메인보드 `search_query`: `f"메인보드 {target_socket}{_color_suffix(color_pref)}"` — 색상 선호 적용.

**티어 데이터:** `chipset_tier_mapper.map_hardware_to_tiers()`가 정적 PassMark DB와 토큰 일치율(`_MIN_TOKEN_OVERLAP=0.7`)로 tier를 즉석 계산. 수동 관리 불필요.

## 빌드 및 배포 (PyInstaller + Inno Setup, KAN-173/KAN-191)

- **`src/config.py`**: `BASE_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent` — frozen 빌드에서 모든 경로가 EXE 옆을 가리킴 (KAN-107 패턴 동일).
- **배포 형태**: `--onedir` (매번 재압축 해제 지연을 피하기 위함). `BuildSense.spec`으로 빌드 → `dist/BuildSense/BuildSense.exe` + `_internal/`.
- **`build.ps1`**: 빌드 후 `data/specs/`, `data/process_categories.json`, `data/process_path_overrides.json`, `.env.example`을 `dist/BuildSense/`로 복사. `.env`(API 키)는 복사하지 않음.
- **`main.py --unregister-startup`**: 제거 시 레지스트리 정리용 CLI 플래그.
- **`installer/BuildSense.iss`** (Inno Setup): `PrivilegesRequired=lowest` — 관리자 권한 없이 사용자별 설치. 제거 시 `BuildSense.exe --unregister-startup` 실행.

**다른 컴퓨터에 배포 시 주의점:**
- `.env` 미동봉 — 새 컴퓨터마다 `.env.example`을 복사해 NAVER/eBay 키를 직접 채워야 가격 조회 동작 (안 채워도 크래시 없음).
- 코드 미서명 — Windows SmartScreen 경고 발생 가능.
- `demo_report.py`/`simulate_user_answers.py`는 개발용이며 인스톨러에 미포함.

## FastAPI 프록시 서버 (`.server/`, KAN-163)

클라이언트(BuildSense 앱)가 직접 Naver/eBay API 키를 가질 필요 없도록 가격 조회를 중계하는 프록시 서버. `.server/` 디렉터리에 위치하며 앱 본체와 독립적으로 배포·운영된다.

### 실행

```bash
cd .server
pip install -r requirements.txt      # fastapi, uvicorn, python-dotenv
cp .env.example .env                 # 환경변수 설정
uvicorn main:app --host 0.0.0.0 --port 8000
```

개발 중 API 문서: `http://localhost:8000/docs`

### 서버 구조

```
.server/
├── main.py                  # FastAPI 앱 진입점, 라우터 등록
├── .env.example             # 환경변수 템플릿
├── requirements.txt
├── client_price_fetcher.py  # 클라이언트 측 호출 래퍼 (앱에서 import)
├── routers/
│   ├── auth.py              # X-API-Key 헤더 검증 의존성
│   ├── naver.py             # GET /api/naver/search
│   └── ebay.py              # GET /api/ebay/search
└── services/
    ├── naver_service.py     # 네이버 쇼핑 API 호출 및 결과 정규화
    ├── ebay_service.py      # eBay Browse API 호출 + KRW 환산
    ├── ebay_auth.py         # eBay OAuth Client Credentials 토큰 캐싱
    └── exchange_rate.py     # USD→KRW 환율 조회 (1시간 TTL 캐싱)
```

### 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| `GET` | `/health` | 서버 상태 확인 |
| `GET` | `/api/naver/search?query=RTX+4070&display=10` | 네이버 쇼핑 검색 |
| `GET` | `/api/ebay/search?query=RTX+4070&limit=10` | eBay 검색 (KRW 환산 포함) |

모든 `/api/*` 요청에 `X-API-Key: <PROXY_API_KEY>` 헤더 필수.

### 서버 환경변수 (`.server/.env`)

```
NAVER_CLIENT_ID=...
NAVER_CLIENT_SECRET=...
EBAY_CLIENT_ID=...
EBAY_CLIENT_SECRET=...
PROXY_API_KEY=...        # 클라이언트 인증용 임의 비밀키 (예: openssl rand -hex 32)
```

### 클라이언트 측 프로그래밍 전략

BuildSense 앱에서 프록시 서버를 호출하는 쪽은 `.server/client_price_fetcher.py`가 담당한다. 핵심 설계 결정들:

**1. 표준 라이브러리만 사용 (`urllib`)**  
`requests` 같은 서드파티 라이브러리를 피하고 `urllib.request`만 사용 — PyInstaller 빌드 크기 절감, 추가 의존성 없음.

```python
_PROXY_BASE = os.getenv("PROXY_BASE_URL", "http://localhost:8000")
_PROXY_API_KEY = os.getenv("PROXY_API_KEY", "")
```

클라이언트 `.env`에 `PROXY_BASE_URL`과 `PROXY_API_KEY`를 설정해야 함. 기본값은 로컬 테스트용(`localhost:8000`).

**2. 공통 요청 함수 `_proxy_get(path)`**  
URL 조합 → `X-API-Key` 헤더 주입 → `urlopen` → JSON 디코딩을 한 곳에서 처리. 오류를 세 종류로 구분해 `RuntimeError`로 래핑:
- `HTTPError` → HTTP 상태 코드 + 응답 본문 포함
- `URLError` → 연결 실패 (서버 미기동, 네트워크 오류)
- `JSONDecodeError` → 응답 파싱 실패

**3. 반환 형식 통일**  
서버가 이미 정규화된 `list[dict]`를 반환하므로 클라이언트는 추가 파싱 없이 바로 사용. 각 항목 형식:

```python
# 네이버
{"source": "naver", "title": str, "link": str, "price_krw": int|None,
 "price_usd": None, "currency": "KRW", "mall_name": str|None, "brand": str|None, "maker": str|None}

# eBay
{"source": "ebay", "title": str, "link": str, "price_usd": float|None,
 "price_krw": int|None, "currency": str|None, "seller": str|None}
```

**4. 하위 호환 래퍼 (`extract_naver_candidates`, `extract_ebay_candidates`)**  
기존 코드가 `extract_*_candidates(api_result)` 패턴으로 호출하는 경우를 대비해 유지. 서버 응답이 이미 리스트이므로 통과(`return api_result`).

**5. 서버 미연결 시 동작**  
`_proxy_get()`이 `RuntimeError`를 던지면 `price_resolver.py`의 `_safe_naver_search()`가 이를 잡아 빈 `[]` 반환 → 추천 카드는 표시되고 가격 정보만 비어 보임. 크래시 없음.

**6. 현재 통합 상태 (진행 중)**  
`client_price_fetcher.py`는 서버 디렉터리(`.server/`)에 위치하며, 아직 앱 본체(`src/pricing/price_fetcher.py`)를 대체하지 않은 상태. 프록시 서버 전환이 완료되면:
- `src/pricing/price_fetcher.py` 내 네이버/eBay 직접 호출 로직을 `client_price_fetcher.py`로 교체
- 앱 `.env`에서 `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`, `EBAY_CLIENT_ID`, `EBAY_CLIENT_SECRET` 제거
- `PROXY_BASE_URL`, `PROXY_API_KEY` 추가

### 서버 측 설계 패턴 (FastAPI)

**인증: `Depends(verify_api_key)`**  
FastAPI 의존성 주입으로 모든 라우터에 인증을 일관되게 적용. `auth.py`의 `verify_api_key`가 `X-API-Key` 헤더를 환경변수 `PROXY_API_KEY`와 비교; 불일치 시 HTTP 401 반환.

```python
@router.get("/naver/search")
def naver_search(query: str = Query(...), _: None = Depends(verify_api_key)):
    ...
```

**예외 처리 계층**  
- `services/*.py`: `ValueError` (환경변수 누락 등 설정 문제) / `RuntimeError` (외부 API 호출 실패) 발생
- `routers/*.py`: `ValueError` → HTTP 500, `RuntimeError` → HTTP 502로 변환해 FastAPI `HTTPException` 발생

**환율 캐싱 (`exchange_rate.py`)**  
프로세스 레벨 글로벌 변수 `_cached_rate`, `_rate_expires_at`으로 1시간 TTL 캐싱. 매 요청마다 외부 API를 호출하지 않음. FastAPI는 기본적으로 싱글 프로세스이므로 별도 공유 메모리 없이 동작.

**eBay 토큰 캐싱 (`ebay_auth.py`)**  
동일 패턴 — 만료 5분 전부터 자동 재발급. Sandbox/Production 자동 감지(`"SBX" in client_id.upper()`).

## 브랜치 현황 (2026-06-16 기준)

### main에 머지 완료 (최신순)

- `fix/rgb-ram-preference` (PR #121): `rgb_preference` 값이 RAM 검색 쿼리에 반영되지 않던 버그 수정
- `KAN-200-feature-add-game-user-x3d-cpu-weight` (PR #119): X3D CPU 게임 성능 보정 + X3D 토큰 분리 + UI/검색 버그 수정
- `KAN-199-fix-loading-screen-and-settings-bugs` (PR #118): 로딩 화면 스레드 안전성, 토글 오버플로, 입문자 제한 수정
- `KAN-196-feature-program-version-mark` (PR #117): `src/version.py` 추가, 앱 UI·보고서 푸터 버전 표시
- `KAN-163-proxy-server` (PR #120): FastAPI 프록시 서버 (`.server/`) 추가
- `KAN-191-feature-inno-setup-configuration` (PR #116): Inno Setup 인스톨러 설정 + PyInstaller spec
- `KAN-195-feature-user-selected-part-compatibility` (PR #115): 보유(owned) 부품 선택 + 메인보드 호환성 체크
- KAN-84~87: 하드웨어 탐지 최적화
- KAN-93~100: HTML 보고서 생성기
- KAN-102 (PR #75): product_matcher GPU variant·제조사 별칭 수정
- KAN-107 (PR #79): main.py EXE 경로 기반 .env 로드
- KAN-109 (PR #81): passmark_tiering.py — PassMark 정적 DB tier 산출
- KAN-110 (PR #83): ebay_auth.py — eBay 토큰 자동 발급·갱신
- KAN-112 (PR #84): 보고서 다크 테마 + demo_report.py
- KAN-122: passmark_tiering 버그 수정 + eBay Sandbox/Production URL 자동 감지
- KAN-135~141: 추천 파이프라인 (사용자 입력 → tier 매핑 → 대상 선정 → tier 계산 → 후보 필터링 → 가격 조회 → 최종 조립)
- KAN-142 (PR #94/#95): HTML 보고서 추천 섹션
- KAN-144: board_specs.json (메인보드 2,152개) 정규화
- KAN-145~150: 메인보드 추천 시스템 + 플랫폼 호환성 쿼리 + 칩셋 rank 수정
- KAN-154-ui-sync-custom-tkinter: UI 다크 테마 동기화, 보고서 사용자 입력 섹션, 예산 가이드
- KAN-164~172: 가격 정제, 예산 시스템, PassMark 정적 DB, 테스트 스위트, 추천 품질 개선, 중복 제품 필터링, 메인보드-CPU 호환성, 프로세스 카테고리 업그레이드
- KAN-166: PassMark 정적 DB(`cpu_passmark_static.json`/`gpu_passmark_static.json`) 구축

### 향후 과제 (TODO)

- **프록시 서버 전환 완료**: `src/pricing/price_fetcher.py`를 `client_price_fetcher.py` 기반으로 교체하고 앱 `.env`에서 직접 API 키 제거. 프록시 서버가 운영 중이어야 앱이 가격 조회 가능.
- **앱 아이콘(.ico)**: BuildSense.spec에 `icon=` 미설정 상태. 아이콘 파일 확보 후 spec 및 BuildSense.iss 모두 수정 필요.
- **코드 서명**: Windows SmartScreen 경고 우회를 위한 코드 서명 인증서 구매·적용.
- **price_candidate_storage.py + eBay 검색**: 가격 캐시 및 eBay 검색이 추천 파이프라인에 아직 미연결 (네이버 API만 사용 중).
