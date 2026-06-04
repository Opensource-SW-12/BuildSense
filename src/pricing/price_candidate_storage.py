import json
from pathlib import Path


def save_price_candidates(candidates, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with output_path.open("w", encoding="utf-8") as file:
            json.dump(
                candidates,
                file,
                ensure_ascii=False,
                indent=2
            )

    except TypeError as error:
        raise RuntimeError(
            f"가격 후보 데이터를 JSON으로 변환할 수 없습니다: {error}"
        ) from error

    except OSError as error:
        raise RuntimeError(
            f"가격 후보 저장 실패: {error}"
        ) from error


def load_price_candidates(input_path):
    input_path = Path(input_path)

    if not input_path.exists():
        return []

    try:
        with input_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"가격 후보 JSON 해석 실패: {error}"
        ) from error

    except OSError as error:
        raise RuntimeError(
            f"가격 후보 불러오기 실패: {error}"
        ) from error