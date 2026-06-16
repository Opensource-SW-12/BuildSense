"""현재 장착된 CPU/GPU를 PassMark 벤치마크 목록과 매칭해 performance_tier를 반환한다."""
import re

from src.pricing.passmark_tiering import (
    load_cpu_passmark_items,
    load_gpu_passmark_items,
    calculate_cpu_tier,
    calculate_gpu_tier,
    normalize_text,
)

_MIN_TOKEN_OVERLAP = 0.7   # 매칭 인정 최소 토큰 일치 비율
_HW_UNKNOWN = "확인할 수 없음"

_SEARCH_RELATIVE_THRESHOLD = 0.7  # 최고 점수 대비 이 비율 미만인 후보는 제외 (예: 4070 검색 시 4080 제외)
_SEARCH_MAX_RESULTS = 5            # 최대 후보 수
_CATEGORY_LOADERS = {
    "cpu": load_cpu_passmark_items,
    "gpu": load_gpu_passmark_items,
}


def _clean_hw_name(name: str) -> str:
    """Win32_Processor/nvidia-smi 이름에서 OEM 수식어·클록 정보를 제거한다."""
    name = name.lower()
    name = re.sub(r'\([^)]*\)', ' ', name)           # (R), (TM) 등 괄호 제거
    name = re.sub(r'cpu\s*@.*', '', name)             # "CPU @ 3.20GHz" 제거
    name = re.sub(r'\d+(\.\d+)?\s*ghz', '', name)    # 클록 속도 제거
    name = re.sub(r'[^a-z0-9]+', ' ', name)          # 특수문자 → 공백
    name = re.sub(r'(\d)(x3d)', r'\1 x3d', name)     # "9800x3d" → "9800 x3d"
    return re.sub(r'\s+', ' ', name).strip()


def _token_overlap(a: str, b: str) -> float:
    ta = {t for t in a.split() if len(t) > 1}
    tb = {t for t in b.split() if len(t) > 1}
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


def _find_best_passmark_match(hw_name: str, passmark_items: list[dict]) -> dict | None:
    cleaned = _clean_hw_name(hw_name)

    best_item, best_ratio = None, 0.0
    for item in passmark_items:
        pm_normalized = normalize_text(item.get("name", ""))
        ratio = _token_overlap(cleaned, pm_normalized)
        if ratio > best_ratio:
            best_ratio = ratio
            best_item = item

    return best_item if best_ratio >= _MIN_TOKEN_OVERLAP else None


def map_hardware_to_tiers(hw_info: dict) -> dict:
    """
    현재 하드웨어를 PassMark 목록에 매칭해 tier를 반환한다.

    hw_info: get_hardware_info() 반환값
    반환:
        {
            "cpu": {"matched_name": str, "tier": int(1-29), "passmark_score": int} | None,
            "gpu": {"matched_name": str, "tier": int(1-29), "passmark_score": int} | None,
        }
    """
    result: dict[str, dict | None] = {"cpu": None, "gpu": None}

    cpu_name = (hw_info.get("CPU") or "").strip()
    gpu_name = (hw_info.get("GPU") or "").strip()

    if cpu_name and cpu_name != _HW_UNKNOWN:
        try:
            cpu_items = load_cpu_passmark_items()
            match = _find_best_passmark_match(cpu_name, cpu_items)
            if match:
                score = match.get("score")
                tier = calculate_cpu_tier(score)
                if tier is not None:
                    result["cpu"] = {
                        "matched_name":  match.get("name"),
                        "tier":          tier,
                        "passmark_score": score,
                    }
        except Exception:
            pass

    if gpu_name and gpu_name != _HW_UNKNOWN:
        try:
            gpu_items = load_gpu_passmark_items()
            match = _find_best_passmark_match(gpu_name, gpu_items)
            if match:
                score = match.get("score")
                tier = calculate_gpu_tier(score)
                if tier is not None:
                    result["gpu"] = {
                        "matched_name":  match.get("name"),
                        "tier":          tier,
                        "passmark_score": score,
                    }
        except Exception:
            pass

    return result


def _numeric_tokens(cleaned: str) -> set[str]:
    """순수 숫자로만 이뤄진 토큰(예: 모델 번호 "4070")을 추출한다."""
    return {t for t in cleaned.split() if t.isdigit() and len(t) > 1}


def search_passmark_candidates(query: str, category: str) -> list[dict]:
    """
    사용자가 입력한 제품명과 이름이 가장 비슷한 PassMark 항목을 찾아 반환한다.
    "보유" 옵션(KAN-195)에서 사용자가 이미 구매한 CPU/GPU를 검색할 때 사용.

    query   : 사용자가 입력한 제품명
    category: "cpu" | "gpu"

    반환: PassMark 항목 목록 (최소 1개, 최대 _SEARCH_MAX_RESULTS개).
          1위 항목과 토큰 일치율이 너무 낮은 후보(예: 4070 검색 시 4080)는 제외한다.
          입력에 모델 번호(순수 숫자 토큰)가 있으면 해당 번호가 포함된 항목으로 우선
          제한해 "RTX A5000"처럼 시리즈만 같고 번호가 다른 항목이 섞이는 것을 막는다.
          입력이 비어 있으면 빈 목록을 반환한다.
    """
    query = (query or "").strip()
    if not query:
        return []

    loader = _CATEGORY_LOADERS.get(category)
    if loader is None:
        return []

    items = loader()
    cleaned = _clean_hw_name(query)

    candidates = items
    num_tokens = _numeric_tokens(cleaned)
    if num_tokens:
        with_matching_number = [
            item for item in items
            if num_tokens & set(normalize_text(item.get("name", "")).split())
        ]
        if with_matching_number:
            candidates = with_matching_number

    scored = [
        (_token_overlap(cleaned, normalize_text(item.get("name", ""))), item)
        for item in candidates
    ]
    scored.sort(key=lambda pair: pair[0], reverse=True)

    if not scored:
        return []

    best_ratio = scored[0][0]
    if best_ratio == 0.0:
        return [scored[0][1]]

    threshold = best_ratio * _SEARCH_RELATIVE_THRESHOLD
    results = []
    for ratio, item in scored:
        if ratio < threshold:
            break
        results.append(item)
        if len(results) >= _SEARCH_MAX_RESULTS:
            break

    return results
