"""
eBay OAuth 2.0 Client Credentials 토큰 발급 및 캐싱.
기존 BuildSense의 ebay_auth.py를 서버용으로 그대로 이식.
"""

import base64
import json
import os
import time
import urllib.parse
import urllib.request


EBAY_SCOPE = "https://api.ebay.com/oauth/api_scope"

_PROD_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
_SBX_TOKEN_URL  = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"

# 서버 프로세스가 살아있는 동안 토큰을 재사용 (매 요청마다 발급 방지)
_cached_access_token: str | None = None
_token_expires_at: float = 0


def is_sandbox(client_id: str) -> bool:
    """클라이언트 ID에 'SBX'가 포함되면 샌드박스 환경으로 판단."""
    return "SBX" in client_id.upper()


def get_ebay_access_token() -> str:
    """
    유효한 eBay access token을 반환한다.
    만료 5분 전부터 자동으로 재발급한다.
    """
    global _cached_access_token, _token_expires_at

    now = time.time()

    # 캐시된 토큰이 아직 유효하면 그대로 반환
    if _cached_access_token and now < _token_expires_at:
        return _cached_access_token

    client_id = os.getenv("EBAY_CLIENT_ID")
    client_secret = os.getenv("EBAY_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError("EBAY_CLIENT_ID 또는 EBAY_CLIENT_SECRET 환경변수가 없습니다.")

    token_url = _SBX_TOKEN_URL if is_sandbox(client_id) else _PROD_TOKEN_URL

    # Basic 인증: base64(client_id:client_secret)
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    data = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "scope": EBAY_SCOPE,
    }).encode()

    request = urllib.request.Request(token_url, data=data, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    request.add_header("Authorization", f"Basic {encoded_credentials}")

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            token_data = json.loads(response.read().decode())

        _cached_access_token = token_data["access_token"]
        expires_in = int(token_data.get("expires_in", 7200))

        # 만료 5분 전을 기준으로 캐시 유효 기간 설정
        _token_expires_at = now + expires_in - 300

        return _cached_access_token

    except urllib.error.HTTPError as e:
        raise RuntimeError(f"eBay 토큰 발급 실패: HTTP {e.code}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"eBay 토큰 발급 연결 실패: {e}") from e
    except KeyError as e:
        raise RuntimeError(f"eBay 토큰 응답에서 access_token을 찾을 수 없습니다: {e}") from e
