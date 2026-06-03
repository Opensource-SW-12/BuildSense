import json
import urllib.request


EXCHANGE_RATE_API_URL = "https://open.er-api.com/v6/latest/USD"


def get_usd_to_krw_rate():
    try:
        with urllib.request.urlopen(EXCHANGE_RATE_API_URL, timeout=10) as response:
            response_body = response.read().decode("utf-8")
            data = json.loads(response_body)

        return data["rates"]["KRW"]

    except KeyError as error:
        raise RuntimeError(f"환율 응답 데이터에서 KRW 값을 찾을 수 없습니다: {error}") from error

    except json.JSONDecodeError as error:
        raise RuntimeError(f"환율 응답 JSON을 해석할 수 없습니다: {error}") from error

    except Exception as error:
        raise RuntimeError(f"환율 정보를 가져오는 데 실패했습니다: {error}") from error


def convert_usd_to_krw(usd_price, exchange_rate=None):
    if usd_price is None:
        return None

    try:
        usd_price = float(usd_price)

        if exchange_rate is None:
            exchange_rate = get_usd_to_krw_rate()

        return round(usd_price * exchange_rate)

    except ValueError as error:
        raise ValueError(f"USD 가격 값이 숫자로 변환될 수 없습니다: {usd_price}") from error