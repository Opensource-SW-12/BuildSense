_W_PERCENT_P80  = 0.5
_W_DANGER       = 0.3
_W_FREE_PENALTY = 0.2

_FREE_PENALTY_MIN_GB = 10.0
_FREE_PENALTY_MAX_GB = 50.0
_HDD_FLOOR           = 0.3

# 규칙 기반 grade 임계값
# HDD 존재 자체가 SSD 교체 신호 → 기본 medium 보장
# 용량 문제까지 겹치면 high
_HIGH_P80_THRESHOLD    = 70.0
_HIGH_DANGER_THRESHOLD = 0.10


def _grade(percent_p80: float, danger_ratio: float) -> str:
    if percent_p80 >= _HIGH_P80_THRESHOLD or danger_ratio >= _HIGH_DANGER_THRESHOLD:
        return "high"
    return "medium"  # HDD 존재 자체 = 최소 medium


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


def _grade_drive(drive: dict) -> str:
    percent_p80  = (drive.get("percent_stats") or {}).get("percentile_80") or 0.0
    danger_ratio = drive.get("danger_ratio") or 0.0
    return _grade(percent_p80, danger_ratio)


def score_hdd(disk_usage: dict) -> dict | None:
    """
    disk_usage: result["disk_usage"] from analyze_disk_usage()
    HDD 드라이브만 스코어링. HDD 존재 자체 = 최소 medium.
    score — 연속값 (강도 측정 / 세션 간 비교용)
    grade — 규칙 기반 (업그레이드 추천 결정 기준)
    HDD 드라이브가 없으면 None 반환.
    """
    hdd_drives = {
        mp: drive for mp, drive in disk_usage.items()
        if drive.get("drive_type") == "HDD"
    }
    if not hdd_drives:
        return None

    drive_scores = {
        mp: {
            "score":      _score_drive(drive),
            "grade":      _grade_drive(drive),
            "drive_type": "HDD",
        }
        for mp, drive in hdd_drives.items()
    }

    worst = max(drive_scores.values(), key=lambda d: d["score"])

    return {
        "score":        worst["score"],
        "grade":        worst["grade"],
        "drive_scores": drive_scores,
    }
