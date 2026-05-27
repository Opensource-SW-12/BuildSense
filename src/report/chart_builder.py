import base64
import io

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from src.report.font_config import setup_korean_font

setup_korean_font()

_C_BLUE   = "#4472C4"
_C_GREEN  = "#70AD47"
_C_ORANGE = "#ED7D31"
_C_RED    = "#FF0000"
_C_GRAY   = "#A6A6A6"

_STAT_LABELS = ["최솟값", "평균", "중앙값", "P80", "최댓값"]
_STAT_KEYS   = ["min", "average", "median", "percentile_80", "max"]


def _fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=110)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def _stat_values(raw: dict) -> list[float]:
    return [raw.get(k) or 0.0 for k in _STAT_KEYS]


def _bar_colors(values: list[float], threshold: float) -> list[str]:
    colors = []
    for v in values:
        if v >= threshold:
            colors.append(_C_RED)
        elif v >= threshold * 0.75:
            colors.append(_C_ORANGE)
        else:
            colors.append(_C_BLUE)
    return colors


def _draw_stat_bars(ax, raw: dict, threshold: float, unit: str = "%") -> None:
    values = _stat_values(raw)
    colors = _bar_colors(values, threshold)
    bars = ax.barh(_STAT_LABELS, values, color=colors, height=0.55, edgecolor="white")

    ax.set_xlim(0, 105 if unit == "%" else max(values) * 1.25 or 1)
    ax.set_xlabel(unit, fontsize=9)
    ax.tick_params(axis="y", labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    for bar, val in zip(bars, values):
        ax.text(
            bar.get_width() + 1.5,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}{unit}",
            va="center", fontsize=8.5,
        )


