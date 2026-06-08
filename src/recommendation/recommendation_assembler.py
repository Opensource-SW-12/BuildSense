"""
전체 추천 파이프라인을 실행해 최종 RecommendationItem 목록을 반환한다.

파이프라인:
  1. map_hardware_to_tiers     (KAN-136): hw_info → PassMark tier 매핑
  2. select_upgrade_targets    (KAN-137): 추천 대상 부품 선정 및 우선순위
  3. calculate_target_tiers    (KAN-138): 목표 tier / 목표 스펙 계산
  4. filter_spec_candidates    (KAN-139): PassMark 후보 필터링 또는 검색 쿼리 생성
  5. resolve_prices            (KAN-140): 네이버 API 가격 조회
  6. PSU 의존성 검사            (KAN-141): GPU 업그레이드 시 PSU 항목 추가
"""

from src.platform_mapper                        import infer_socket_from_cpu_name
from src.recommendation.chipset_tier_mapper     import map_hardware_to_tiers
from src.recommendation.upgrade_target_selector import select_upgrade_targets
from src.recommendation.target_tier_calculator  import calculate_target_tiers
from src.recommendation.spec_candidate_filter   import filter_spec_candidates
from src.recommendation.price_resolver          import resolve_prices

# score_psu grade(gold/platinum/titanium) → 사용자 표시 레이블
_PSU_GRADE_LABEL: dict[str, str] = {
    "gold":     "골드",
    "platinum": "플래티넘",
    "titanium": "티타늄",
}


def _build_psu_item(psu_score_data: dict, gpu_item: dict) -> dict:
    """
    GPU 업그레이드에 연동되는 PSU 의존성 항목을 생성한다.
    PSU는 직접 감지·가격 조회가 불가능하므로 candidates는 비워 둔다.
    """
    grade    = psu_score_data.get("grade", "platinum")   # gold | platinum | titanium
    label    = _PSU_GRADE_LABEL.get(grade, "플래티넘")
    score    = psu_score_data.get("score", 0.5)
    # GPU 우선순위보다 0.2 낮게 설정해 목록 후반부에 자연스럽게 배치
    priority = round(max(0.0, gpu_item.get("priority", 0.5) - 0.2), 4)

    return {
        "part":         "PSU",
        "score":        score,
        "grade":        grade,
        "priority":     priority,
        "reason":       (
            f"GPU 업그레이드 후 전력 소비가 증가합니다. "
            f"80+ {label} 이상 효율 등급의 PSU를 권장합니다."
        ),
        "current_tier": None,
        "target_tier":  None,
        "target_spec": {
            "recommended_efficiency": label,
            "note": f"업그레이드 GPU의 TDP를 확인하고 충분한 출력(W)의 PSU를 선택하세요.",
        },
        "candidates":   [],
        "search_query": None,
    }


def assemble_recommendations(
    scores: dict,
    hw_info: dict,
    user_profile: dict,
    user_preferences: dict | None,
) -> list[dict]:
    """
    전체 추천 파이프라인을 실행해 최종 RecommendationItem 목록을 반환한다.

    scores          : result["scores"]  (analyze 결과)
    hw_info         : get_hardware_info() 반환값
    user_profile    : user_profile.json
    user_preferences: user_preferences.json (budget, rgb_preference 등)

    반환: priority 내림차순으로 정렬된 RecommendationItem 목록
        [
            {
                "part":          str,          # CPU | GPU | RAM | SSD | HDD | PSU
                "score":         float,
                "grade":         str,          # low | medium | high | unknown
                                              # PSU는 gold | platinum | titanium
                "priority":      float,
                "reason":        str,
                "current_tier":  int | None,
                "target_tier":   int | None,
                "target_spec":   dict | None,
                "candidates":    list[dict],
                "search_query":  str | None,
            },
            ...
        ]
    """
    hw_tiers = map_hardware_to_tiers(hw_info)
    targets  = select_upgrade_targets(scores, user_profile, user_preferences)
    enriched = calculate_target_tiers(targets, hw_tiers, hw_info)
    # 노트북 등 소켓 정보가 없는 경우, 현재 CPU 모델명에서 소켓을 추론한다
    # (PassMark 조회 실패 시에도 메인보드 추천이 누락되지 않도록 하는 폴백)
    socket = hw_info.get("CPU_socket") or infer_socket_from_cpu_name(hw_info.get("CPU"))
    upgrade_motherboard = (
        (user_profile or {}).get("parts", {}).get("메인보드", {}).get("option") == "recommend"
    )
    filtered = filter_spec_candidates(
        enriched, user_preferences, socket=socket,
        upgrade_motherboard=upgrade_motherboard,
    )
    resolved = resolve_prices(filtered)

    # GPU 업그레이드가 추천 목록에 포함된 경우 PSU 의존성 항목 추가
    gpu_item = next((t for t in resolved if t["part"] == "GPU"), None)
    if gpu_item is not None:
        resolved.append(_build_psu_item(scores.get("psu", {}), gpu_item))

    resolved.sort(key=lambda x: x.get("priority", 0.0), reverse=True)
    return resolved
