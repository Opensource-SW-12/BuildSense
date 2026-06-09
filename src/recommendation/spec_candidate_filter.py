"""
추천 대상 부품별로 PassMark 후보를 필터링하거나 가격 검색 쿼리를 생성한다.

CPU/GPU : PassMark 벤치마크 목록에서 목표 tier 범위 + 예산 조건으로 후보 최대 5개 선정.
RAM/SSD/HDD : PassMark tier 없음 → 빈 candidates + search_query 생성 (KAN-140에서 채움).
Motherboard : upgrade_motherboard=True 일 때 board_specs.json에서 소켓 호환 보드 선정.
"""
import json
import re

from src.pricing.passmark_tiering import (
    load_cpu_passmark_items,
    load_gpu_passmark_items,
    calculate_cpu_tier,
    calculate_gpu_tier,
    parse_price_usd,
    MAX_TIER,
)
from src.platform_mapper import (
    cpu_patterns_for_socket,
    infer_socket_from_cpu_name,
    socket_to_pcie_gen,
    socket_to_ram_type,
)

_TIER_BELOW    = 1   # target_tier - 1 이상
_TIER_ABOVE    = 2   # target_tier + 2 이하
_MAX_CANDS     = 5   # 부품당 최대 후보 수

# ── 워크스테이션/전문가용 GPU 런타임 필터 ─────────────────────────────────
# PassMark DB에 포함될 수 있는 비소비자용 GPU를 추천 후보에서 제외한다.
_GPU_WORKSTATION_RE = re.compile(
    r"^RTX A\d"            # RTX A2000/A4000/A5000/A6000 워크스테이션
    r"|^Quadro "           # Quadro 시리즈
    r"|^RTX PRO "          # RTX PRO 워크스테이션 (신형)
    r"|Embedded GPU"       # 임베디드 변형
    r"|Embedded"           # 임베디드 (catch-all)
    r"|^Radeon PRO "       # AMD 워크스테이션 (대문자)
    r"|^Radeon Pro "       # AMD 워크스테이션 (소문자)
    r"|^Radeon AI PRO"     # AMD AI 가속기/워크스테이션
    r"|^Intel Arc Pro"     # Intel 워크스테이션
    r"|^T\d{3}"            # T400/T600/T1000/T2000 Quadro T 계열
    r"|Generation Embedded"
    r"|^RTX \d+ Ada"       # RTX xxxx Ada Generation 워크스테이션 전체
    r"|^A\d{4} "           # A4500, A5500 등 워크스테이션
    r"|^NVIDIA RTX A"      # 전체 NVIDIA RTX A 계열
    r"| SFF Edition"       # SFF 워크스테이션 에디션
    r"|Workstation Edition"  # 워크스테이션 에디션 명시
)


def _is_workstation_gpu(name: str) -> bool:
    return bool(_GPU_WORKSTATION_RE.search(name))


# ── 모바일 SoC / 노트북 CPU 런타임 필터 ─────────────────────────────────
# ARM SoC 및 모바일 서픽스(HX/H/HS/HQ/U/V 등)를 가진 노트북 CPU를 제외한다.
# 이 CPU들은 standalone으로 판매되지 않으므로 검색 시 노트북 제품이 반환된다.
_CPU_MOBILE_SOC_RE = re.compile(
    r"^Snapdragon"    # Qualcomm Snapdragon (ARM SoC)
    r"|^Qualcomm"     # Qualcomm 브랜드 전체
    r"|^Apple M\d"    # Apple Silicon
    r"|^MediaTek"     # MediaTek (ARM SoC)
    r"|^Dimensity"    # MediaTek Dimensity
    r"|^Exynos"       # Samsung Exynos
    r"|^Kirin"        # Huawei Kirin
    r"|^Helio"        # MediaTek Helio
    r"|^Unisoc"       # Unisoc (ARM SoC)
    r"|\bSoC\b"       # 이름에 SoC가 명시된 경우
    # ── 노트북/모바일 CPU 서픽스 ──────────────────────────────────────
    r"|\bLaptop\b"    # "Laptop CPU" 명시
    r"|\d+HX3D\b"     # AMD HX3D 모바일 (7945HX3D 등)
    r"|\d+HX\b"       # HX 모바일 서픽스
    r"| HX\b"         # 독립형 HX (Ryzen AI 9 HX 470 등)
    r"|\d+HS\b"       # HS 모바일 서픽스
    r"|\d+HQ\b"       # HQ 모바일 서픽스
    r"|\d+HK\b"       # HK 모바일 서픽스 (Intel)
    r"|\d+H\b"        # H 모바일 서픽스 (13900H 등)
    r"|\d+U\b"        # U 초저전력 서픽스
    r"|\d+V\b"        # V 서픽스 (Intel Lunar Lake Core Ultra 200V)
    r"|Ryzen AI Max"  # AMD 모바일 AI APU (Ryzen AI Max+ 395 등, 대소문자 무시)
    r"|Ryzen AI [0-9]"  # AMD Ryzen AI 모바일 시리즈
    , re.IGNORECASE   # 대소문자 무시 (RYZEN AI MAX+ 392 등 대문자 변형 대응)
)


