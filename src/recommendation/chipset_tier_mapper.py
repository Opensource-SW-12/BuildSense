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


def _clean_hw_name(name: str) -> str:
    """Win32_Processor/nvidia-smi 이름에서 OEM 수식어·클록 정보를 제거한다."""
    name = name.lower()
    name = re.sub(r'\([^)]*\)', ' ', name)           # (R), (TM) 등 괄호 제거
    name = re.sub(r'cpu\s*@.*', '', name)             # "CPU @ 3.20GHz" 제거
    name = re.sub(r'\d+(\.\d+)?\s*ghz', '', name)    # 클록 속도 제거
    name = re.sub(r'[^a-z0-9]+', ' ', name)          # 특수문자 → 공백
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
