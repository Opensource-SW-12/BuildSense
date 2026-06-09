"""
추천 대상 부품별로 네이버 쇼핑 API(1차) → eBay(폴백)를 통해 가격 정보를 조회하고,
결과를 파일 캐시(24h TTL)에 저장·재사용한다.

CPU/GPU : PassMark 후보 이름으로 검색 → product_matcher 검증 → 가격 주입
RAM     : 검색 쿼리로 검색 → 상위 결과를 candidates로 설정
SSD/HDD : 검색 쿼리로 검색 → product_matcher 검증 → candidates 설정
PSU/MB  : 검색 쿼리로 검색 → 상위 결과 반환
"""
import hashlib
import os
import re
import time

from src.config import PRICES_DIR
from src.pricing.price_fetcher import (
    search_naver_shopping, extract_naver_candidates,
    search_ebay, extract_ebay_candidates,
)
from src.pricing.price_candidate_storage import save_price_candidates, load_price_candidates
from src.pricing.product_matcher import is_matching_product

_MAX_ENRICH  = 3        # CPU/GPU 후보 중 가격을 조회할 최대 수
_MAX_CANDS   = 3        # RAM/SSD/HDD 최대 후보 수
_NAVER_FETCH = 10       # 네이버 API 1회 검색 결과 수
_CACHE_TTL   = 86_400   # 캐시 유효 시간 (24시간)

# ──────────────────────────────────────────────────────────────────────
# 캐시 헬퍼
# ──────────────────────────────────────────────────────────────────────

def _cache_path(part: str, query: str):
    key = hashlib.sha1(f"{part}:{query}".encode()).hexdigest()[:12]
    return PRICES_DIR / f"{part}_{key}.json"


def _cache_load(part: str, query: str) -> list[dict] | None:
    path = _cache_path(part, query)
    if not path.exists():
        return None
    if time.time() - path.stat().st_mtime > _CACHE_TTL:
        return None
    try:
        return load_price_candidates(str(path))
    except Exception:
        return None


def _cache_save(part: str, query: str, items: list[dict]) -> None:
    try:
        PRICES_DIR.mkdir(parents=True, exist_ok=True)
        save_price_candidates(items, str(_cache_path(part, query)))
    except Exception:
        pass


# ── part dict 빌더 ────────────────────────────────────────────────────

_CPU_BRAND_PREFIXES = ("Intel ", "AMD ", "Qualcomm ")

_GPU_BRAND_HINTS = {
    "geforce": "NVIDIA",
    "rtx":     "NVIDIA",
    "gtx":     "NVIDIA",
    "radeon":  "AMD",
}

_GPU_NAME_PREFIXES = (
    "NVIDIA GeForce ", "GeForce ",
    "AMD Radeon ",     "Radeon ",
    "Intel Arc ",
)


def _cpu_part_dict(name: str) -> dict:
    """PassMark CPU 이름으로 product_matcher용 part dict를 생성한다."""
    manufacturer = ""
    for prefix in _CPU_BRAND_PREFIXES:
        if name.startswith(prefix):
            manufacturer = prefix.strip()
            break
    return {
        "name":         name,
        "manufacturer": manufacturer,
        "category":     "cpu",
        "series":       None,
        "variant":      None,
    }


def _gpu_part_dict(name: str) -> dict:
    """PassMark GPU 이름으로 product_matcher용 part dict를 생성한다."""
    name_lower = name.lower()
    manufacturer = ""
    for hint, brand in _GPU_BRAND_HINTS.items():
        if hint in name_lower:
            manufacturer = brand
            break

    chipset = name
    for prefix in _GPU_NAME_PREFIXES:
        if chipset.startswith(prefix):
            chipset = chipset[len(prefix):]
            break

    return {
        "name":         name,
        "manufacturer": manufacturer,
        "category":     "gpu",
        "chipset":      chipset,
        "memory":       {},
    }


def _storage_part_dict(search_query: str) -> dict:
    """search_query 문자열로 product_matcher용 SSD part dict를 생성한다."""
    q = search_query.lower()

    capacity_gb = None
    m_tb = re.search(r'(\d+)\s*tb', q)
    m_gb = re.search(r'(\d+)\s*gb', q)
    if m_tb:
        capacity_gb = int(m_tb.group(1)) * 1000  # product_matcher: TB = ÷1000
    elif m_gb:
        capacity_gb = int(m_gb.group(1))

    storage_type = None
    if "nvme" in q:
        storage_type = "NVMe"
    elif "ssd" in q:
        storage_type = "SSD"

    return {
        "name":         search_query,
        "manufacturer": "",
        "category":     "ssd",
        "capacity_gb":  capacity_gb,
        "storage_type": storage_type,
    }


# ── 검색 헬퍼 ─────────────────────────────────────────────────────────

def _naver_search_safe(query: str) -> list[dict]:
    """네이버 검색 실패 시 빈 리스트 반환해 파이프라인 중단을 방지한다."""
    try:
        result = search_naver_shopping(query, display=_NAVER_FETCH)
        return extract_naver_candidates(result)
    except Exception:
        return []


