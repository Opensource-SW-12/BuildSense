import json

from src.config import USAGE_LOG_PATH
from src.analysis.resource_usage import analyze_resource_usage
from src.analysis.usage_pattern_summary import create_usage_pattern_summary
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


def collect_report_data(logs: list[dict], profile: dict | None = None) -> dict:
    if not logs:
        return {}

    resource = analyze_resource_usage(logs)
    pattern = create_usage_pattern_summary(logs)
    disk = analyze_disk_usage(logs)
    process = analyze_process_usage(logs)

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
        "pattern":         pattern,
        "disk":            disk,
        "process":         process,
        "user_type":       user_type,
        "scores":          scores,
        "profile":         profile,
        "total_snapshots": len(logs),
    }
