# BuildSense

> 사용자의 실제 PC 사용 패턴을 분석해 맞춤형 하드웨어 업그레이드를 추천하는 **Windows 데스크탑 애플리케이션**입니다.

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![GUI](https://img.shields.io/badge/GUI-Tkinter-green)
![Server](https://img.shields.io/badge/Server-FastAPI-009688)

---

## 1. 프로젝트 소개

대부분의 PC 견적 추천 서비스는 사용자가 직접 사용 목적, 예산, 원하는 부품을 입력해야 합니다.  
하지만 컴퓨터 부품에 익숙하지 않은 사용자는 CPU, GPU, RAM, 저장장치 중 어떤 부품을 우선적으로 업그레이드해야 하는지 판단하기 어렵습니다.

**BuildSense**는 이러한 문제를 해결하기 위해 사용자의 실제 PC 사용 데이터를 일정 기간 동안 백그라운드에서 수집합니다.  
CPU, RAM, GPU, VRAM, 디스크 사용량과 실행 프로세스 정보를 분석하여 사용자의 사용 패턴을 파악하고, 이를 기반으로 업그레이드가 필요한 부품과 추천 제품을 제시합니다.

즉, BuildSense는 사용자가 직접 모든 조건을 입력하는 방식이 아니라 **실제 사용 데이터 기반으로 맞춤형 하드웨어 업그레이드를 추천하는 시스템**입니다.

---

## 2. 핵심 차별점

| 구분 | 기존 견적 추천 서비스 | BuildSense |
|---|---|---|
| 추천 기준 | 사용자가 입력한 목적과 예산 | 실제 PC 사용 데이터 |
| 사용자 부담 | 사용자가 직접 부품 지식 필요 | 사용 패턴을 자동 분석 |
| 분석 데이터 | 주관적 입력 중심 | CPU/RAM/GPU/프로세스/디스크 로그 기반 |
| 추천 방식 | 일반적인 견적 조합 추천 | 사용자 환경에 맞는 업그레이드 우선순위 제시 |
| 가격 조회 | 고정 데이터 또는 수동 검색 | 네이버 쇼핑/eBay API 기반 실시간 가격 조회 |
| 보안 | API 키 노출 위험 가능 | 프록시 서버를 통해 API 키 보호 |

---

## 3. 주요 기능

| 기능 | 설명 |
|---|---|
| 백그라운드 모니터링 | 60초 간격으로 CPU, RAM, GPU, VRAM 사용률, 실행 중인 상위 프로세스, 디스크 사용량을 기록합니다. |
| 재부팅 후 자동 재개 | Windows 시작 프로그램에 등록되어 모니터링 중 재부팅이 발생해도 분석을 이어서 진행할 수 있습니다. |
| 사용자 유형 자동 분류 | 게임, 개발, 창작, 문서, 브라우저, 메신저 등 프로세스 카테고리와 하드웨어 사용 신호를 기반으로 사용 패턴을 분류합니다. |
| 부품별 업그레이드 점수화 | CPU, GPU, RAM, SSD, HDD, PSU에 대해 사용 패턴 기반 점수와 low/medium/high 등급을 산출합니다. |
| 실제 제품 추천 | PassMark 성능 데이터와 내부 스펙 DB를 활용하여 추천 제품 후보를 선정합니다. |
| 실시간 가격 조회 | 네이버 쇼핑 API와 eBay API를 프록시 서버를 통해 호출하여 추천 제품의 가격 정보를 제공합니다. |
| 보유 부품 지원 | CPU 또는 GPU를 `보유`로 설정하면 해당 부품을 기준으로 호환되는 메인보드와 나머지 구성을 추천합니다. |
| HTML 보고서 생성 | 분석 결과 차트와 추천 결과가 포함된 다크 테마 HTML 보고서를 생성합니다. |

---

## 4. 시스템 동작 흐름

```text
사용자 동의
   ↓
현재 PC 하드웨어 탐지
   ↓
사용자 설정 입력
- 분석 기간
- 사용자 지식 수준
- 부품별 추천 옵션
   ↓
백그라운드 모니터링
- CPU/RAM/GPU/VRAM 사용률
- 실행 프로세스
- 디스크 사용량
   ↓
모니터링 종료 후 추가 정보 입력
- 예산
- RGB 선호 여부
- 색상 선호
   ↓
사용 패턴 분석 및 사용자 유형 분류
   ↓
부품별 업그레이드 필요도 계산
   ↓
추천 제품 후보 선정
   ↓
프록시 서버를 통한 실시간 가격 조회
   ↓
HTML 보고서 생성 및 결과 표시
```

---

## 5. 추천 로직 개요

BuildSense의 추천은 단순히 높은 성능의 부품을 고르는 방식이 아닙니다.  
사용자의 실제 사용 패턴을 분석하여 **어떤 부품이 병목이 되는지**, **어떤 부품을 우선적으로 업그레이드해야 하는지**를 판단합니다.

### 5-1. 사용 데이터 수집

모니터링 단계에서는 다음과 같은 정보를 주기적으로 기록합니다.

- CPU 사용률
- RAM 사용률
- GPU 사용률
- VRAM 사용률
- 디스크 사용량 및 저장장치 상태
- 실행 중인 상위 프로세스
- 프로세스별 사용 빈도와 평균 사용량

수집된 데이터는 `logs/usage.jsonl`에 저장되며, 한 줄이 한 번의 측정 기록을 의미합니다.

### 5-2. 사용자 유형 분류

실행 프로세스는 사전에 정의된 카테고리를 기준으로 분류됩니다.

- 게임
- 개발
- 창작
- 문서 작업
- 브라우저
- 메신저
- 기타 미분류 프로그램

예를 들어 게임 관련 프로세스와 GPU 사용량이 높게 나타나면 게임 사용자 성향이 강하다고 판단할 수 있습니다.  
개발 도구 실행 빈도가 높고 CPU/RAM 사용량이 높다면 개발 작업 중심 사용자로 분류될 수 있습니다.

### 5-3. 부품별 업그레이드 점수화

분석 결과를 바탕으로 각 부품에 대해 업그레이드 필요도를 계산합니다.

| 부품 | 판단 기준 예시 |
|---|---|
| CPU | 평균/최대 CPU 사용률, 고부하 지속 시간, 실행 프로세스 유형 |
| GPU | GPU/VRAM 사용률, 게임·창작 프로그램 사용 여부 |
| RAM | 평균 RAM 점유율, 고점유 상태 지속 여부 |
| SSD/HDD | 저장공간 부족 여부, 디스크 사용 상태 |
| PSU | 추천 부품 조합의 예상 전력 소모량 |

각 부품은 점수에 따라 `low`, `medium`, `high` 등급으로 분류되며, 업그레이드 우선순위 판단에 사용됩니다.

### 5-4. 추천 제품 선정

추천 단계에서는 내부 스펙 DB와 PassMark 성능 데이터를 활용하여 제품 후보를 선정합니다.  
사용자가 CPU 또는 GPU를 이미 보유하고 있다고 설정한 경우, 해당 부품을 기준으로 호환 가능한 메인보드와 나머지 부품 구성을 추천합니다.

게임 사용자로 분류된 경우에는 게임 성능에 유리한 CPU 특성도 추천 과정에 반영하여, 단순 벤치마크 점수만으로 판단하지 않도록 설계했습니다.

---

## 6. 가격 조회 구조

BuildSense는 네이버 쇼핑 API와 eBay API를 활용하여 추천 제품의 가격 정보를 조회합니다.  
다만 API 키가 클라이언트 코드에 직접 포함되면 보안상 위험이 있기 때문에, 가격 조회는 프록시 서버를 통해 처리합니다.

```text
BuildSense 클라이언트
   ↓
가격 조회 요청
   ↓
FastAPI 프록시 서버
   ↓
네이버 쇼핑 API / eBay API
   ↓
가격 후보 정리 및 반환
   ↓
BuildSense 추천 결과에 반영
```

프록시 서버를 사용하면 API 키가 사용자 PC나 GitHub 저장소에 직접 노출되지 않으며, 가격 조회 로직과 API 인증 정보를 서버 측에서 관리할 수 있습니다.

---

## 7. 기술 스택

| 영역 | 기술 |
|---|---|
| 클라이언트 | Python, Tkinter, psutil, matplotlib |
| 가격 조회 서버 | FastAPI, uvicorn |
| 서버 배포 | Render |
| 외부 API | 네이버 쇼핑 검색 API, eBay Browse API |
| 데이터 처리 | JSON, JSONL, CSV |
| 빌드 | PyInstaller |
| 설치 파일 생성 | Inno Setup |
| 테스트 | pytest |
| 협업 | GitHub, Jira |

---

## 8. 설치 및 실행

### 8-1. 저장소 클론

```bash
git clone https://github.com/Opensource-SW-12/BuildSense.git
cd BuildSense
```

### 8-2. 패키지 설치

```bash
pip install -r requirements.txt
```

### 8-3. 개발 모드 실행

```bash
python main.py
```

> BuildSense는 Windows 환경을 기준으로 개발되었습니다.  
> `ctypes.windll`, WMI/PowerShell, `nvidia-smi` 등 Windows 기반 기능을 사용합니다.

---

## 9. 환경 변수 설정

가격 조회 기능은 자체 프록시 서버를 통해 동작합니다.  
프로젝트 루트의 `.env.example` 파일을 복사하여 `.env` 파일을 생성한 뒤 필요한 값을 입력합니다.

```env
PROXY_BASE_URL=http://localhost:8000
PROXY_API_KEY=
```

> 실제 API 키와 토큰은 절대 GitHub에 업로드하지 않습니다.  
> `.env` 파일은 반드시 `.gitignore`에 포함되어야 합니다.

### 프록시 서버 실행

프록시 서버를 직접 실행하려면 `server/` 디렉터리를 사용합니다.

```bash
cd server
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --host 0.0.0.0 --port 8000
```

`server/.env`에는 네이버 쇼핑 API, eBay API, 프록시 API 키 등을 입력합니다.

---

## 10. 빌드 및 배포

Windows용 실행 파일과 설치 파일을 생성할 수 있습니다.

### 10-1. PyInstaller 빌드

```powershell
.\build.ps1
```

### 10-2. Inno Setup 인스톨러 생성

Inno Setup 6 설치 후 아래 명령을 실행합니다.

```powershell
& "ISCC.exe" installer\BuildSense.iss
```

### 빌드 결과물

| 결과물 | 설명 |
|---|---|
| `dist/BuildSense/BuildSense.exe` | 실행 가능한 앱 폴더 |
| `BuildSense-Setup.exe` | Windows 설치 파일 |

---

## 11. 테스트

```bash
pytest
```

BuildSense는 pytest 기반 테스트를 사용하여 주요 분석 로직, 추천 파이프라인, 가격 조회 관련 기능의 동작을 검증합니다.

---

## 12. 프로젝트 구조

```text
BuildSense/
├── main.py                         # 앱 진입점
├── build.ps1                       # PyInstaller 빌드 스크립트
├── BuildSense.spec                 # PyInstaller 빌드 설정
├── installer/
│   └── BuildSense.iss              # Inno Setup 인스톨러 스크립트
├── assets/
│   └── icon.ico                    # 앱 아이콘
├── data/
│   ├── specs/                      # CPU/GPU/RAM/SSD/HDD/PSU/메인보드 정적 스펙 DB
│   ├── process_categories.json     # 프로세스 카테고리 매핑
│   └── process_path_overrides.json # 동일 실행 파일명 재분류 규칙
├── src/
│   ├── app.py                      # 전체 UI 및 화면 전환 로직
│   ├── monitor.py                  # 백그라운드 모니터링 루프
│   ├── hardware.py                 # 하드웨어 탐지
│   ├── gpu.py                      # GPU 정보 수집
│   ├── process_tracker.py          # 실행 프로세스 추적
│   ├── storage.py                  # 파일 입출력
│   ├── config.py                   # 경로 및 설정 상수
│   ├── startup_state.py            # 시작 상태 감지
│   ├── startup_registry.py         # Windows 시작 프로그램 등록
│   ├── analysis/                   # 사용 패턴 분석 및 부품별 점수화
│   ├── recommendation/             # 추천 파이프라인
│   ├── pricing/                    # 프록시 서버 경유 가격 조회 클라이언트
│   └── report/                     # HTML 보고서 생성
├── server/                         # FastAPI 가격 조회 프록시 서버
├── tests/                          # pytest 테스트 코드
├── exports/                        # 스펙 DB CSV 내보내기
└── requirements.txt
```

---

## 13. 주요 데이터 파일

| 파일 | 설명 |
|---|---|
| `data/user_profile.json` | 사용자 동의 여부, 지식 수준, 분석 기간, 부품별 옵션 저장 |
| `data/user_preferences.json` | 예산, RGB/색상 선호, 미분류 프로세스 분류 정보 저장 |
| `logs/usage.jsonl` | 모니터링 스냅샷 저장. 1줄이 1회 측정 데이터를 의미합니다. |
| `reports/report_*.html` | 최종 분석 및 추천 결과 보고서 |

---

## 14. 보안 안내

BuildSense는 외부 API를 활용하지만, API 키가 클라이언트에 직접 노출되지 않도록 프록시 서버 구조를 사용합니다.

다음 파일은 GitHub에 업로드하지 않습니다.

- `.env`
- `server/.env`
- 실제 API 키가 포함된 설정 파일
- 배포용 비밀 키 또는 토큰

공개 저장소에는 `.env.example`처럼 값이 비어 있는 예시 파일만 포함합니다.

---

## 15. 향후 개선 방향

- 추천 알고리즘 고도화
- 다양한 하드웨어 환경 지원 확대
- 미분류 프로세스 자동 분류 정확도 향상
- 가격 데이터 최신성 및 안정성 개선
- UI/UX 개선
- 추천 결과 설명 기능 강화
- 장기 사용 데이터 기반 추천 정확도 개선

---

## 16. 프로젝트 의의

BuildSense는 사용자의 실제 PC 사용 데이터를 기반으로 하드웨어 업그레이드 방향을 제시하는 프로그램입니다.  
단순히 고성능 부품을 추천하는 것이 아니라, 사용자의 작업 환경과 사용 패턴을 분석하여 필요한 부품을 판단한다는 점에서 차별성을 가집니다.

이를 통해 컴퓨터 부품에 익숙하지 않은 사용자도 자신에게 필요한 사양을 쉽게 이해하고, 목적에 맞는 합리적인 PC 업그레이드를 선택할 수 있습니다.
