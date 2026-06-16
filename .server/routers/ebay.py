"""
GET /api/ebay/search?query=... 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from routers.auth import verify_api_key
from services import ebay_service


router = APIRouter()


@router.get(
    "/ebay/search",
    summary="eBay 검색",
    description="query 파라미터로 부품명을 전달하면 eBay 검색 결과를 KRW 환산 가격과 함께 반환",
)
def ebay_search(
    query: str = Query(..., description="검색할 부품명"),
    limit: int = Query(10, ge=1, le=50, description="검색 결과 개수"),
    _: None = Depends(verify_api_key),
):
    try:
        return ebay_service.search(query, limit)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
