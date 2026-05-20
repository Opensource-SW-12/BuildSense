import json
import statistics


def read_jsonl(file_path):
    data = []

    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if line:
                data.append(json.loads(line))

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
        return {
            "normalized": [],
            "is_constant": False
        }

    min_value = min(values)
    max_value = max(values)

    if min_value == max_value:
        return {
            "normalized": [0 for _ in values],
            "is_constant": True
        }

    normalized = [
        (value - min_value) / (max_value - min_value)
        for value in values
    ]

    return {
        "normalized": normalized,
        "is_constant": False
    }


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
            "percentile_80": None
        }

    return {
        "min": min(values),
        "max": max(values),
        "average": statistics.mean(values),
        "median": statistics.median(values),
        "percentile_80": percentile(values, 80)
    }