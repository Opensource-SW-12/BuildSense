_W_PERCENT_P80  = 0.5
_W_DANGER       = 0.3
_W_FREE_PENALTY = 0.2

_FREE_PENALTY_MIN_GB = 10.0
_FREE_PENALTY_MAX_GB = 50.0


def _free_penalty(free_min_gb: float | None) -> float:
    if free_min_gb is None:
        return 0.0
    if free_min_gb <= _FREE_PENALTY_MIN_GB:
        return 1.0
    if free_min_gb >= _FREE_PENALTY_MAX_GB:
        return 0.0
    return (_FREE_PENALTY_MAX_GB - free_min_gb) / (_FREE_PENALTY_MAX_GB - _FREE_PENALTY_MIN_GB)


def capacity_score(drive: dict) -> float:
    """드라이브 용량 기반 원시 점수 (0.0~1.0 범위 보정 전). SSD/HDD 공용."""
    percent_p80  = (drive.get("percent_stats") or {}).get("percentile_80") or 0.0
    danger_ratio = drive.get("danger_ratio") or 0.0
    free_min     = (drive.get("free_gb_stats") or {}).get("min")
    return (
        (percent_p80 / 100.0) * _W_PERCENT_P80
        + danger_ratio          * _W_DANGER
        + _free_penalty(free_min) * _W_FREE_PENALTY
    )
