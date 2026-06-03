_W_P80         = 0.4
_W_HIGH_LOAD   = 0.4
_W_SUSTAINED   = 0.2
_SUSTAINED_CAP_MINUTES = 60

# 규칙 기반 grade 임계값
# RAM 85%+ 지속 = 가상 메모리 사용 시작 구간 (일반적 업그레이드 권장 기준)
_HIGH_P80_THRESHOLD        = 85.0
_HIGH_LOAD_RATIO_THRESHOLD = 0.20
_HIGH_SUSTAINED_THRESHOLD  = 30.0  # 분
_MED_P80_THRESHOLD         = 75.0
_MED_LOAD_RATIO_THRESHOLD  = 0.10


def _grade(p80: float, high_load_ratio: float, max_sustained_minutes: float) -> str:
    if (p80 >= _HIGH_P80_THRESHOLD and high_load_ratio >= _HIGH_LOAD_RATIO_THRESHOLD) \
            or max_sustained_minutes >= _HIGH_SUSTAINED_THRESHOLD:
        return "high"
    if p80 >= _MED_P80_THRESHOLD or high_load_ratio >= _MED_LOAD_RATIO_THRESHOLD:
        return "medium"
    return "low"


def score_ram(ram: dict) -> dict:
    """
    ram: result["resource_usage"]["ram"] from analyze_ram_usage()
    score — 연속값 (강도 측정 / 세션 간 비교용)
    grade — 규칙 기반 (업그레이드 추천 결정 기준)
    """
    p80                   = (ram.get("raw") or {}).get("percentile_80") or 0.0
    high_load_ratio       = ram.get("high_load_ratio") or 0.0
    max_sustained_minutes = ram.get("max_sustained_high_load_minutes") or 0.0

    score = round(min(
        (p80 / 100.0) * _W_P80
        + high_load_ratio * _W_HIGH_LOAD
        + min(max_sustained_minutes / _SUSTAINED_CAP_MINUTES, 1.0) * _W_SUSTAINED,
        1.0,
    ), 4)

    return {
        "score": score,
        "grade": _grade(p80, high_load_ratio, max_sustained_minutes),
        "factors": {
            "p80_percent":                    round(p80, 2),
            "high_load_ratio":                round(high_load_ratio, 4),
            "max_sustained_high_load_minutes": round(max_sustained_minutes, 1),
        },
    }
