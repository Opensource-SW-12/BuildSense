_W_P80          = 0.4
_W_HIGH_LOAD    = 0.4
_W_SUSTAINED    = 0.2
_SUSTAINED_CAP  = 5


def _grade(score: float) -> str:
    if score >= 0.7:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"


def score_cpu(cpu: dict) -> dict:
    """
    cpu: result["resource_usage"]["cpu"] from analyze_cpu_usage()
    returns: {"score": float, "grade": str, "factors": dict}
    """
    p80             = (cpu.get("raw") or {}).get("percentile_80") or 0.0
    high_load_ratio = cpu.get("high_load_ratio") or 0.0
    episode_count   = (cpu.get("sustained_high_load") or {}).get("episode_count") or 0

    p80_component       = (p80 / 100.0) * _W_P80
    high_load_component = high_load_ratio * _W_HIGH_LOAD
    sustained_component = min(episode_count / _SUSTAINED_CAP, 1.0) * _W_SUSTAINED

    score = round(min(p80_component + high_load_component + sustained_component, 1.0), 4)

    return {
        "score": score,
        "grade": _grade(score),
        "factors": {
            "p80_percent":      round(p80, 2),
            "high_load_ratio":  round(high_load_ratio, 4),
            "sustained_episodes": episode_count,
        },
    }
