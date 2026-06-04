import base64
import json
import os
import time
import urllib.parse
import urllib.request


EBAY_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
EBAY_SCOPE = "https://api.ebay.com/oauth/api_scope"

_cached_access_token = None
_token_expires_at = 0


def get_ebay_access_token():
    global _cached_access_token, _token_expires_at

    now = time.time()

    if _cached_access_token and now < _token_expires_at:
        return _cached_access_token

    client_id = os.getenv("EBAY_CLIENT_ID")
    client_secret = os.getenv("EBAY_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError(
            "EBAY_CLIENT_ID 또는 EBAY_CLIENT_SECRET 환경변수가 없습니다."
        )

    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(
        credentials.encode("utf-8")
    ).decode("utf-8")

    data = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "scope": EBAY_SCOPE
    }).encode("utf-8")

    request = urllib.request.Request(
        EBAY_TOKEN_URL,
        data=data,
        method="POST"
    )
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    request.add_header("Authorization", f"Basic {encoded_credentials}")

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            response_body = response.read().decode("utf-8")

        token_data = json.loads(response_body)

        _cached_access_token = token_data["access_token"]
        expires_in = int(token_data.get("expires_in", 7200))

        _token_expires_at = now + expires_in - 300

        return _cached_access_token

    except urllib.error.HTTPError as error:
        raise RuntimeError(
            f"eBay 토큰 발급 요청 실패: HTTP 상태 코드 {error.code}"
        ) from error

    except urllib.error.URLError as error:
        raise RuntimeError(
            f"eBay 토큰 발급 연결 실패: 네트워크 또는 주소 문제 - {error}"
        ) from error

    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"eBay 토큰 응답 JSON 해석 실패: {error}"
        ) from error

    except KeyError as error:
        raise RuntimeError(
            f"eBay 토큰 응답에서 access_token 값을 찾을 수 없습니다: {error}"
        ) from error