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
from src.pricing.passmark_tiering               import calculate_gpu_tier
from src.recommendation.chipset_tier_mapper     import map_hardware_to_tiers
from src.recommendation.upgrade_target_selector import select_upgrade_targets
from src.recommendation.target_tier_calculator  import calculate_target_tiers
from src.recommendation.spec_candidate_filter   import filter_spec_candidates, get_board_candidates
from src.recommendation.price_resolver          import resolve_prices

# score_psu grade(gold/platinum/titanium) → 사용자 표시 레이블
_PSU_GRADE_LABEL: dict[str, str] = {
    "gold":     "골드",
    "platinum": "플래티넘",
    "titanium": "티타늄",
}

# PassMark tier(0-29) → 대표 데스크톱 TDP(W) 근사값
# tier = int((passmark_score / max_score) * 29)
_CPU_TIER_TDP: list[tuple[int, int]] = [
    (8,  65), (14,  95), (18, 125), (22, 165), (29, 253),
]
_GPU_TIER_TDP: list[tuple[int, int]] = [
    (5,  75), (10, 150), (14, 200), (18, 250), (22, 320), (29, 400),
]
_SYSTEM_OVERHEAD_W = 100   # RAM·SSD·메인보드·쿨러·팬 등 기타 소비전력
_PSU_SAFETY_MARGIN = 1.25  # 25% 여유 (안정성 마진)
_PSU_STANDARD_WATT = [400, 500, 550, 600, 650, 700, 750, 800, 850, 1000, 1200]


def _tier_to_tdp(tier: int | None, table: list[tuple[int, int]]) -> int:
    """tier 값을 대표 TDP(W)로 변환한다. tier가 None이면 중간 기본값 반환."""
    if tier is None:
        return table[len(table) // 2][1]
    for threshold, tdp in table:
        if tier <= threshold:
            return tdp
    return table[-1][1]


def _recommend_wattage(cpu_tier: int | None, gpu_tier: int | None) -> int:
    """CPU·GPU tier를 기반으로 최소 권장 PSU 용량(W)을 반환한다."""
    raw = (
        _tier_to_tdp(cpu_tier, _CPU_TIER_TDP)
        + _tier_to_tdp(gpu_tier, _GPU_TIER_TDP)
        + _SYSTEM_OVERHEAD_W
    ) * _PSU_SAFETY_MARGIN
    for w in _PSU_STANDARD_WATT:
        if w >= raw:
            return w
    return _PSU_STANDARD_WATT[-1]


def _build_psu_item(
    psu_score_data: dict,
    gpu_item: dict,
    cpu_item: dict | None = None,
    color_suffix: str = "",
) -> dict:
    """GPU 업그레이드에 연동되는 PSU 의존성 항목을 생성한다."""
    grade    = psu_score_data.get("grade", "platinum")
    label    = _PSU_GRADE_LABEL.get(grade, "플래티넘")
    score    = psu_score_data.get("score", 0.5)
    priority = round(max(0.0, gpu_item.get("priority", 0.5) - 0.2), 4)

    cpu_tier = (cpu_item or {}).get("target_tier")
    gpu_tier = gpu_item.get("target_tier")
    min_watt = _recommend_wattage(cpu_tier, gpu_tier)

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
            "min_wattage":            min_watt,
            "note": f"{min_watt}W 이상, 80+ {label} 등급 권장",
        },
        "candidates":   [],
        "search_query": f"파워서플라이 {min_watt}W 80PLUS {label}{color_suffix}",
    }


