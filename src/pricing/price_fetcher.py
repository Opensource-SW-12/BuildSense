"""
가격 조회 클라이언트.
직접 Naver/eBay API를 호출하지 않고 BuildSense 프록시 서버를 통해 검색한다.
API 키는 서버에서만 관리되므로 클라이언트(앱/EXE)에 키가 없어도 동작한다.

필요 환경변수 (.env):
    PROXY_BASE_URL  : 프록시 서버 주소 (기본값: http://localhost:8000)
    PROXY_API_KEY   : 프록시 서버 인증 키
"""
import json
import os
import urllib.parse
import urllib.request

_PROXY_BASE    = os.getenv("PROXY_BASE_URL", "http://localhost:8000")
_PROXY_API_KEY = os.getenv("PROXY_API_KEY", "")


# ── 공통 요청 헬퍼 ────────────────────────────────────────────────────

def _proxy_get(path: str) -> list[dict]:
    """프록시 서버에 GET 요청을 보내고 JSON 응답(list[dict])을 반환한다."""
    url = f"{_PROXY_BASE}{path}"
    req = urllib.request.Request(url)
    req.add_header("X-API-Key", _PROXY_API_KEY)

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"프록시 서버 요청 실패: HTTP {e.code} - {body}") from e

    except urllib.error.URLError as e:
        raise RuntimeError(f"프록시 서버 연결 실패: {e}") from e

    except json.JSONDecodeError as e:
        raise RuntimeError(f"프록시 서버 응답 JSON 해석 실패: {e}") from e


# ── 유틸 ─────────────────────────────────────────────────────────────

def build_search_query(part: dict) -> str:
    manufacturer = part.get("manufacturer", "")
    name = part.get("name", "")
    return f"{manufacturer} {name}".strip()


def safe_int(value):
    try:
        return int(value) if value is not None else None
    except (ValueError, TypeError):
        return None


def safe_float(value):
    try:
        return float(value) if value is not None else None
    except (ValueError, TypeError):
        return None


# ── 네이버 ───────────────────────────────────────────────────────────

def search_naver_shopping(query: str, display: int = 10) -> list[dict]:
    """
    프록시 서버를 통해 네이버 쇼핑을 검색한다.
    반환값은 이미 정규화된 list[dict] (기존 extract_naver_candidates 결과와 동일한 형식).
    """
    path = f"/api/naver/search?query={urllib.parse.quote(query)}&display={display}"
    return _proxy_get(path)


def extract_naver_candidates(api_result) -> list[dict]:
    """
    하위 호환용. 프록시 전환 후 search_naver_shopping()이 이미 list[dict]를 반환하므로
    price_resolver.py의 기존 호출 패턴(extract_naver_candidates(search_naver_shopping(...)))이
    그대로 동작하도록 pass-through 처리한다.
    """
    if isinstance(api_result, list):
        return api_result
    return []


# ── eBay ─────────────────────────────────────────────────────────────

def search_ebay(query: str, limit: int = 10) -> list[dict]:
    """
    프록시 서버를 통해 eBay를 검색한다.
    KRW 환산은 서버에서 처리되어 포함된 채로 반환된다.
    """
    path = f"/api/ebay/search?query={urllib.parse.quote(query)}&limit={limit}"
    return _proxy_get(path)


def extract_ebay_candidates(api_result) -> list[dict]:
    """하위 호환용. extract_naver_candidates와 동일한 이유로 pass-through 처리."""
    if isinstance(api_result, list):
        return api_result
    return []
