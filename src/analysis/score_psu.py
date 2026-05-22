_HOURS_PER_DAY  = 24.0
_TITANIUM_HOURS = 20.0
_PLATINUM_HOURS = 8.0

_W_UPTIME    = 0.7
_W_LONG_RATIO = 0.3


def _grade(avg_hours: float) -> str:
    """
    grade = recommended PSU efficiency tier (규칙 기반)
    avg_hours < 8h  → "gold"     (일반 사용자)
    8h ≤ avg < 20h  → "platinum" (중간 사용자)
    avg ≥ 20h       → "titanium" (헤비 유저 / 상시 가동)
    """
    if avg_hours >= _TITANIUM_HOURS:
        return "titanium"
    if avg_hours >= _PLATINUM_HOURS:
        return "platinum"
    return "gold"


def score_psu(usage_pattern: dict) -> dict:
    """
    usage_pattern: result["usage_pattern"] from create_usage_pattern_summary()
    score — 연속값 (강도 측정 / 세션 간 비교용)
    grade — 규칙 기반 추천 PSU 효율 등급 (gold / platinum / titanium)
    """
    uptime     = usage_pattern.get("uptime") or {}
    avg_hours  = uptime.get("average_uptime_hours") or 0.0
    long_ratio = uptime.get("long_usage_ratio") or 0.0

    score = round(min(
        (avg_hours / _HOURS_PER_DAY) * _W_UPTIME + long_ratio * _W_LONG_RATIO,
        1.0,
    ), 4)

    return {
        "score": score,
        "grade": _grade(avg_hours),
        "factors": {
            "average_uptime_hours": round(avg_hours, 2),
            "long_usage_ratio":     round(long_ratio, 4),
        },
    }
