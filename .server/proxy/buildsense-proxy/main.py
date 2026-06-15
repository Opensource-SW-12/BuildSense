"""
BuildSense 프록시 서버 진입점.

실행:
    uvicorn main:app --host 0.0.0.0 --port 8000

API 문서 (개발 중에만 사용):
    http://localhost:8000/docs
"""

from dotenv import load_dotenv
load_dotenv()  # .env 파일을 가장 먼저 로드

from fastapi import FastAPI
from routers import naver, ebay


app = FastAPI(
    title="BuildSense Proxy",
    description="Naver / eBay API 키를 서버에서만 관리하는 가격 조회 프록시",
    version="1.0.0",
)

# /api/naver/search, /api/ebay/search
app.include_router(naver.router, prefix="/api")
app.include_router(ebay.router, prefix="/api")


@app.get("/health", tags=["운영"])
def health_check():
    """서버가 정상적으로 동작 중인지 확인한다."""
    return {"status": "ok"}