def _is_mobile_soc(name: str) -> bool:
    return bool(_CPU_MOBILE_SOC_RE.search(name))


def _infer_cpu_manufacturer(cpu_name: str) -> str:
    """CPU 이름에서 제조사를 추론한다. 소켓 감지 실패 시 호환성 폴백에 사용.
    반환값: 'amd' | 'intel' | '' (미확인)
    """
    n = (cpu_name or "").lower()
    if re.search(r"\b(amd|ryzen|athlon|threadripper)\b", n):
        return "amd"
    if re.search(r"\b(intel|celeron|pentium|xeon)\b", n) or "core i" in n or "core ultra" in n:
        return "intel"
    return ""

# 메인보드 칩셋 등급 분류 (0=프리미엄, 2=메인스트림, 4=보급)
# board_specs.json의 칩셋 값은 "AMD X870E" / "Intel Z790" 형식이므로
# _chipset_rank()에서 제조사 접두사를 제거 후 조회한다.
_CHIPSET_RANK: dict[str, int] = {
    # ── AM5 ──────────────────────────────────────────────────────
    "X870E": 0, "X670E": 0,          # flagship
    "X870":  1, "X670":  1,          # high-end
    "B850":  2, "B650E": 2,          # mid-high
    "B840":  3, "B650":  3,          # mid
    "A620":  4,                       # budget
    # ── AM4 ──────────────────────────────────────────────────────
    "X570":  0, "X470":  0, "X370": 0,  # flagship
    "B550":  2, "B450":  2,             # mid
    "B350":  3,                          # mid-budget
    "A520":  4, "A320":  4,             # budget
    # ── LGA 1851 ─────────────────────────────────────────────────
    "Z890":  0,
    "B860":  2,
    "H810":  4,
    # ── LGA 1700 ─────────────────────────────────────────────────
    "Z790":  0, "Z690":  0,
    "B760":  2, "B660":  2, "H770": 2, "H670": 2,
    "H610":  4, "Q670":  4,
    # ── LGA 1200 ─────────────────────────────────────────────────
    "Z590":  0, "Z490":  0,
    "B560":  2, "B460":  2, "H570": 2,
    "H510":  4, "H470":  4, "H410": 4,
}


def _chipset_rank(chipset: str) -> int:
    """칩셋 이름에서 제조사 접두사(AMD / Intel)를 제거한 뒤 등급을 반환한다."""
    short = chipset.split(" ", 1)[-1] if " " in chipset else chipset
    return _CHIPSET_RANK.get(short, 99)


# ── 공통 유틸 ─────────────────────────────────────────────────────────

def _krw_from_usd(price_usd, exchange_rate: float | None) -> int | None:
    if price_usd == "NA" or exchange_rate is None:
        return None
    try:
        return int(float(price_usd) * exchange_rate)
    except (TypeError, ValueError):
        return None


def _within_budget(price_krw: int | None, budget: int | None) -> bool:
    """예산이 설정되어 있고 가격을 알 수 있을 때만 필터링한다. 가격 미상은 통과."""
    if budget is None or price_krw is None:
        return True
    return price_krw <= budget


# ── CPU / GPU PassMark 후보 필터링 ────────────────────────────────────

