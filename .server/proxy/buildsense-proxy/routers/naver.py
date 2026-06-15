"""
GET /api/naver/search?query=... 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from routers.auth import verify_api_key
from services import naver_service


router = APIRouter()


@router.get(
    "/naver/search",
    summary="네이버 쇼핑 검색",
    description="query 파라미터로 부품명을 전달하면 네이버 쇼핑 검색 결과를 반환합니다.",
)
def naver_search(
    query: str = Query(..., description="검색할 부품명 (예: RTX 4070 SUPER)"),
    display: int = Query(10, ge=1, le=100, description="검색 결과 개수"),
    _: None = Depends(verify_api_key),
):
    try:
        return naver_service.search(query, display)
    except ValueError as e:
        # 환경변수 누락 등 서버 설정 문제
        raise HTTPException(status_code=500, detail=str(e))
    except RuntimeError as e:
        # 네이버 API 호출 실패
        raise HTTPException(status_code=502, detail=str(e))
