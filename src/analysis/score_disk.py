_W_PERCENT_P80   = 0.5
_W_DANGER        = 0.3
_W_FREE_PENALTY  = 0.2

_FREE_PENALTY_MIN_GB  = 10.0
_FREE_PENALTY_MAX_GB  = 50.0

# HDD는 SSD 대비 성능이 낮으므로 업그레이드 추천을 유도하는 기본 패널티
_HDD_BASE_PENALTY = 0.3


def _grade(score: float) -> str:
    if score >= 0.7:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"


def _free_penalty(free_min_gb: float | None) -> float:
    if free_min_gb is None:
        return 0.0
    if free_min_gb <= _FREE_PENALTY_MIN_GB:
        return 1.0
    if free_min_gb >= _FREE_PENALTY_MAX_GB:
        return 0.0
    return (_FREE_PENALTY_MAX_GB - free_min_gb) / (_FREE_PENALTY_MAX_GB - _FREE_PENALTY_MIN_GB)


def _score_drive(drive: dict) -> float:
    percent_p80  = (drive.get("percent_stats") or {}).get("percentile_80") or 0.0
    danger_ratio = drive.get("danger_ratio") or 0.0
    free_min     = (drive.get("free_gb_stats") or {}).get("min")
    drive_type   = drive.get("drive_type", "Unknown")

    capacity_score = (
        (percent_p80 / 100.0) * _W_PERCENT_P80
        + danger_ratio         * _W_DANGER
        + _free_penalty(free_min) * _W_FREE_PENALTY
    )

    if drive_type == "HDD":
        return min(capacity_score + _HDD_BASE_PENALTY, 1.0)
    return min(capacity_score, 1.0)


def score_disk(disk_usage: dict) -> dict:
    """
    disk_usage: result["disk_usage"] from analyze_disk_usage()
    returns: {"score": float, "grade": str, "drive_scores": dict}
    """
    if not disk_usage:
        return {"score": 0.0, "grade": "low", "drive_scores": {}}

    drive_scores = {}
    for mountpoint, drive in disk_usage.items():
        drive_scores[mountpoint] = {
            "score":      round(_score_drive(drive), 4),
            "drive_type": drive.get("drive_type", "Unknown"),
        }

    score = round(max(d["score"] for d in drive_scores.values()), 4)

    return {
        "score":        score,
        "grade":        _grade(score),
        "drive_scores": drive_scores,
    }