def _draw_time_series(ax, values: list, threshold: float, label: str, unit: str = "%") -> None:
    clean = [v if v is not None else float("nan") for v in values]
    xs = list(range(len(clean)))

    ax.plot(xs, clean, color=_C_BLUE, linewidth=1.2, alpha=0.85)
    ax.axhline(threshold, color=_C_RED, linewidth=0.9, linestyle="--", alpha=0.7)
    ax.fill_between(xs, clean, alpha=0.15, color=_C_BLUE)

    ax.set_xlim(0, max(len(xs) - 1, 1))
    ax.set_ylim(0, 105 if unit == "%" else None)
    ax.set_xlabel("스냅샷 순서", fontsize=9)
    ax.set_ylabel(unit, fontsize=9)
    ax.tick_params(labelsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def build_cpu_chart(cpu: dict, raw_series: list) -> str:
    fig = plt.figure(figsize=(10, 4))
    fig.suptitle("CPU 사용량", fontsize=14, fontweight="bold", y=1.01)
    gs = gridspec.GridSpec(1, 2, figure=fig, wspace=0.4)

    ax_bar = fig.add_subplot(gs[0])
    _draw_stat_bars(ax_bar, cpu.get("raw", {}), threshold=75)
    ax_bar.set_title("통계 요약", fontsize=11)

    high_ratio = cpu.get("high_load_ratio", 0.0) * 100
    episodes   = (cpu.get("sustained_high_load") or {}).get("episode_count", 0)
    ax_bar.text(
        0.98, 0.04,
        f"고부하 비율 {high_ratio:.1f}%  |  지속 고부하 {episodes}회",
        transform=ax_bar.transAxes, ha="right", fontsize=8, color=_C_GRAY,
    )

    ax_ts = fig.add_subplot(gs[1])
    _draw_time_series(ax_ts, raw_series, threshold=75, label="CPU")
    ax_ts.set_title("시계열", fontsize=11)

    return _fig_to_base64(fig)


def build_ram_chart(ram: dict, raw_series: list) -> str:
    fig = plt.figure(figsize=(10, 4))
    fig.suptitle("RAM 사용량", fontsize=14, fontweight="bold", y=1.01)
    gs = gridspec.GridSpec(1, 2, figure=fig, wspace=0.4)

    ax_bar = fig.add_subplot(gs[0])
    _draw_stat_bars(ax_bar, ram.get("raw", {}), threshold=85)
    ax_bar.set_title("통계 요약", fontsize=11)

    high_ratio     = ram.get("high_load_ratio", 0.0) * 100
    sustained_min  = ram.get("max_sustained_high_load_minutes", 0.0)
    ax_bar.text(
        0.98, 0.04,
        f"고부하 비율 {high_ratio:.1f}%  |  최대 연속 고부하 {sustained_min:.0f}분",
        transform=ax_bar.transAxes, ha="right", fontsize=8, color=_C_GRAY,
    )

    ax_ts = fig.add_subplot(gs[1])
    _draw_time_series(ax_ts, raw_series, threshold=85, label="RAM")
    ax_ts.set_title("시계열", fontsize=11)

    return _fig_to_base64(fig)


def build_gpu_chart(gpu: dict, raw_series: list) -> str:
    not_detected = gpu.get("gpu_not_detected_ratio", 0.0)

    fig = plt.figure(figsize=(10, 4))
    fig.suptitle("GPU 사용량", fontsize=14, fontweight="bold", y=1.01)
    gs = gridspec.GridSpec(1, 2, figure=fig, wspace=0.4)

    ax_bar = fig.add_subplot(gs[0])

    if not_detected >= 1.0:
        ax_bar.text(0.5, 0.5, "GPU 감지되지 않음", ha="center", va="center",
                    transform=ax_bar.transAxes, fontsize=12, color=_C_GRAY)
        ax_bar.axis("off")
    else:
        _draw_stat_bars(ax_bar, gpu.get("raw", {}), threshold=80)
        high_ratio = gpu.get("high_load_ratio", 0.0) * 100
        ax_bar.text(
            0.98, 0.04,
            f"고부하 비율 {high_ratio:.1f}%  |  미감지 {not_detected*100:.0f}%",
            transform=ax_bar.transAxes, ha="right", fontsize=8, color=_C_GRAY,
        )
    ax_bar.set_title("통계 요약", fontsize=11)

    ax_ts = fig.add_subplot(gs[1])
    valid = [v for v in raw_series if v is not None]
    if valid:
        _draw_time_series(ax_ts, raw_series, threshold=80, label="GPU")
    else:
        ax_ts.text(0.5, 0.5, "데이터 없음", ha="center", va="center",
                   transform=ax_ts.transAxes, fontsize=11, color=_C_GRAY)
        ax_ts.axis("off")
    ax_ts.set_title("시계열", fontsize=11)

    return _fig_to_base64(fig)


def build_vram_chart(vram: dict, raw_series: list) -> str:
    total_mb    = vram.get("vram_total_mb") or 0
    pct_raw     = (vram.get("usage_percent") or {}).get("raw", {})
    used_raw    = (vram.get("used_mb") or {}).get("raw", {})
    high_ratio  = vram.get("high_load_ratio", 0.0) * 100
    total_gb    = total_mb / 1024 if total_mb else 0

    fig = plt.figure(figsize=(10, 4))
    title = f"VRAM 사용량 (총 {total_gb:.1f} GB)" if total_gb else "VRAM 사용량"
    fig.suptitle(title, fontsize=14, fontweight="bold", y=1.01)
    gs = gridspec.GridSpec(1, 2, figure=fig, wspace=0.4)

    ax_bar = fig.add_subplot(gs[0])
    if not pct_raw or pct_raw.get("average") is None:
        ax_bar.text(0.5, 0.5, "VRAM 감지되지 않음", ha="center", va="center",
                    transform=ax_bar.transAxes, fontsize=12, color=_C_GRAY)
        ax_bar.axis("off")
    else:
        _draw_stat_bars(ax_bar, pct_raw, threshold=90)
        used_avg = used_raw.get("average") or 0
        ax_bar.text(
            0.98, 0.04,
            f"고부하 비율 {high_ratio:.1f}%  |  평균 사용 {used_avg/1024:.1f} GB",
            transform=ax_bar.transAxes, ha="right", fontsize=8, color=_C_GRAY,
        )
    ax_bar.set_title("사용률 통계 (%)", fontsize=11)

    ax_ts = fig.add_subplot(gs[1])
    valid = [v for v in raw_series if v is not None]
    if valid and total_mb:
        pct_series = [v / total_mb * 100 if v is not None else None for v in raw_series]
        _draw_time_series(ax_ts, pct_series, threshold=90, label="VRAM")
    else:
        ax_ts.text(0.5, 0.5, "데이터 없음", ha="center", va="center",
                   transform=ax_ts.transAxes, fontsize=11, color=_C_GRAY)
        ax_ts.axis("off")
    ax_ts.set_title("시계열", fontsize=11)

    return _fig_to_base64(fig)
