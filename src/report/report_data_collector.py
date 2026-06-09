import json

from src.config import USAGE_LOG_PATH
from src.analysis.resource_usage import analyze_resource_usage
from src.analysis.usage_pattern_summary import create_usage_pattern_summary, parse_utc_to_kst
from src.analysis.disk_usage import analyze_disk_usage
from src.analysis.process_usage import analyze_process_usage
from src.analysis.user_type import classify_user_type
from src.analysis.score_cpu import score_cpu
from src.analysis.score_ram import score_ram
from src.analysis.score_gpu_vram import score_gpu_vram
from src.analysis.score_ssd import score_ssd
from src.analysis.score_hdd import score_hdd
from src.analysis.score_psu import score_psu


def load_usage_logs() -> list[dict]:
    if not USAGE_LOG_PATH.exists():
        return []

    logs = []
    with open(USAGE_LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                logs.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    return logs


def _extract_raw_series(logs: list[dict]) -> dict:
    return {
        "cpu":         [log.get("cpu_percent") for log in logs],
        "ram":         [log.get("ram_percent") for log in logs],
        "gpu":         [log.get("gpu_percent") for log in logs],
        "vram_used_mb": [log.get("vram_used_mb") for log in logs],
    }


def _extract_pattern_series(logs: list[dict]) -> dict:
    hourly = [0] * 24
    daily  = [0] * 7
    hourly_by_day = [[0] * 24 for _ in range(7)]

    for log in logs:
        kst = parse_utc_to_kst(log.get("timestamp"))
        if kst is None:
            continue
        hourly[kst.hour] += 1
        daily[kst.weekday()] += 1
        hourly_by_day[kst.weekday()][kst.hour] += 1

    return {
        "hourly":        hourly,
        "daily":         daily,
        "hourly_by_day": hourly_by_day,
    }


def collect_report_data(
    logs: list[dict],
    profile: dict | None = None,
    user_preferences: dict | None = None,
) -> dict:
    if not logs:
        return {}

    resource = analyze_resource_usage(logs)
    pattern = create_usage_pattern_summary(logs)
    disk = analyze_disk_usage(logs)

    # user_preferences의 수동 프로세스 분류를 반영해 카테고리 집계
    extra_cats = (user_preferences or {}).get("unknown_process_categories") or {}
    process = analyze_process_usage(logs, extra_categories=extra_cats)

    user_type = classify_user_type(
        {"resource_usage": resource, "process_usage": process},
        total_snapshots=len(logs),
    )

    scores = {
        "cpu":     score_cpu(resource["cpu"]),
        "ram":     score_ram(resource["ram"]),
        "gpu_vram": score_gpu_vram(resource["gpu"], resource["vram"]),
        "ssd":     score_ssd(disk),
        "hdd":     score_hdd(disk),
        "psu":     score_psu(pattern),
    }

    return {
        "resource":        resource,
        "raw_series":      _extract_raw_series(logs),
        "pattern_series":  _extract_pattern_series(logs),
        "pattern":         pattern,
        "disk":            disk,
        "process":         process,
        "user_type":       user_type,
        "scores":          scores,
        "profile":         profile,
        "total_snapshots": len(logs),
    }
