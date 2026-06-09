_NOISE_CATEGORIES = {"browser", "etc"}
_PRESENCE_THRESHOLD = 0.10

_GPU_BOOST_THRESHOLD       = 0.15
_CPU_EPISODE_BOOST         = True
_VRAM_P80_BOOST_THRESHOLD  = 60.0

_GAME_GPU_BOOST   = 0.20
_GAME_VRAM_BOOST  = 0.15
_DEV_CPU_BOOST    = 0.15


def _category_base_scores(category_summary: dict, total_snapshots: int) -> dict[str, float]:
    filtered = {
        cat: count
        for cat, count in category_summary.items()
        if cat not in _NOISE_CATEGORIES
    }
    if not filtered or total_snapshots == 0:
        return {}

    total = sum(filtered.values())
    if total == 0:
        return {cat: 0.0 for cat in filtered}

    return {cat: count / total for cat, count in filtered.items()}


def _extract_hardware_signals(analysis: dict) -> dict:
    cpu  = analysis.get("resource_usage", {}).get("cpu",  {})
    gpu  = analysis.get("resource_usage", {}).get("gpu",  {})
    vram = analysis.get("resource_usage", {}).get("vram", {})

    gpu_high_load_ratio     = gpu.get("high_load_ratio", 0.0) or 0.0
    cpu_sustained_episodes  = (cpu.get("sustained_high_load") or {}).get("episode_count", 0) or 0
    vram_p80 = (
        (vram.get("usage_percent") or {})
        .get("raw", {})
        .get("percentile_80") or 0.0
    )

    return {
        "gpu_high_load_ratio":    gpu_high_load_ratio,
        "cpu_sustained_episodes": cpu_sustained_episodes,
        "vram_p80":               vram_p80,
    }


def _apply_hardware_boosts(scores: dict[str, float], signals: dict) -> dict[str, float]:
    boosted = dict(scores)

    # 하드웨어 부스트는 해당 카테고리가 이미 base_scores에 존재할 때만 적용한다.
    # 사용자가 모든 프로세스를 수동 재분류한 경우 하드웨어 신호로 분류가 덮어씌워지지 않도록 하기 위함.
    if signals["gpu_high_load_ratio"] > _GPU_BOOST_THRESHOLD and "game" in boosted:
        boosted["game"] = boosted["game"] + _GAME_GPU_BOOST

    if signals["vram_p80"] > _VRAM_P80_BOOST_THRESHOLD and "game" in boosted:
        boosted["game"] = boosted["game"] + _GAME_VRAM_BOOST

    if signals["cpu_sustained_episodes"] > 0:
        boosted["development"] = boosted.get("development", 0.0) + _DEV_CPU_BOOST

    return {cat: min(score, 1.0) for cat, score in boosted.items()}


def classify_user_type(analysis: dict, total_snapshots: int) -> dict:
    category_summary = analysis.get("process_usage", {}).get("category_summary", {})
    base_scores      = _category_base_scores(category_summary, total_snapshots)
    signals          = _extract_hardware_signals(analysis)
    final_scores     = _apply_hardware_boosts(base_scores, signals)

    user_type = sorted(
        [cat for cat, score in final_scores.items() if score >= _PRESENCE_THRESHOLD],
        key=lambda c: final_scores[c],
        reverse=True,
    )

    return {
        "user_type":       user_type,
        "category_scores": final_scores,
        "hardware_signals": signals,
    }
