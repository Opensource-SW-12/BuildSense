"""
eBay Browse API 검색 및 결과 가공.
기존 BuildSense의 price_fetcher.py에서 eBay 관련 로직만 분리.
"""

import json
import urllib.parse
import urllib.request

from services.ebay_auth import get_ebay_access_token, is_sandbox
from services.exchange_rate import get_usd_to_krw_rate, convert_usd_to_krw
import os


_EBAY_SEARCH_PROD = "https://api.ebay.com/buy/browse/v1/item_summary/search"
_EBAY_SEARCH_SBX  = "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search"


def _search_url() -> str:
    client_id = os.getenv("EBAY_CLIENT_ID", "")
    return _EBAY_SEARCH_SBX if is_sandbox(client_id) else _EBAY_SEARCH_PROD


def _safe_float(value) -> float | None:
    try:
        return float(value) if value is not None else None
    except (ValueError, TypeError):
        return None


def search(query: str, limit: int = 10) -> list[dict]:
    """
    eBay에서 query를 검색하고, KRW 환산 가격이 포함된 후보 리스트를 반환한다.

    반환 형식:
        [
            {
                "source": "ebay",
                "title": str,
                "link": str,
                "price_usd": float | None,
                "price_krw": int | None,
                "currency": str | None,
                "seller": str | None,
            },
            ...
        ]
    """
    token = get_ebay_access_token()

    url = (
        f"{_search_url()}"
        f"?q={urllib.parse.quote(query)}"
        f"&limit={limit}"
    )

    request = urllib.request.Request(url)
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("X-EBAY-C-MARKETPLACE-ID", "EBAY_US")

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw = json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as e:
        raise RuntimeError(f"eBay API 요청 실패: HTTP {e.code}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"eBay API 연결 실패: {e}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"eBay API 응답 JSON 해석 실패: {e}") from e

    # 환율은 한 번만 가져와서 전체 아이템에 재사용
    exchange_rate = get_usd_to_krw_rate()

    candidates = []
    for item in raw.get("itemSummaries", []):
        price_info = item.get("price", {})
        currency = price_info.get("currency")
        price_usd = _safe_float(price_info.get("value")) if currency == "USD" else None
        price_krw = convert_usd_to_krw(price_usd, exchange_rate) if price_usd is not None else None

        candidates.append({
            "source": "ebay",
            "title": item.get("title"),
            "link": item.get("itemWebUrl"),
            "price_usd": price_usd,
            "price_krw": price_krw,
            "currency": currency,
            "seller": item.get("seller", {}).get("username"),
        })

    return candidates
