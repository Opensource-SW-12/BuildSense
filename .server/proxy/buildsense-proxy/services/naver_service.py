"""
네이버 쇼핑 검색 API 호출 및 결과 가공.
기존 BuildSense의 price_fetcher.py에서 네이버 관련 로직만 분리.
응답에서 제목/가격/링크 등 필요한 필드만 골라서 정리해 반환
"""

import html
import json
import os
import re
import urllib.parse
import urllib.request


NAVER_SHOPPING_API_URL = "https://openapi.naver.com/v1/search/shop.json"


def _clean_title(title: str) -> str:
    """네이버 API 응답의 <b> 태그와 HTML 엔티티를 제거한다."""
    if not title:
        return title
    return html.unescape(re.sub(r"</?b>", "", title))


def _safe_int(value) -> int | None:
    try:
        return int(value) if value is not None else None
    except (ValueError, TypeError):
        return None


def search(query: str, display: int = 10) -> list[dict]:
    """
    네이버 쇼핑에서 query를 검색하고, 가공된 후보 리스트를 반환

    반환 형식:
        [
            {
                "source": "naver",
                "title": str,
                "link": str,
                "price_krw": int | None,
                "price_usd": None,
                "currency": "KRW",
                "mall_name": str | None,
                "brand": str | None,
                "maker": str | None,
            },
            ...
        ]
    """
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError("NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET 환경변수가 없습니다.")

    url = (
        f"{NAVER_SHOPPING_API_URL}"
        f"?query={urllib.parse.quote(query)}"
        f"&display={display}"
        f"&sort=sim"
    )

    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw = json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as e:
        raise RuntimeError(f"네이버 쇼핑 API 요청 실패: HTTP {e.code}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"네이버 쇼핑 API 연결 실패: {e}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"네이버 쇼핑 API 응답 JSON 해석 실패: {e}") from e

    candidates = []
    for item in raw.get("items", []):
        candidates.append({
            "source": "naver",
            "title": _clean_title(item.get("title")),
            "link": item.get("link"),
            "price_krw": _safe_int(item.get("lprice")),
            "price_usd": None,
            "currency": "KRW",
            "mall_name": item.get("mallName"),
            "brand": item.get("brand"),
            "maker": item.get("maker"),
        })

    return candidates
