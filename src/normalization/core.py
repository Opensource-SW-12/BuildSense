import json
import statistics


def read_jsonl(file_path):
    data = []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                line = line.strip()

                if not line:
                    continue

                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError as error:
                    print(f"[JSONL 오류] {line_number}번째 줄을 읽을 수 없습니다: {error}")

    except FileNotFoundError:
        print(f"[파일 오류] 파일을 찾을 수 없습니다: {file_path}")

    except PermissionError:
        print(f"[파일 오류] 파일 접근 권한이 없습니다: {file_path}")

    except OSError as error:
        print(f"[파일 오류] 파일을 읽는 중 문제가 발생했습니다: {error}")

    return data


def remove_none(values):
    return [value for value in values if value is not None]


def remove_outliers(values):
    values = remove_none(values)

    if len(values) < 30:
        return values

    mean = statistics.mean(values)
    stdev = statistics.stdev(values)

    lower = mean - (3 * stdev)
    upper = mean + (3 * stdev)

    return [value for value in values if lower <= value <= upper]


def min_max_normalize(values):
    values = remove_none(values)

    if not values:
        return {"normalized": [], "is_constant": False}

    min_value = min(values)
    max_value = max(values)

    if min_value == max_value:
        return {"normalized": [0 for _ in values], "is_constant": True}

    normalized = [(value - min_value) / (max_value - min_value) for value in values]

    return {"normalized": normalized, "is_constant": False}


def percentile(values, p):
    values = sorted(remove_none(values))

    if not values:
        return None

    index = int(len(values) * p / 100)

    if index >= len(values):
        index = len(values) - 1

    return values[index]


def calculate_basic_stats(values):
    values = remove_outliers(values)

    if not values:
        return {
            "min": None,
            "max": None,
            "average": None,
            "median": None,
            "percentile_80": None,
        }

    return {
        "min": min(values),
        "max": max(values),
        "average": statistics.mean(values),
        "median": statistics.median(values),
        "percentile_80": percentile(values, 80),
    }
