# BuildSense

> 사용자의 실제 PC 사용 패턴을 분석하여  
> 가장 적합한 조립 PC 사양을 추천하는 AI 기반 PC 추천 시스템

# 1. 프로젝트 소개

BuildSense는 사용자의 실제 컴퓨터 사용 데이터를 기반으로  
개인에게 적합한 조립 PC 사양을 추천해주는 프로그램입니다.

기존의 조립 PC 추천 방식은 사용자가 직접 부품을 검색하고 비교해야 하므로  
컴퓨터에 익숙하지 않은 사용자에게는 진입 장벽이 높습니다.  
BuildSense는 이러한 불편함을 줄이고, 사용자의 실제 사용 환경과 목적에 맞는  
보다 합리적인 PC 구성을 추천하는 것을 목표로 합니다.

# 2. 프로젝트 목표

- 사용자의 실제 PC 사용 패턴 수집 및 분석
- 하드웨어 정보와 프로세스 사용 이력을 기반으로 사용자 환경 파악
- CPU, GPU, RAM, 저장장치, 파워 등 주요 부품 추천
- 초보 사용자도 쉽게 이해할 수 있는 추천 결과 제공
- 불필요한 과소비를 줄이고 목적에 맞는 조립 PC 선택 지원

# 3. 주요 기능

# 3-1. 사용자 PC 정보 수집
- 현재 사용 중인 PC의 하드웨어 정보 확인
- CPU / GPU / RAM / 저장장치 사용량 모니터링
- 실행 중인 프로세스 및 사용 패턴 기록

# 3-2. 사용 패턴 분석
- 일정 기간 동안 사용자 PC 사용 데이터 수집
- 사용 시간대, 자원 점유율, 실행 프로그램 빈도 분석
- 수집된 데이터를 정규화하여 추천 로직에 활용

# 3-3. 부품 추천
- 사용 목적과 실제 사용량을 반영한 부품 추천
- CPU / GPU / RAM / SSD / HDD / PSU 등 추천 방향 제시
- 사용자 지식 수준 및 선택 옵션 반영 가능

# 3-4. 결과 제공
- 분석 결과 및 추천 사양 시각화
- 결과 리포트 및 추천 화면 제공
- 사용자가 이해하기 쉬운 형태로 결과 출력

# 4. 기대 효과

- 조립 PC에 익숙하지 않은 사용자도 쉽게 사양 선택 가능
- 실제 사용 패턴 기반 추천으로 불필요한 고사양 구매 방지
- 사용자 맞춤형 추천으로 만족도 향상
- 하드웨어 선택 과정을 보다 직관적으로 지원

# 5. 기술 스택

### Language
- Python

# Libraries / Tools
- psutil
- Pillow
- matplotlib
- python-dotenv

# UI / App
- Tkinter 기반 데스크톱 애플리케이션

# Collaboration
- GitHub
- Jira

# Packaging / Build
- PyInstaller
- Inno Setup

# 6. 프로젝트 구조

```bash
BuildSense/
├── data/                # 원본/가공 데이터 저장
├── exports/             # 내보낸 결과 파일
├── installer/           # 설치 파일 관련 리소스
├── logs/                # 모니터링 로그
├── reports/             # 분석/추천 리포트
├── results/             # 결과 산출물
├── src/
│   ├── analysis/        # 사용 패턴 분석 로직
│   ├── normalization/   # 데이터 정규화
│   ├── pricing/         # 가격 관련 처리
│   ├── recommendation/  # 부품 추천 로직
│   ├── report/          # 리포트 생성
│   ├── app.py
│   ├── background.py
│   ├── config.py
│   ├── consent.py
│   ├── gpu.py
│   ├── hardware.py
│   ├── instance_status.py
│   ├── monitor.py
│   ├── platform_mapper.py
│   ├── process_tracker.py
│   ├── settings.py
│   ├── startup_registry.py
│   ├── startup_state.py
│   ├── storage.py
│   └── validators.py
├── tests/               # 테스트 코드
├── tools/               # 보조 스크립트 / 유틸
├── .env.example         # 환경 변수 예시
├── BuildSense.spec      # PyInstaller 설정
├── build.ps1            # 빌드 스크립트
├── demo_report.py
├── main.py              # 프로그램 실행 진입점
├── requirements.txt
└── README.md
