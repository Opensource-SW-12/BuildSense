# BuildSense

사용자의 실제 PC 사용 패턴을 분석해 맞춤형 하드웨어 업그레이드를 추천하는 Windows 데스크탑 애플리케이션입니다.

## 프로젝트 소개

대부분의 견적 추천 서비스는 사용자가 직접 본인의 사용 목적과 예산을 입력해야 합니다. BuildSense는 그 대신 일정 기간 동안 백그라운드에서 PC를 모니터링하여 **실제 사용 데이터**(CPU/RAM/GPU 사용률, 실행 프로세스, 디스크 상태)를 직접 수집하고, 이를 기반으로 사용자 유형(게임/개발/창작 등)을 자동으로 분류해 업그레이드가 필요한 부품과 구체적인 제품을 추천합니다.

## 주요 기능

- **백그라운드 모니터링**: 60초 간격으로 CPU/RAM/GPU/VRAM 사용률, 실행 중인 상위 프로세스, 디스크 사용량을 기록 (`logs/usage.jsonl`)
- **재부팅 후 자동 재개**: Windows 시작 프로그램에 등록되어, 모니터링 중 재부팅해도 이어서 분석 가능
- **사용자 유형 자동 분류**: 프로세스 카테고리(게임/개발/창작/문서/브라우저/메신저)와 하드웨어 신호를 기반으로 사용 패턴 분류
- **부품별 업그레이드 점수화**: CPU/GPU/RAM/SSD/HDD/파워(PSU)에 대해 사용 패턴 기반 점수·등급(low/medium/high) 산출
- **실제 제품 추천 + 실시간 가격 조회**: PassMark 성능 데이터 기반으로 추천 제품 후보를 선정하고, 네이버 쇼핑/eBay API로 실시간 가격을 조회해 제시
- **보유 부품 지원**: CPU/GPU를 "보유"로 설정하면 해당 부품을 기준으로 호환되는 메인보드 등 나머지 구성을 추천
- **다크 테마 HTML 보고서**: 분석 결과를 차트 12종 + 추천 결과가 포함된 단독 HTML 파일로 생성 (외부 의존 없이 브라우저에서 바로 열람 가능)

## 동작 흐름

```
동의 화면 → 하드웨어 탐지 → 사용자 설정(분석 기간/지식 수준/부품별 옵션)
   → 백그라운드 모니터링 (재부팅 시에도 자동 재개)
   → 모니터링 종료 → 추가 정보 입력(예산/RGB/색상 선호)
   → 사용 패턴 분석 → 업그레이드 추천 → 실시간 가격 조회
   → HTML 보고서 생성 및 표시
```

## 기술 스택

| 영역 | 기술 |
|---|---|
| 클라이언트 | Python, Tkinter, psutil, matplotlib, PyInstaller |
| 가격 조회 서버 | FastAPI, uvicorn (Render 배포) |
| 외부 API | 네이버 쇼핑 검색 API, eBay Browse API |
| 배포 | PyInstaller(onedir) + Inno Setup 인스톨러 |
| 테스트 | pytest |

## 설치 및 실행 (개발 모드)

```bash
pip install -r requirements.txt
python main.py
```

Windows 전용입니다 (`ctypes.windll`, WMI/PowerShell, `nvidia-smi` 사용).

### 환경변수 (`.env`)

가격 조회는 자체 프록시 서버를 거칩니다. 프로젝트 루트에 `.env.example`을 복사해 `.env`로 만들고 값을 채워주세요.

```
PROXY_BASE_URL=http://localhost:8000   # 로컬 프록시 서버 사용 시
PROXY_API_KEY=
```

프록시 서버를 직접 띄우려면 [`.server/`](.server/) 디렉터리를 참고하세요.

```bash
cd .server
pip install -r requirements.txt
cp .env.example .env   # NAVER/eBay API 키, PROXY_API_KEY 입력
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 빌드 및 배포

Windows용 단일 설치 파일(EXE)로 빌드할 수 있습니다.

```powershell
# 1. PyInstaller 빌드 (dist.env가 있으면 프록시 서버 키를 빌드에 내장)
.\build.ps1

# 2. Inno Setup으로 인스톨러 생성 (Inno Setup 6 설치 필요)
& "ISCC.exe" installer\BuildSense.iss
```

결과물: `dist/BuildSense/BuildSense.exe` (실행 폴더), `BuildSense-Setup.exe` (설치 파일, 프로젝트 루트에 생성).

## 테스트

```bash
pytest
```

## 프로젝트 구조

```
BuildSense/
├── main.py                      # 앱 진입점
├── build.ps1                    # PyInstaller 빌드 스크립트
├── BuildSense.spec              # PyInstaller 빌드 설정
├── installer/
│   └── BuildSense.iss           # Inno Setup 인스톨러 스크립트
├── assets/
│   └── icon.ico                 # 앱 아이콘
├── data/
│   ├── specs/                   # CPU/GPU/RAM/SSD/HDD/PSU/메인보드 정적 스펙 DB
│   ├── process_categories.json  # 프로세스 → 사용자 유형 카테고리 매핑
│   └── process_path_overrides.json  # 동일 실행 파일명 재분류 규칙 (경로 키워드 기반)
├── src/
│   ├── app.py                   # 전체 UI/화면 전환 로직
│   ├── monitor.py               # 백그라운드 모니터링 루프
│   ├── hardware.py / gpu.py / process_tracker.py   # 하드웨어/프로세스 탐지
│   ├── storage.py / config.py   # 파일 I/O, 경로 상수
│   ├── startup_state.py / startup_registry.py       # 재부팅 자동 재개
│   ├── analysis/                # 사용 패턴·디스크·프로세스 분석, 부품별 점수화
│   ├── recommendation/          # 7단계 추천 파이프라인 (사용자 입력 → 가격 조회 → 결과 조립)
│   ├── pricing/                 # 프록시 서버 경유 가격 조회 클라이언트
│   └── report/                  # 분석 결과 → 다크 테마 HTML 보고서
├── .server/                     # FastAPI 가격 조회 프록시 서버 (독립 배포)
├── tests/                       # pytest 테스트 (177개)
├── exports/                     # 스펙 DB CSV 내보내기
└── requirements.txt
```

## 주요 데이터 파일

- `data/user_profile.json` — 동의·지식 수준·분석 기간·부품별 옵션
- `data/user_preferences.json` — 예산·RGB/색상 선호·미분류 프로세스 분류
- `logs/usage.jsonl` — 모니터링 스냅샷 (1줄 = 1회 측정)
- `reports/report_*.html` — 최종 분석/추천 보고서
