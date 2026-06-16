"""
USD → KRW 환율 조회.
기존 BuildSense의 exchange_rate.py를 이식하되,
서버에서는 매 요청마다 외부 API를 호출하지 않도록 1시간 TTL 캐싱을 추가.
"""

import json
import time
import urllib.request


EXCHANGE_RATE_API_URL = "https://open.er-api.com/v6/latest/USD"

# 캐시: (환율값, 만료시각)
_cached_rate: float | None = None
_rate_expires_at: float = 0

# 1시간마다 갱신
_CACHE_TTL_SECONDS = 3600


def get_usd_to_krw_rate() -> float:
    """
    USD → KRW 환율을 반환한다.
    1시간 이내에 조회한 값이 있으면 캐시를 재사용한다.
    """
    global _cached_rate, _rate_expires_at

    now = time.time()

    if _cached_rate is not None and now < _rate_expires_at:
        return _cached_rate

    try:
        with urllib.request.urlopen(EXCHANGE_RATE_API_URL, timeout=10) as response:
            data = json.loads(response.read().decode())

        rate = data["rates"]["KRW"]

        _cached_rate = rate
        _rate_expires_at = now + _CACHE_TTL_SECONDS

        return rate

    except KeyError as e:
        raise RuntimeError(f"환율 응답에서 KRW 값을 찾을 수 없습니다: {e}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"환율 응답 JSON 해석 실패: {e}") from e
    except Exception as e:
        raise RuntimeError(f"환율 정보 조회 실패: {e}") from e


def convert_usd_to_krw(usd_price: float, exchange_rate: float | None = None) -> int | None:
    """USD 가격을 KRW로 변환한다. exchange_rate를 생략하면 자동으로 조회한다."""
    if usd_price is None:
        return None

    if exchange_rate is None:
        exchange_rate = get_usd_to_krw_rate()

    return round(float(usd_price) * exchange_rate)
