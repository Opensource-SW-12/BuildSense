import json
import os
import urllib.parse
import urllib.request


NAVER_SHOPPING_API_URL = "https://openapi.naver.com/v1/search/shop.json"

EBAY_SEARCH_API_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"

def build_search_query(part):
    manufacturer = part.get("manufacturer", "")
    name = part.get("name", "")

    return f"{manufacturer} {name}".strip()


def search_naver_shopping(query, display=10):
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError(
            "NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET 환경변수가 없습니다."
        )

    encoded_query = urllib.parse.quote(query)

    url = (
        f"{NAVER_SHOPPING_API_URL}"
        f"?query={encoded_query}"
        f"&display={display}"
        f"&sort=sim"
    )

    request = urllib.request.Request(url)

    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            response_body = response.read().decode("utf-8")

        return json.loads(response_body)

    except urllib.error.HTTPError as error:
        raise RuntimeError(
            f"네이버 쇼핑 API 요청 실패: {error.code}"
        ) from error

    except urllib.error.URLError as error:
        raise RuntimeError(
            f"네이버 쇼핑 API 연결 실패: {error}"
        ) from error

    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"네이버 쇼핑 API 응답 JSON 해석 실패: {error}"
        ) from error


def extract_naver_candidates(api_result):
    candidates = []

    for item in api_result.get("items", []):
        price = item.get("lprice")

        candidates.append({
            "source": "naver",
            "title": item.get("title"),
            "link": item.get("link"),
            "price_krw": int(price) if price else None,
            "mall_name": item.get("mallName"),
            "brand": item.get("brand"),
            "maker": item.get("maker")
        })

def search_ebay(query, limit=10):
    ebay_token = os.getenv("EBAY_ACCESS_TOKEN")

    if not ebay_token:
        raise ValueError("EBAY_ACCESS_TOKEN 환경변수가 없습니다.")

    encoded_query = urllib.parse.quote(query)

    url = (
        f"{EBAY_SEARCH_API_URL}"
        f"?q={encoded_query}"
        f"&limit={limit}"
    )

    request = urllib.request.Request(url)
    request.add_header("Authorization", f"Bearer {ebay_token}")
    request.add_header("X-EBAY-C-MARKETPLACE-ID", "EBAY_US")

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            response_body = response.read().decode("utf-8")

        return json.loads(response_body)

    except urllib.error.HTTPError as error:
        raise RuntimeError(
            f"eBay API 요청 실패: {error.code}"
        ) from error

    except urllib.error.URLError as error:
        raise RuntimeError(
            f"eBay API 연결 실패: {error}"
        ) from error

    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"eBay API 응답 JSON 해석 실패: {error}"
        ) from error
    
    return candidates