def _ebay_search_safe(query: str) -> list[dict]:
    """eBay 검색 실패 시 빈 리스트 반환한다. 자격증명 미설정이면 즉시 반환."""
    if not (os.getenv("EBAY_CLIENT_ID") and os.getenv("EBAY_CLIENT_SECRET")):
        return []
    try:
        result = search_ebay(query, limit=_NAVER_FETCH)
        return extract_ebay_candidates(result)
    except Exception:
        return []


def _search_safe(query: str, part: str, ebay_fallback: bool = False) -> list[dict]:
    """캐시 우선 → 네이버 → (선택적) eBay 폴백 순서로 검색한다.
    결과가 있을 때만 캐시에 저장한다."""
    cached = _cache_load(part, query)
    if cached is not None:
        return cached

    items = _naver_search_safe(query)

    if not items and ebay_fallback:
        items = _ebay_search_safe(query)

    if items:
        _cache_save(part, query, items)
    return items


def _make_price_candidate(item: dict) -> dict:
    return {
        "name":             item.get("title"),
        "passmark_score":   None,
        "performance_tier": None,
        "price_usd":        None,
        "price_krw":        item.get("price_krw"),
        "price_source":     "naver",
        "product_url":      item.get("link"),
        "mall_name":        item.get("mall_name"),
    }


# ── 부품 유형별 처리 ──────────────────────────────────────────────────

def _enrich_hw_candidate(candidate: dict, part: str) -> dict:
    """
    PassMark CPU/GPU 후보 1개에 대해 네이버 → eBay 순으로 가격을 보완한다.
    이미 price_krw 값이 있으면 검색을 건너뛴다.
    """
    if candidate.get("price_krw") is not None:
        return candidate

    name = candidate.get("name", "")
    if not name:
        return candidate

    part_dict = _cpu_part_dict(name) if part == "CPU" else _gpu_part_dict(name)
    items = _search_safe(name, part, ebay_fallback=True)

    for item in items:
        if not is_matching_product(item.get("title", ""), part_dict):
            continue
        source = item.get("source", "naver")
        return {
            **candidate,
            "price_krw":    item.get("price_krw"),
            "price_source": source,
            "product_url":  item.get("link"),
            "mall_name":    item.get("mall_name") or ("eBay" if source == "ebay" else None),
        }

    return candidate


def _search_ram_candidates(search_query: str) -> list[dict]:
    """RAM은 스펙 검증 없이 상위 결과를 그대로 사용한다."""
    cands = []
    for item in _search_safe(search_query, "RAM"):
        if item.get("price_krw") is None:
            continue
        cands.append(_make_price_candidate(item))
        if len(cands) >= _MAX_CANDS:
            break
    return cands


def _search_storage_candidates(search_query: str, part: str = "SSD") -> list[dict]:
    """SSD/HDD는 product_matcher로 용량·타입을 검증한 결과만 사용한다."""
    part_dict = _storage_part_dict(search_query)
    cands = []
    for item in _search_safe(search_query, part):
        if not is_matching_product(item.get("title", ""), part_dict):
            continue
        if item.get("price_krw") is None:
            continue
        cands.append(_make_price_candidate(item))
        if len(cands) >= _MAX_CANDS:
            break
    return cands


def _enrich_board_candidate(candidate: dict) -> dict:
    """메인보드 후보에 캐시·네이버 검색으로 가격을 보완한다."""
    if candidate.get("price_krw") is not None:
        return candidate
    name = candidate.get("name", "")
    if not name:
        return candidate
    items = _search_safe(name, "Motherboard")
    if items:
        first = items[0]
        return {
            **candidate,
            "price_krw":    first.get("price_krw"),
            "price_source": first.get("source", "naver"),
            "product_url":  first.get("link"),
            "mall_name":    first.get("mall_name"),
        }
    return candidate


# ── 진입점 ────────────────────────────────────────────────────────────

def resolve_prices(filtered_targets: list[dict]) -> list[dict]:
    """
    각 추천 대상의 candidates에 실제 가격 정보를 채워 반환한다.

    filtered_targets : filter_spec_candidates() 결과
    반환:
        각 target에 가격이 보완된 candidates 목록이 포함된 새 list
    """
    result = []

    for target in filtered_targets:
        part         = target["part"]
        candidates   = list(target.get("candidates", []))
        search_query = target.get("search_query", part)

        if part in ("CPU", "GPU"):
            enriched = [_enrich_hw_candidate(c, part) for c in candidates[:_MAX_ENRICH]]
            result.append({**target, "candidates": enriched})

        elif part == "RAM":
            result.append({**target, "candidates": _search_ram_candidates(search_query)})

        elif part in ("SSD", "HDD"):
            result.append({**target, "candidates": _search_storage_candidates(search_query, part)})

        elif part == "Motherboard":
            enriched = [_enrich_board_candidate(c) for c in candidates[:_MAX_ENRICH]]
            result.append({**target, "candidates": enriched})

        elif part == "PSU" and search_query:
            psu_cands = [_make_price_candidate(i) for i in _search_safe(search_query, "PSU")]
            result.append({**target, "candidates": psu_cands})

        else:
            result.append(target)

    return result
