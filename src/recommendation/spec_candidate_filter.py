"""
추천 대상 부품별로 PassMark 후보를 필터링하거나 가격 검색 쿼리를 생성한다.

CPU/GPU : PassMark 벤치마크 목록에서 목표 tier 범위 + 예산 조건으로 후보 최대 5개 선정.
RAM/SSD/HDD : PassMark tier 없음 → 빈 candidates + search_query 생성 (KAN-140에서 채움).
"""

from src.pricing.passmark_tiering import (
    load_cpu_passmark_items,
    load_gpu_passmark_items,
    calculate_cpu_tier,
    calculate_gpu_tier,
    parse_price_usd,
    MAX_TIER,
)

_TIER_BELOW    = 1   # target_tier - 1 이상
_TIER_ABOVE    = 2   # target_tier + 2 이하
_MAX_CANDS     = 5   # 부품당 최대 후보 수


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
) -> list[dict]:
    tier_min = max(1, target_tier - _TIER_BELOW)
    tier_max = min(MAX_TIER, target_tier + _TIER_ABOVE)

    candidates = []
    for item in items:
        tier = calc_tier_fn(item.get("score"))
        if tier is None or not (tier_min <= tier <= tier_max):
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

    # target_tier에 가까운 순 → 같은 tier면 score 높은 순
    candidates.sort(key=lambda x: (
        abs(x["performance_tier"] - target_tier),
        -(x["passmark_score"] or 0),
    ))
    return candidates[:_MAX_CANDS]


# ── RAM / SSD / HDD 검색 쿼리 생성 ───────────────────────────────────

def _gb_str(gb: int) -> str:
    return f"{gb // 1024}TB" if gb >= 1024 else f"{gb}GB"


def _ram_query(spec: dict) -> str:
    return f"RAM {_gb_str(spec.get('target_gb', 16))}"


def _ssd_query(spec: dict) -> str:
    return f"NVMe SSD {_gb_str(spec.get('target_gb', 1024))}"


def _hdd_query(spec: dict) -> str:
    # HDD 교체 목적이므로 SSD 검색
    return f"SSD {_gb_str(spec.get('target_gb', 1024))}"


_QUERY_BUILDERS = {
    "RAM": _ram_query,
    "SSD": _ssd_query,
    "HDD": _hdd_query,
}


# ── 진입점 ────────────────────────────────────────────────────────────

def filter_spec_candidates(
    enriched_targets: list[dict],
    user_preferences: dict | None,
) -> list[dict]:
    """
    각 추천 대상에 candidates 목록과 search_query를 추가해 반환한다.

    enriched_targets : calculate_target_tiers() 결과
    user_preferences : user_preferences.json (budget 필터용)
    """
    budget: int | None = (user_preferences or {}).get("budget")

    # 예산이 있을 때만 환율 조회 (루프 밖 1회)
    exchange_rate: float | None = None
    if budget is not None:
        try:
            from src.pricing.exchange_rate import get_usd_to_krw_rate
            exchange_rate = get_usd_to_krw_rate()
        except Exception:
            pass

    # PassMark 데이터는 CPU/GPU 각각 최초 1회만 로드
    _cpu_items: list[dict] | None = None
    _gpu_items: list[dict] | None = None

    result = []
    for target in enriched_targets:
        part         = target["part"]
        target_tier  = target.get("target_tier")
        target_spec  = target.get("target_spec")

        if part == "CPU" and target_tier is not None:
            if _cpu_items is None:
                try:
                    _cpu_items = load_cpu_passmark_items()
                except Exception:
                    _cpu_items = []
            cands = _filter_passmark(_cpu_items, calculate_cpu_tier, target_tier, budget, exchange_rate)
            query = cands[0]["name"] if cands else "CPU"
            result.append({**target, "candidates": cands, "search_query": query})

        elif part == "GPU" and target_tier is not None:
            if _gpu_items is None:
                try:
                    _gpu_items = load_gpu_passmark_items()
                except Exception:
                    _gpu_items = []
            cands = _filter_passmark(_gpu_items, calculate_gpu_tier, target_tier, budget, exchange_rate)
            query = cands[0]["name"] if cands else "GPU"
            result.append({**target, "candidates": cands, "search_query": query})

        elif part in _QUERY_BUILDERS and target_spec:
            query = _QUERY_BUILDERS[part](target_spec)
            result.append({**target, "candidates": [], "search_query": query})

        else:
            result.append({**target, "candidates": [], "search_query": part})

    return result
