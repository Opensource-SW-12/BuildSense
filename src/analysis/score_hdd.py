_W_PERCENT_P80  = 0.5
_W_DANGER       = 0.3
_W_FREE_PENALTY = 0.2

_FREE_PENALTY_MIN_GB = 10.0
_FREE_PENALTY_MAX_GB = 50.0

# HDD는 기술 자체가 구식이므로 최소 스코어를 보장 (업그레이드 추천 유도)
_HDD_FLOOR = 0.3


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

    capacity_score = (
        (percent_p80 / 100.0) * _W_PERCENT_P80
        + danger_ratio          * _W_DANGER
        + _free_penalty(free_min) * _W_FREE_PENALTY
    )

    return round(min(max(capacity_score, _HDD_FLOOR), 1.0), 4)


def score_hdd(disk_usage: dict) -> dict | None:
    """
    disk_usage: result["disk_usage"] from analyze_disk_usage()
    HDD 드라이브만 스코어링. HDD는 최소 0.3 보장 (SSD 업그레이드 추천 유도).
    HDD 드라이브가 없으면 None 반환.
    """
    hdd_drives = {
        mp: drive for mp, drive in disk_usage.items()
        if drive.get("drive_type") == "HDD"
    }
    if not hdd_drives:
        return None

    drive_scores = {
        mp: {"score": _score_drive(drive), "drive_type": "HDD"}
        for mp, drive in hdd_drives.items()
    }

    score = round(max(d["score"] for d in drive_scores.values()), 4)

    return {
        "score":        score,
        "grade":        _grade(score),
        "drive_scores": drive_scores,
    }
