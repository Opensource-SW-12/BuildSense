import json
import os


def save_price_candidates(candidates, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(
                candidates,
                file,
                ensure_ascii=False,
                indent=2
            )

    except OSError as error:
        raise RuntimeError(
            f"가격 후보 저장 실패: {error}"
        ) from error


def load_price_candidates(input_path):
    if not os.path.exists(input_path):
        return []

    try:
        with open(input_path, "r", encoding="utf-8") as file:
            return json.load(file)

    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"가격 후보 JSON 해석 실패: {error}"
        ) from error

    except OSError as error:
        raise RuntimeError(
            f"가격 후보 불러오기 실패: {error}"
        ) from error