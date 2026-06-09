"""
추천 대상 부품별 목표 tier / 목표 스펙을 계산한다.

CPU·GPU : PassMark tier(1-29) 기반으로 현재 tier에서 점프 폭만큼 올림.
RAM     : 현재 용량의 2배 또는 다음 표준 용량으로 목표 설정.
SSD     : NVMe 업그레이드 + 다음 표준 용량 목표.
HDD     : SSD 교체 권장 + 다음 표준 용량 목표.
"""
import re

from src.pricing.passmark_tiering import MAX_TIER

# 등급별 tier 점프 폭 (29단계 기준)
# high +6 ≈ 한 세대 이상 점프 (예: tier 12→18, mid → high-end)
# medium +3 ≈ 체감 가능한 업그레이드
_TIER_JUMP: dict[str, int] = {
    "high":    6,
    "medium":  3,
    "unknown": 0,
}

# tier 매칭 실패(None) 시 등급별 고정 목표 tier
_FALLBACK_TARGET_TIER: dict[str, int] = {
    "high":    22,
    "medium":  17,
    "unknown": 18,
}

# 표준 RAM 용량 단계 (GB)
_RAM_STEPS = [8, 16, 24, 32, 48, 64, 128]

# 표준 SSD/HDD 용량 단계 (GB)
_STORAGE_STEPS = [256, 512, 1024, 2048, 4096]


# ── RAM 파싱 ──────────────────────────────────────────────────────────

def _parse_ram_gb(hw_ram: str) -> int | None:
    m = re.search(r'(\d+)\s*gb', (hw_ram or "").lower())
    return int(m.group(1)) if m else None


def _next_step(current: int, steps: list[int], min_mult: float) -> int:
    """current * min_mult 이상인 첫 번째 표준 용량을 반환한다."""
    target = current * min_mult
    for s in steps:
        if s >= target:
            return s
    return steps[-1]


# ── CPU / GPU 계산 ────────────────────────────────────────────────────

def _calc_cpu_gpu_tier(current_tier: int | None, grade: str, current_score: int | None = None) -> dict:
    jump = _TIER_JUMP.get(grade, 0)

    if current_tier is not None:
        target = min(current_tier + jump, MAX_TIER)
        return {
            "current_tier":  current_tier,
            "current_score": current_score,
            "target_tier":   target,
            "target_spec":   None,
        }

    # tier 매칭 실패 → 고정 목표
    return {
        "current_tier":  None,
        "current_score": current_score,
        "target_tier":   _FALLBACK_TARGET_TIER.get(grade, 15),
        "target_spec":   None,
    }


# ── RAM 계산 ─────────────────────────────────────────────────────────

def _calc_ram(grade: str, hw_info: dict) -> dict:
    current_gb = _parse_ram_gb(hw_info.get("RAM", ""))
    mult = 2.0 if grade == "high" else 1.5
    target_gb = _next_step(current_gb, _RAM_STEPS, mult) if current_gb else _RAM_STEPS[3]  # 32 GB 기본

    return {
        "current_tier": None,
        "target_tier":  None,
        "target_spec": {
            "current_gb": current_gb,
            "target_gb":  target_gb,
            "note":        f"현재 {current_gb} GB → {target_gb} GB 권장" if current_gb else f"{target_gb} GB 권장",
        },
    }


# ── SSD 계산 ─────────────────────────────────────────────────────────

def _calc_ssd(grade: str, hw_info: dict) -> dict:
    ssd_str = hw_info.get("SSD") or ""
    # SSD 이름에서 용량 추출 (예: "Samsung 970 EVO 1TB", "500GB SSD")
    m = re.search(r'(\d+)\s*(tb|gb)', ssd_str.lower())
    current_gb: int | None = None
    if m:
        val, unit = int(m.group(1)), m.group(2)
        current_gb = val * 1024 if unit == "tb" else val

    mult = 2.0 if grade == "high" else 1.5
    target_gb = _next_step(current_gb, _STORAGE_STEPS, mult) if current_gb else _STORAGE_STEPS[2]  # 1TB 기본

    return {
        "current_tier": None,
        "target_tier":  None,
        "target_spec": {
            "current_gb":   current_gb,
            "target_gb":    target_gb,
            "storage_type": "NVMe",
            "note":          f"NVMe {target_gb // 1024}TB 또는 {target_gb}GB 권장",
        },
    }


# ── HDD 계산 ─────────────────────────────────────────────────────────

def _calc_hdd(grade: str, hw_info: dict) -> dict:
    hdd_str = hw_info.get("HDD") or ""
    m = re.search(r'(\d+)\s*(tb|gb)', hdd_str.lower())
    current_gb: int | None = None
    if m:
        val, unit = int(m.group(1)), m.group(2)
        current_gb = val * 1024 if unit == "tb" else val

    target_gb = _next_step(current_gb, _STORAGE_STEPS, 1.0) if current_gb else _STORAGE_STEPS[2]

    return {
        "current_tier": None,
        "target_tier":  None,
        "target_spec": {
            "current_gb":   current_gb,
            "target_gb":    target_gb,
            "storage_type": "SSD",
            "note":          f"HDD → SSD {target_gb // 1024}TB 교체 권장 (체감 성능 대폭 향상)",
        },
    }


# ── 진입점 ────────────────────────────────────────────────────────────

def calculate_target_tiers(
    targets: list[dict],
    hw_tiers: dict,
    hw_info: dict,
) -> list[dict]:
    """
    각 추천 대상 부품에 목표 tier / 목표 스펙을 추가해 반환한다.

    targets  : select_upgrade_targets() 결과
    hw_tiers : map_hardware_to_tiers() 결과  {"cpu": {...}|None, "gpu": {...}|None}
    hw_info  : get_hardware_info() 결과 (RAM·SSD·HDD 용량 파싱용)
    """
    enriched = []

    for target in targets:
        part  = target["part"]
        grade = target["grade"]

        if part == "CPU":
            cpu_match = hw_tiers.get("cpu") or {}
            tier_data = _calc_cpu_gpu_tier(cpu_match.get("tier"), grade, cpu_match.get("passmark_score"))

        elif part == "GPU":
            gpu_match = hw_tiers.get("gpu") or {}
            tier_data = _calc_cpu_gpu_tier(gpu_match.get("tier"), grade, gpu_match.get("passmark_score"))

        elif part == "RAM":
            tier_data = _calc_ram(grade, hw_info)

        elif part == "SSD":
            tier_data = _calc_ssd(grade, hw_info)

        elif part == "HDD":
            tier_data = _calc_hdd(grade, hw_info)

        else:
            tier_data = {"current_tier": None, "target_tier": None, "target_spec": None}

        enriched.append({**target, **tier_data})

    return enriched
