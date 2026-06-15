"""
클라이언트 인증: X-API-Key 헤더 검증.
서버를 아무나 쓰지 못하도록 .env의 PROXY_API_KEY와 대조한다.
"""

import os
from fastapi import Header, HTTPException, status


def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """
    요청 헤더의 X-API-Key 값이 서버의 PROXY_API_KEY와 일치하지 않으면 401을 반환한다.
    BuildSense 클라이언트는 모든 요청에 이 헤더를 포함해야 한다.
    """
    expected = os.getenv("PROXY_API_KEY")

    if not expected:
        # 서버에 PROXY_API_KEY가 설정되지 않은 경우 → 운영 실수 방지
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="서버에 PROXY_API_KEY가 설정되지 않았습니다.",
        )

    if x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 API 키입니다.",
        )
