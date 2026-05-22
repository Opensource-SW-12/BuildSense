_W_P80          = 0.4
_W_HIGH_LOAD    = 0.4
_W_SUSTAINED    = 0.2
_SUSTAINED_CAP_MINUTES = 60


def _grade(score: float) -> str:
    if score >= 0.7:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"


def score_ram(ram: dict) -> dict:
    """
    ram: result["resource_usage"]["ram"] from analyze_ram_usage()
    returns: {"score": float, "grade": str, "factors": dict}
    """
    p80                      = (ram.get("raw") or {}).get("percentile_80") or 0.0
    high_load_ratio          = ram.get("high_load_ratio") or 0.0
    max_sustained_minutes    = ram.get("max_sustained_high_load_minutes") or 0.0

    p80_component       = (p80 / 100.0) * _W_P80
    high_load_component = high_load_ratio * _W_HIGH_LOAD
    sustained_component = min(max_sustained_minutes / _SUSTAINED_CAP_MINUTES, 1.0) * _W_SUSTAINED

    score = round(min(p80_component + high_load_component + sustained_component, 1.0), 4)

    return {
        "score": score,
        "grade": _grade(score),
        "factors": {
            "p80_percent":                round(p80, 2),
            "high_load_ratio":            round(high_load_ratio, 4),
            "max_sustained_high_load_minutes": round(max_sustained_minutes, 1),
        },
    }
