_W_PERCENT_P80   = 0.5
_W_DANGER        = 0.3
_W_FREE_PENALTY  = 0.2

_FREE_PENALTY_MIN_GB  = 10.0   # 이하면 페널티 1.0
_FREE_PENALTY_MAX_GB  = 50.0   # 이상이면 페널티 0.0


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

    return min(
        (percent_p80 / 100.0) * _W_PERCENT_P80
        + danger_ratio         * _W_DANGER
        + _free_penalty(free_min) * _W_FREE_PENALTY,
        1.0,
    )


def score_disk(disk_usage: dict) -> dict:
    """
    disk_usage: result["disk_usage"] from analyze_disk_usage()
    returns: {"score": float, "grade": str, "drive_scores": dict}
    """
    if not disk_usage:
        return {"score": 0.0, "grade": "low", "drive_scores": {}}

    drive_scores = {
        mountpoint: round(_score_drive(drive), 4)
        for mountpoint, drive in disk_usage.items()
    }

    score = round(max(drive_scores.values()), 4)

    return {
        "score": score,
        "grade": _grade(score),
        "drive_scores": drive_scores,
    }
