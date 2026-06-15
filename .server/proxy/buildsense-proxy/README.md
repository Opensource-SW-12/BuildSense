# BuildSense Proxy Server

Naver / eBay API 키를 서버에서만 관리하는 가격 조회 프록시입니다.  
클라이언트(BuildSense 앱)는 키 없이 이 서버를 통해 가격을 조회합니다.

---

## 파일 구조

```
buildsense-proxy/
├── main.py                   # FastAPI 앱 진입점
├── requirements.txt
├── .env.example              # 환경변수 템플릿
│
├── routers/
│   ├── auth.py               # X-API-Key 헤더 인증
│   ├── naver.py              # GET /api/naver/search
│   └── ebay.py               # GET /api/ebay/search
│
└── services/
    ├── naver_service.py      # 네이버 쇼핑 API 호출 + 결과 가공
    ├── ebay_service.py       # eBay Browse API 호출 + 결과 가공
    ├── ebay_auth.py          # eBay OAuth 토큰 발급 및 캐싱
    └── exchange_rate.py      # USD→KRW 환율 조회 (1시간 캐싱)
```

---

## 서버 설정 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어 실제 키 값을 입력합니다.

```
NAVER_CLIENT_ID=...
NAVER_CLIENT_SECRET=...
EBAY_CLIENT_ID=...
EBAY_CLIENT_SECRET=...
PROXY_API_KEY=임의의_긴_문자열  # openssl rand -hex 32
```

### 3. 서버 실행

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

개발 중 자동 재시작이 필요하면 `--reload` 옵션을 추가합니다.

---

## API 엔드포인트

모든 요청에 `X-API-Key` 헤더가 필요합니다.

### 네이버 쇼핑 검색

```
GET /api/naver/search?query=RTX+4070+SUPER&display=10
X-API-Key: {PROXY_API_KEY}
```

### eBay 검색

```
GET /api/ebay/search?query=RTX+4070+SUPER&limit=10
X-API-Key: {PROXY_API_KEY}
```

### 서버 상태 확인

```
GET /health
```

### 자동 생성 API 문서

```
http://localhost:8000/docs
```

---

## 클라이언트(BuildSense) 측 변경

`src/pricing/price_fetcher.py`를 `client_price_fetcher.py`의 내용으로 교체합니다.

BuildSense의 `.env`에 아래 두 줄을 추가합니다.

```
PROXY_BASE_URL=http://서버주소:8000
PROXY_API_KEY=서버에_설정한_것과_동일한_키
```

기존에 있던 `NAVER_*`, `EBAY_*` 키는 더 이상 클라이언트에 불필요합니다.

---

## 캐싱 동작

| 항목 | 캐시 방식 | 유효 시간 |
|---|---|---|
| eBay access token | 메모리 (서버 프로세스) | 토큰 만료 5분 전까지 |
| USD→KRW 환율 | 메모리 (서버 프로세스) | 1시간 |
