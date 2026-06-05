"""
분석 점수·등급·사용자 유형을 바탕으로 추천 대상 부품을 선정하고 우선순위를 계산한다.
"""

# 분석 결과의 scores 키 → UI 부품명 매핑 (PSU는 직접 추천하지 않음)
_SCORE_KEY_TO_PART = {
    "cpu":      "CPU",
    "ram":      "RAM",
    "gpu_vram": "GPU",
    "ssd":      "SSD",
    "hdd":      "HDD",
}

# 사용자 유형별 부품 우선순위 보정 가중치
_USER_TYPE_BOOSTS: dict[str, dict[str, float]] = {
    "game":        {"GPU": 0.20, "CPU": 0.05, "RAM": 0.05},
    "development": {"CPU": 0.20, "RAM": 0.10},
    "creative":    {"GPU": 0.15, "CPU": 0.10, "SSD": 0.05},
    "business":    {"RAM": 0.10, "SSD": 0.05},
    "streaming":   {"GPU": 0.15, "CPU": 0.05},
}

# 사용자 유형별 이유 문구 접두어 (부품별)
_USER_TYPE_PREFIX: dict[str, dict[str, str]] = {
    "game":        {"GPU": "게임 워크로드에서 ", "CPU": "게임 실행 중 "},
    "development": {"CPU": "빌드·컴파일 작업에서 ", "RAM": "개발 환경에서 "},
    "creative":    {"GPU": "영상·렌더링 작업에서 ", "CPU": "크리에이티브 작업에서 "},
    "streaming":   {"GPU": "스트리밍·방송 중 "},
}

# 등급별 기본 이유 문구
_GRADE_REASONS: dict[str, dict[str, str]] = {
    "CPU": {
        "high":   "CPU가 지속적으로 고부하 상태입니다",
        "medium": "CPU 사용률이 간헐적으로 높습니다",
    },
    "GPU": {
        "high":    "GPU가 지속적으로 고부하 상태입니다",
        "medium":  "GPU 사용률이 간헐적으로 높습니다",
        "unknown": "GPU 사용 데이터를 수집하지 못했습니다",
    },
    "RAM": {
        "high":   "RAM이 자주 한계치에 도달합니다",
        "medium": "RAM 사용률이 간헐적으로 높습니다",
    },
    "SSD": {
        "high":   "SSD 여유 공간이 심각하게 부족합니다",
        "medium": "SSD 여유 공간이 줄어들고 있습니다",
    },
    "HDD": {
        "high":   "HDD 용량이 심각하게 부족합니다",
        "medium": "HDD를 SSD로 교체하면 체감 성능이 크게 향상됩니다",
    },
}


def _build_reason(part: str, grade: str, user_types: list[str]) -> str:
    base = _GRADE_REASONS.get(part, {}).get(grade, f"{part} 업그레이드가 필요합니다")
    for utype in user_types:
        prefix = _USER_TYPE_PREFIX.get(utype, {}).get(part)
        if prefix:
            return prefix + base
    return base


def _compute_priority(score: float, grade: str, part: str, user_types: list[str]) -> float:
    base = score
    for utype in user_types:
        base += _USER_TYPE_BOOSTS.get(utype, {}).get(part, 0.0)
    # high 등급에 추가 보정으로 medium과 명확히 구분
    if grade == "high":
        base += 0.1
    return min(base, 1.5)


def select_upgrade_targets(
    scores: dict,
    user_profile: dict,
    user_preferences: dict | None,
) -> list[dict]:
    """
    추천 대상 부품을 우선순위 순으로 반환한다.

    scores          : result["scores"] (app.py 분석 결과)
    user_profile    : user_profile.json (option="recommend" 부품 필터)
    user_preferences: user_preferences.json (현재는 참조만, 필터는 KAN-139에서 처리)

    반환:
        [
            {
                "part":     str,    # "CPU" | "GPU" | "RAM" | "SSD" | "HDD"
                "score":    float,  # 원본 점수 (0~1)
                "grade":    str,    # "high" | "medium" | "unknown"
                "priority": float,  # 보정 후 우선순위 (높을수록 먼저)
                "reason":   str,    # 추천 이유 문구
            },
            ...
        ]  # priority 내림차순 정렬
    """
    parts_config = (user_profile or {}).get("parts", {})
    user_types: list[str] = (
        scores.get("user_classification", {}).get("user_type") or []
    )

    targets = []

    for score_key, part in _SCORE_KEY_TO_PART.items():
        part_option = parts_config.get(part, {}).get("option", "recommend")
        if part_option != "recommend":
            continue

        part_score = scores.get(score_key)
        if part_score is None:
            continue

        score = part_score.get("score", 0.0)
        grade = part_score.get("grade", "low")

        # low 등급은 추천 불필요
        if grade == "low":
            continue

        # GPU unknown: 감지 실패이므로 낮은 우선순위로 포함
        if grade == "unknown":
            targets.append({
                "part":     part,
                "score":    0.0,
                "grade":    "unknown",
                "priority": 0.1,
                "reason":   _GRADE_REASONS["GPU"]["unknown"],
            })
            continue

        priority = _compute_priority(score, grade, part, user_types)
        reason   = _build_reason(part, grade, user_types)

        targets.append({
            "part":     part,
            "score":    score,
            "grade":    grade,
            "priority": priority,
            "reason":   reason,
        })

    targets.sort(key=lambda x: x["priority"], reverse=True)
    return targets
