from collections import Counter

from src.normalization.core import (
    calculate_basic_stats,
    min_max_normalize,
    remove_outliers,
)

_SUSTAINED_HIGH_LOAD_N = 5  # 연속 고부하 감지 기준 스냅샷 수 (60초 기준 약 5분)
_MONITOR_INTERVAL_SECONDS = 60


def _stats_with_normalized(values: list) -> dict:
    clean = remove_outliers(values)
    raw = calculate_basic_stats(values)

    if not clean:
        empty = {"min": None, "max": None, "average": None, "median": None, "percentile_80": None}
        return {"raw": raw, "normalized": {**empty, "is_constant": False}}

    norm = min_max_normalize(clean)
    if norm["is_constant"]:
        norm_stats = {
            "min": 0.0, "max": 0.0, "average": 0.0,
            "median": 0.0, "percentile_80": 0.0, "is_constant": True,
        }
    else:
        norm_stats = {**calculate_basic_stats(norm["normalized"]), "is_constant": False}

    return {"raw": raw, "normalized": norm_stats}


def _high_load_ratio(values: list, threshold: float) -> float:
    valid = [v for v in values if v is not None]
    if not valid:
        return 0.0
    return sum(1 for v in valid if v >= threshold) / len(valid)


def _sustained_episodes(values: list, threshold: float, min_count: int = _SUSTAINED_HIGH_LOAD_N) -> dict:
    episodes = 0
    current = 0
    for v in values:
        if v is not None and v >= threshold:
            current += 1
        else:
            if current >= min_count:
                episodes += 1
            current = 0
    if current >= min_count:
        episodes += 1
    return {"episode_count": episodes, "min_consecutive_snapshots": min_count}


def _max_sustained_minutes(values: list, threshold: float) -> float:
    max_streak = 0
    current = 0
    for v in values:
        if v is not None and v >= threshold:
            current += 1
            max_streak = max(max_streak, current)
        else:
            current = 0
    return round(max_streak * _MONITOR_INTERVAL_SECONDS / 60, 1)


def _mode(values: list):
    if not values:
        return None
    return Counter(round(v, 0) for v in values).most_common(1)[0][0]


def analyze_cpu_usage(logs: list) -> dict:
    cpu_values = [log.get("cpu_percent") for log in logs]
    return {
        **_stats_with_normalized(cpu_values),
        "high_load_ratio": _high_load_ratio(cpu_values, 75),
        "sustained_high_load": _sustained_episodes(cpu_values, 75),
    }


def analyze_ram_usage(logs: list) -> dict:
    ram_values = [log.get("ram_percent") for log in logs]
    return {
        **_stats_with_normalized(ram_values),
        "high_load_ratio": _high_load_ratio(ram_values, 85),
        "max_sustained_high_load_minutes": _max_sustained_minutes(ram_values, 85),
    }


def analyze_gpu_usage(logs: list) -> dict:
    gpu_values = [log.get("gpu_percent") for log in logs]
    total_count = len(gpu_values)
    none_count = sum(1 for v in gpu_values if v is None)
    valid_gpu = [v for v in gpu_values if v is not None]

    return {
        **_stats_with_normalized(valid_gpu),
        "gpu_not_detected_ratio": none_count / total_count if total_count > 0 else 0.0,
        "high_load_ratio": _high_load_ratio(valid_gpu, 80),
    }


def analyze_vram_usage(logs: list) -> dict:
    used_values = []
    pct_values = []
    total_candidates = []

    for log in logs:
        used = log.get("vram_used_mb")
        total = log.get("vram_total_mb")

        if total is not None and total > 0:
            total_candidates.append(total)

        if used is None or total is None or total == 0:
            continue

        used_values.append(used)
        pct_values.append((used / total) * 100)

    return {
        "vram_total_mb": _mode(total_candidates),
        "used_mb": _stats_with_normalized(used_values),
        "usage_percent": _stats_with_normalized(pct_values),
        "high_load_ratio": _high_load_ratio(pct_values, 90),
    }


def analyze_resource_usage(logs: list) -> dict:
    return {
        "cpu":  analyze_cpu_usage(logs),
        "ram":  analyze_ram_usage(logs),
        "gpu":  analyze_gpu_usage(logs),
        "vram": analyze_vram_usage(logs),
    }
