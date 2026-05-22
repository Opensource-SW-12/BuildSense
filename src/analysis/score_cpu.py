_W_P80         = 0.4
_W_HIGH_LOAD   = 0.4
_W_SUSTAINED   = 0.2
_SUSTAINED_CAP = 5

# 규칙 기반 grade 임계값 (Intel/AMD 병목 기준 참고)
_HIGH_P80_THRESHOLD        = 80.0
_HIGH_LOAD_RATIO_THRESHOLD = 0.30
_HIGH_EPISODE_THRESHOLD    = 3
_MED_P80_THRESHOLD         = 60.0
_MED_LOAD_RATIO_THRESHOLD  = 0.15


def _grade(p80: float, high_load_ratio: float, episodes: int) -> str:
    if (p80 >= _HIGH_P80_THRESHOLD and high_load_ratio >= _HIGH_LOAD_RATIO_THRESHOLD) \
            or episodes >= _HIGH_EPISODE_THRESHOLD:
        return "high"
    if p80 >= _MED_P80_THRESHOLD or high_load_ratio >= _MED_LOAD_RATIO_THRESHOLD:
        return "medium"
    return "low"


def score_cpu(cpu: dict) -> dict:
    """
    cpu: result["resource_usage"]["cpu"] from analyze_cpu_usage()
    score — 연속값 (강도 측정 / 세션 간 비교용)
    grade — 규칙 기반 (업그레이드 추천 결정 기준)
    """
    p80            = (cpu.get("raw") or {}).get("percentile_80") or 0.0
    high_load_ratio = cpu.get("high_load_ratio") or 0.0
    episode_count  = (cpu.get("sustained_high_load") or {}).get("episode_count") or 0

    score = round(min(
        (p80 / 100.0) * _W_P80
        + high_load_ratio * _W_HIGH_LOAD
        + min(episode_count / _SUSTAINED_CAP, 1.0) * _W_SUSTAINED,
        1.0,
    ), 4)

    return {
        "score": score,
        "grade": _grade(p80, high_load_ratio, episode_count),
        "factors": {
            "p80_percent":        round(p80, 2),
            "high_load_ratio":    round(high_load_ratio, 4),
            "sustained_episodes": episode_count,
        },
    }
