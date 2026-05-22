_GPU_NOT_DETECTED_THRESHOLD = 0.9

_W_GPU_P80       = 0.3
_W_GPU_HIGH_LOAD = 0.3
_W_VRAM_P80      = 0.2
_W_VRAM_HIGH_LOAD = 0.2


def _grade(score: float) -> str:
    if score >= 0.7:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"


def score_gpu_vram(gpu: dict, vram: dict) -> dict:
    """
    gpu:  result["resource_usage"]["gpu"]  from analyze_gpu_usage()
    vram: result["resource_usage"]["vram"] from analyze_vram_usage()
    returns: {"score": float, "grade": str, "factors": dict}
    """
    gpu_not_detected_ratio = gpu.get("gpu_not_detected_ratio") or 0.0
    if gpu_not_detected_ratio > _GPU_NOT_DETECTED_THRESHOLD:
        return {
            "score": 0.0,
            "grade": "unknown",
            "factors": {
                "gpu_p80_percent":       None,
                "gpu_high_load_ratio":   None,
                "vram_p80_percent":      None,
                "vram_high_load_ratio":  None,
                "gpu_not_detected_ratio": round(gpu_not_detected_ratio, 4),
            },
        }

    gpu_p80           = (gpu.get("raw") or {}).get("percentile_80") or 0.0
    gpu_high_load     = gpu.get("high_load_ratio") or 0.0

    vram_p80          = ((vram.get("usage_percent") or {}).get("raw") or {}).get("percentile_80") or 0.0
    vram_high_load    = vram.get("high_load_ratio") or 0.0

    has_vram = vram_p80 > 0 or vram_high_load > 0

    if has_vram:
        score = (
            (gpu_p80 / 100.0) * _W_GPU_P80
            + gpu_high_load    * _W_GPU_HIGH_LOAD
            + (vram_p80 / 100.0) * _W_VRAM_P80
            + vram_high_load   * _W_VRAM_HIGH_LOAD
        )
    else:
        total_gpu_weight = _W_GPU_P80 + _W_GPU_HIGH_LOAD
        score = (gpu_p80 / 100.0) * (_W_GPU_P80 / total_gpu_weight) + gpu_high_load * (_W_GPU_HIGH_LOAD / total_gpu_weight)

    score = round(min(score, 1.0), 4)

    return {
        "score": score,
        "grade": _grade(score),
        "factors": {
            "gpu_p80_percent":        round(gpu_p80, 2),
            "gpu_high_load_ratio":    round(gpu_high_load, 4),
            "vram_p80_percent":       round(vram_p80, 2) if has_vram else None,
            "vram_high_load_ratio":   round(vram_high_load, 4) if has_vram else None,
            "gpu_not_detected_ratio": round(gpu_not_detected_ratio, 4),
        },
    }