def _filter_passmark(
    items: list[dict],
    calc_tier_fn,
    target_tier: int,
    budget: int | None,
    exchange_rate: float | None,
    min_score: int | None = None,
    exclude_fn=None,
    max_results: int = _MAX_CANDS,
) -> list[dict]:
    """
    target_tier 근방의 후보를 반환한다.
    조건을 모두 충족하는 후보가 없으면 target_tier를 1씩 낮춰 재시도한다.
    """
    current_target = target_tier
    while current_target >= 1:
        tier_min = max(1, current_target - _TIER_BELOW)
        tier_max = min(MAX_TIER, current_target + _TIER_ABOVE)

        candidates = []
        for item in items:
            tier = calc_tier_fn(item.get("score"))
            if tier is None or not (tier_min <= tier <= tier_max):
                continue

            # 현재 하드웨어보다 낮은 점수의 후보 제외 (다운그레이드 방지)
            if min_score is not None and (item.get("score") or 0) <= min_score:
                continue

            # 워크스테이션/전문가용 부품 제외
            if exclude_fn is not None and exclude_fn(item.get("name", "")):
                continue

            price_usd = parse_price_usd(item.get("price_usd", "NA"))
            price_krw = _krw_from_usd(price_usd, exchange_rate)

            if not _within_budget(price_krw, budget):
                continue

            candidates.append({
                "name":             item.get("name"),
                "passmark_score":   item.get("score"),
                "performance_tier": tier,
                "price_usd":        price_usd,
                "price_krw":        price_krw,
            })

        candidates.sort(key=lambda x: (
            abs(x["performance_tier"] - current_target),
            -(x["passmark_score"] or 0),
        ))
        result = candidates[:max_results]
        if result:
            return result

        current_target -= 1

    return []


def _diversify_cpu_candidates(candidates: list[dict], target_tier: int) -> list[dict]:
    """
    Intel/AMD 후보를 번갈아 배치해 제조사 다양성을 보장한다.
    AMD를 먼저 배치해 게임용 사용자가 Ryzen 옵션을 볼 수 있도록 한다.
    """
    def _is_amd(name: str) -> bool:
        n = (name or "").lower()
        return "ryzen" in n or "amd " in n or "threadripper" in n or "athlon" in n

    def _is_intel(name: str) -> bool:
        n = (name or "").lower()
        return "intel" in n or "core i" in n or "core ultra" in n

    def _sort_key(x):
        return (abs(x["performance_tier"] - target_tier), -(x["passmark_score"] or 0))

    amd_pool   = sorted([c for c in candidates if _is_amd(c.get("name", ""))],   key=_sort_key)
    intel_pool = sorted([c for c in candidates if _is_intel(c.get("name", ""))], key=_sort_key)
    other_pool = sorted(
        [c for c in candidates if not _is_amd(c.get("name", "")) and not _is_intel(c.get("name", ""))],
        key=_sort_key,
    )

    result: list[dict] = []
    while amd_pool or intel_pool or other_pool:
        if amd_pool:
            result.append(amd_pool.pop(0))
        if intel_pool:
            result.append(intel_pool.pop(0))
        if other_pool:
            result.append(other_pool.pop(0))

    return result[:_MAX_CANDS]


# ── RAM / SSD / HDD 검색 쿼리 생성 ───────────────────────────────────

def _gb_str(gb: int) -> str:
    return f"{gb // 1024}TB" if gb >= 1024 else f"{gb}GB"


def _color_suffix(color_pref: str) -> str:
    return {"black": " 블랙", "white": " 화이트"}.get(color_pref, "")


def _ram_query(spec: dict, socket: str | None = None, color_pref: str = "none") -> str:
    cap = _gb_str(spec.get("target_gb", 16))
    ddr = socket_to_ram_type(socket)
    sfx = _color_suffix(color_pref)
    if ddr:
        return f"{ddr} RAM {cap}{sfx}"
    return f"RAM {cap}{sfx}"


def _ssd_query(spec: dict, socket: str | None = None) -> str:
    cap = _gb_str(spec.get("target_gb", 1024))
    gen = socket_to_pcie_gen(socket)
    if gen:
        return f"PCIe {gen}.0 NVMe SSD {cap}"
    return f"NVMe SSD {cap}"


def _hdd_query(spec: dict, socket: str | None = None) -> str:
    # HDD 교체 목적이므로 SSD 검색
    cap = _gb_str(spec.get("target_gb", 1024))
    return f"SSD {cap}"


# ── 메인보드 후보 선정 ────────────────────────────────────────────────

def _load_board_specs() -> list[dict]:
    try:
        from src.config import SPECS_DIR
        path = SPECS_DIR / "board_specs.json"
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _get_board_candidates(socket: str) -> list[dict]:
    """소켓 호환 메인보드를 칩셋 등급별로 최대 3개(상위/중간/보급) 반환한다."""
    boards = [b for b in _load_board_specs() if b.get("socket") == socket]
    if not boards:
        return []

    # 칩셋 등급 오름차순(0=프리미엄), 이름 알파벳순으로 정렬
    boards.sort(key=lambda b: (_chipset_rank(b.get("chipset", "")), b.get("name", "")))

    # 등급별 1개씩 최대 3개 선정
    seen_ranks: set[int] = set()
    result = []
    for b in boards:
        rank = _chipset_rank(b.get("chipset", ""))
        if rank not in seen_ranks:
            seen_ranks.add(rank)
            result.append({
                "name":             b.get("name"),
                "chipset":          b.get("chipset"),
                "socket":           b.get("socket"),
                "form_factor":      b.get("form_factor"),
                "m2_interfaces":    b.get("m2_interfaces", []),
                "sata_ports":       b.get("sata_ports", 0),
                "passmark_score":   None,
                "performance_tier": None,
                "price_usd":        None,
                "price_krw":        None,
                "price_source":     None,
                "product_url":      None,
                "mall_name":        None,
            })
        if len(result) >= 3:
            break

    return result