def _build_motherboard_item_for_owned_cpu(
    socket: str,
    owned_cpu_name: str,
    color_suffix: str = "",
) -> dict:
    """'보유' CPU의 소켓을 기준으로 메인보드 호환성 체크 항목을 생성한다. (KAN-195)"""
    board_cands = get_board_candidates(socket, target_cpu_name=owned_cpu_name)

    return {
        "part":         "Motherboard",
        "score":        0.0,
        "grade":        "medium",
        "priority":     0.3,
        "reason":       (
            f"보유 예정인 {owned_cpu_name} 기준 {socket} 소켓 호환 메인보드입니다."
        ),
        "current_tier": None,
        "target_tier":  None,
        "target_spec": {
            "socket": socket,
            "note":   f"{socket} 소켓 호환 메인보드",
        },
        "candidates":   board_cands,
        "search_query": f"메인보드 {socket}{color_suffix}",
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
    hw_tiers    = map_hardware_to_tiers(hw_info)
    targets     = select_upgrade_targets(scores, user_profile, user_preferences)
    budget_mode = (user_preferences or {}).get("budget_mode", "recommended")
    enriched    = calculate_target_tiers(targets, hw_tiers, hw_info, budget_mode=budget_mode)
    # 노트북 등 소켓 정보가 없는 경우, 현재 CPU 모델명에서 소켓을 추론한다
    # (PassMark 조회 실패 시에도 메인보드 추천이 누락되지 않도록 하는 폴백)
    socket = hw_info.get("CPU_socket") or infer_socket_from_cpu_name(hw_info.get("CPU"))
    upgrade_motherboard = (
        (user_profile or {}).get("parts", {}).get("메인보드", {}).get("option") == "recommend"
    )
    filtered = filter_spec_candidates(
        enriched, user_preferences, socket=socket,
        upgrade_motherboard=upgrade_motherboard,
        current_cpu=hw_info.get("CPU"),
    )

    # GPU 업그레이드가 추천 목록에 포함된 경우 PSU 의존성 항목을 resolve_prices 전에 추가해
    # 네이버 가격 조회가 함께 실행되도록 한다
    _color_pref = (user_preferences or {}).get("color_preference", "none")
    _color_sfx  = {"black": " 블랙", "white": " 화이트"}.get(_color_pref, "")

    parts_config = (user_profile or {}).get("parts", {})

    # KAN-195: CPU '보유' + 메인보드 '추천' → 보유 예정 CPU의 소켓 기준 메인보드 호환성 체크
    cpu_state = parts_config.get("CPU", {})
    if cpu_state.get("option") == "owned" and parts_config.get("메인보드", {}).get("option") == "recommend":
        owned_cpu_name = (cpu_state.get("owned_product") or {}).get("name")
        owned_socket = infer_socket_from_cpu_name(owned_cpu_name) if owned_cpu_name else None
        if owned_socket:
            filtered.append(_build_motherboard_item_for_owned_cpu(owned_socket, owned_cpu_name, color_suffix=_color_sfx))

    gpu_item = next((t for t in filtered if t["part"] == "GPU"), None)
    if gpu_item is not None:
        cpu_item = next((t for t in filtered if t["part"] == "CPU"), None)
        filtered.append(_build_psu_item(scores.get("psu", {}), gpu_item, cpu_item, color_suffix=_color_sfx))
    else:
        # KAN-195: GPU '보유' → 보유 예정 GPU의 tier 기준 PSU 호환성 체크
        gpu_state = parts_config.get("GPU", {})
        if gpu_state.get("option") == "owned":
            owned_gpu = gpu_state.get("owned_product") or {}
            owned_gpu_tier = calculate_gpu_tier(owned_gpu.get("score"))
            if owned_gpu_tier is not None:
                cpu_item = next((t for t in filtered if t["part"] == "CPU"), None)
                owned_gpu_item = {"part": "GPU", "target_tier": owned_gpu_tier}
                psu_item = _build_psu_item(scores.get("psu", {}), owned_gpu_item, cpu_item, color_suffix=_color_sfx)
                psu_item["reason"] = (
                    f"보유 예정인 {owned_gpu.get('name', '')} 기준 PSU 용량 호환성을 확인합니다."
                )
                filtered.append(psu_item)

    resolved = resolve_prices(filtered, color_suffix=_color_sfx)

    resolved.sort(key=lambda x: x.get("priority", 0.0), reverse=True)
    return resolved
