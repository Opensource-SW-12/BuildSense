"""
가격 조회 클라이언트.
기존: 클라이언트가 직접 Naver/eBay API 호출 (키 필요)
변경: BuildSense 프록시 서버를 통해 가격 조회 (키 불필요)

서버 주소는 .env의 PROXY_BASE_URL로 설정한다.
"""

import json
import os
import urllib.parse
import urllib.request


# .env 또는 환경변수로 서버 주소를 지정 (기본값: 로컬 테스트용)
_PROXY_BASE = os.getenv("PROXY_BASE_URL", "http://localhost:8000")
_PROXY_API_KEY = os.getenv("PROXY_API_KEY", "")


def _proxy_get(path: str) -> list[dict]:
    """프록시 서버에 GET 요청을 보내고 JSON 응답을 반환하는 공통 함수."""
    url = f"{_PROXY_BASE}{path}"
    request = urllib.request.Request(url)
    request.add_header("X-API-Key", _PROXY_API_KEY)

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"프록시 서버 요청 실패: HTTP {e.code} - {body}") from e

    except urllib.error.URLError as e:
        raise RuntimeError(f"프록시 서버 연결 실패: {e}") from e

    except json.JSONDecodeError as e:
        raise RuntimeError(f"프록시 서버 응답 JSON 해석 실패: {e}") from e


def build_search_query(part: dict) -> str:
    """부품 dict에서 검색어를 생성한다."""
    manufacturer = part.get("manufacturer", "")
    name = part.get("name", "")
    return f"{manufacturer} {name}".strip()


# ── 네이버 ────────────────────────────────────────────────────────────────────

def search_naver_shopping(query: str, display: int = 10) -> list[dict]:
    """
    프록시 서버를 통해 네이버 쇼핑 검색 결과를 가져옴
    반환값은 기존 extract_naver_candidates()의 출력과 동일한 형식
    """
    path = f"/api/naver/search?query={urllib.parse.quote(query)}&display={display}"
    return _proxy_get(path)


# ── eBay ─────────────────────────────────────────────────────────────────────

def search_ebay(query: str, limit: int = 10) -> list[dict]:
    """
    프록시 서버를 통해 eBay 검색 결과를 가져옴
    반환값은 기존 extract_ebay_candidates()의 출력과 동일한 형식
    (KRW 환산도 서버에서 처리되어 포함된 채로 반환됨)
    """
    path = f"/api/ebay/search?query={urllib.parse.quote(query)}&limit={limit}"
    return _proxy_get(path)


# ── 하위 호환: 기존 코드가 extract_*_candidates()를 호출하는 경우를 위해 유지 ──

def extract_naver_candidates(api_result) -> list[dict]:
    """
    [하위 호환용] 서버가 이미 가공된 리스트를 반환하므로,
    search_naver_shopping()을 직접 써도 되지만 기존 호출부가 이 함수를 쓴다면
    그냥 통과시킨다.
    """
    if isinstance(api_result, list):
        return api_result
    # 혹시 raw dict가 넘어온 경우 (이전 코드와의 호환)
    return api_result


def extract_ebay_candidates(api_result) -> list[dict]:
    """[하위 호환용] extract_naver_candidates와 동일한 이유로 유지."""
    if isinstance(api_result, list):
        return api_result
    return api_result