# ── 진입점 ────────────────────────────────────────────────────────────

def filter_spec_candidates(
    enriched_targets: list[dict],
    user_preferences: dict | None,
    socket: str | None = None,
    upgrade_motherboard: bool | None = None,
    current_cpu: str | None = None,
) -> list[dict]:
    """
    각 추천 대상에 candidates 목록과 search_query를 추가해 반환한다.

    enriched_targets    : calculate_target_tiers() 결과
    user_preferences    : user_preferences.json (budget 필터용)
    socket              : hw_info["CPU_socket"] — 소켓 인식 쿼리·필터링에 사용
    upgrade_motherboard : user_profile parts 설정에서 전달; None 이면 user_preferences 폴백
    current_cpu         : hw_info["CPU"] — 소켓 감지 실패 시 제조사 기반 호환성 폴백에 사용
    """
    prefs        = user_preferences or {}
    budget_mode  = prefs.get("budget_mode", "recommended")
    part_budgets: dict[str, int | None] = prefs.get("budgets", {}) if budget_mode == "custom" else {}
    color_pref   = prefs.get("color_preference", "none")
    if upgrade_motherboard is None:
        upgrade_motherboard = prefs.get("upgrade_motherboard", False)

    # custom 모드에서 예산이 하나라도 있을 때만 환율 조회 (루프 밖 1회)
    exchange_rate: float | None = None
    if budget_mode == "custom" and any(v for v in part_budgets.values()):
        try:
            from src.pricing.exchange_rate import get_usd_to_krw_rate
            exchange_rate = get_usd_to_krw_rate()
        except Exception:
            pass

    # PassMark 데이터는 CPU/GPU 각각 최초 1회만 로드
    _cpu_items: list[dict] | None = None
    _gpu_items: list[dict] | None = None

    # upgrade_motherboard=True 인 경우, CPU 후보를 미리 계산해 새 소켓을 파악한다.
    # (RAM/SSD 쿼리에 새 플랫폼의 DDR/PCIe gen 반영)
    effective_socket = socket
    if upgrade_motherboard:
        for t in enriched_targets:
            if t["part"] == "CPU" and t.get("target_tier") is not None:
                try:
                    if _cpu_items is None:
                        _cpu_items = load_cpu_passmark_items()
                    pre_cands = _filter_passmark(
                        _cpu_items, calculate_cpu_tier,
                        t["target_tier"], part_budgets.get("CPU"), exchange_rate,
                        min_score=t.get("current_score"),
                        exclude_fn=_is_mobile_soc,
                        max_results=30,
                    )
                    pre_cands = _diversify_cpu_candidates(pre_cands, t["target_tier"])
                    if pre_cands:
                        inferred = infer_socket_from_cpu_name(pre_cands[0]["name"])
                        if inferred:
                            effective_socket = inferred
                except Exception:
                    pass
                break

    result = []
    for target in enriched_targets:
        part         = target["part"]
        target_tier  = target.get("target_tier")
        target_spec  = target.get("target_spec")

        if part == "CPU":
            if target_tier is not None:
                if _cpu_items is None:
                    try:
                        _cpu_items = load_cpu_passmark_items()
                    except Exception:
                        _cpu_items = []

                # CPU 다양성 보장을 위해 더 넓은 후보 풀을 모은 뒤 인터리브
                cands_pool = _filter_passmark(
                    _cpu_items, calculate_cpu_tier, target_tier,
                    part_budgets.get("CPU"), exchange_rate,
                    min_score=target.get("current_score"),
                    exclude_fn=_is_mobile_soc,
                    max_results=30,
                )

                # ── CPU 호환성 필터 ───────────────────────────────────────
                if not upgrade_motherboard:
                    # keep 모드: 소켓 호환 CPU만 남김
                    if socket:
                        _sock_patterns = cpu_patterns_for_socket(socket)
                        if _sock_patterns:
                            cands_pool = [c for c in cands_pool
                                          if any(p.search(c.get("name", "")) for p in _sock_patterns)]

                            # 소켓 필터 후 빈 결과 → 플랫폼 최고 tier로 폴백
                            # (예: AM4 사용자의 target_tier=20이 AM4 최대 tier=16을 초과)
                            if not cands_pool and _cpu_items:
                                _plat_max = max(
                                    (calculate_cpu_tier(i.get("score"))
                                     for i in _cpu_items
                                     if not _is_mobile_soc(i.get("name", ""))
                                     and any(p.search(i.get("name", "")) for p in _sock_patterns)
                                     and calculate_cpu_tier(i.get("score")) is not None),
                                    default=None,
                                )
                                if _plat_max:
                                    _fb = _filter_passmark(
                                        _cpu_items, calculate_cpu_tier, _plat_max,
                                        part_budgets.get("CPU"), exchange_rate,
                                        min_score=None,
                                        exclude_fn=_is_mobile_soc,
                                        max_results=30,
                                    )
                                    cands_pool = [c for c in _fb
                                                  if any(p.search(c.get("name", "")) for p in _sock_patterns)]

                    elif current_cpu:
                        # 소켓 미감지 폴백: 현재 CPU와 같은 제조사만 추천
                        # (예: AMD B450 보드 사용자에게 Intel LGA1851 CPU 추천 방지)
                        mfr = _infer_cpu_manufacturer(current_cpu)
                        if mfr:
                            cands_pool = [c for c in cands_pool
                                          if _infer_cpu_manufacturer(c.get("name", "")) == mfr]
                elif upgrade_motherboard and effective_socket:
                    # recommend 모드: effective_socket 기준 플랫폼으로 CPU 통일
                    # (Intel CPU + AMD 메인보드처럼 소켓 혼재 방지)
                    _tgt_patterns = cpu_patterns_for_socket(effective_socket)
                    if _tgt_patterns:
                        cands_pool = [c for c in cands_pool
                                      if any(p.search(c.get("name", "")) for p in _tgt_patterns)]

                cands = _diversify_cpu_candidates(cands_pool, target_tier)
                query = cands[0]["name"] if cands else "CPU"
                result.append({**target, "candidates": cands, "search_query": query})
            else:
                # PassMark 조회 실패 등으로 목표 tier를 계산하지 못한 경우에도
                # CPU 추천 카드 자체는 유지한다 (후보·검색어만 비워둠)
                result.append({**target, "candidates": [], "search_query": "CPU"})

            # recommend 모드: 새 소켓 호환 메인보드 항목 추가
            # (CPU 목표 tier 계산 성공 여부와 무관하게, 소켓 정보만 있으면 추가한다 —
            #  PassMark 조회가 실패해도 메인보드 추천이 누락되지 않도록 함)
            if upgrade_motherboard:
                target_socket = effective_socket or socket
                if target_socket:
                    board_cands = _get_board_candidates(target_socket)
                    result.append({
                        "part":         "Motherboard",
                        "score":        0.0,
                        "grade":        "medium",
                        "priority":     round(target.get("priority", 0.5) - 0.05, 4),
                        "reason":       (
                            f"CPU 업그레이드 시 {target_socket} 소켓 호환 메인보드가 필요합니다."
                        ),
                        "current_tier": None,
                        "target_tier":  None,
                        "target_spec": {
                            "socket": target_socket,
                            "note":   f"{target_socket} 소켓 호환 메인보드",
                        },
                        "candidates":   board_cands,
                        "search_query": f"메인보드 {target_socket}{_color_suffix(color_pref)}",
                    })

        elif part == "GPU" and target_tier is not None:
            if _gpu_items is None:
                try:
                    _gpu_items = load_gpu_passmark_items()
                except Exception:
                    _gpu_items = []
            cands = _filter_passmark(
                _gpu_items, calculate_gpu_tier, target_tier,
                part_budgets.get("GPU"), exchange_rate,
                min_score=target.get("current_score"),
                exclude_fn=_is_workstation_gpu,
            )
            query = cands[0]["name"] if cands else "GPU"
            result.append({**target, "candidates": cands, "search_query": query})

        elif part == "RAM" and target_spec:
            query = _ram_query(target_spec, effective_socket, color_pref)
            result.append({**target, "candidates": [], "search_query": query})

        elif part == "SSD" and target_spec:
            query = _ssd_query(target_spec, effective_socket)
            result.append({**target, "candidates": [], "search_query": query})

        elif part == "HDD" and target_spec:
            query = _hdd_query(target_spec, effective_socket)
            result.append({**target, "candidates": [], "search_query": query})

        else:
            result.append({**target, "candidates": [], "search_query": part})

    return result
