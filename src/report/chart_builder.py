import base64
import io

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

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


# ── KAN-97: 사용 패턴 차트 ────────────────────────────────────────────────────

_DAY_LABELS = ["월", "화", "수", "목", "금", "토", "일"]


def build_time_pattern_chart(pattern_series: dict) -> str:
    hourly = pattern_series.get("hourly", [0] * 24)
    daily  = pattern_series.get("daily",  [0] * 7)

    fig = plt.figure(figsize=(12, 4))
    fig.suptitle("사용 시간 분포", fontsize=14, fontweight="bold", y=1.01)
    gs = gridspec.GridSpec(1, 2, figure=fig, wspace=0.45)

    ax_h = fig.add_subplot(gs[0])
    xs = list(range(24))
    bars = ax_h.bar(xs, hourly, color=_C_BLUE, width=0.7, edgecolor="white")
    peak_h = hourly.index(max(hourly)) if hourly else 0
    bars[peak_h].set_color(_C_ORANGE)
    ax_h.set_xticks(xs)
    ax_h.set_xticklabels([f"{h}" for h in xs], fontsize=7.5)
    ax_h.set_xlabel("시 (KST)", fontsize=9)
    ax_h.set_ylabel("스냅샷 수", fontsize=9)
    ax_h.set_title("시간대별", fontsize=11)
    ax_h.spines["top"].set_visible(False)
    ax_h.spines["right"].set_visible(False)

    ax_d = fig.add_subplot(gs[1])
    d_colors = [_C_ORANGE if i >= 5 else _C_BLUE for i in range(7)]
    ax_d.bar(_DAY_LABELS, daily, color=d_colors, width=0.6, edgecolor="white")
    ax_d.set_xlabel("요일", fontsize=9)
    ax_d.set_ylabel("스냅샷 수", fontsize=9)
    ax_d.set_title("요일별", fontsize=11)
    ax_d.spines["top"].set_visible(False)
    ax_d.spines["right"].set_visible(False)

    return _fig_to_base64(fig)


def build_usage_heatmap(pattern_series: dict) -> str:
    data = np.array(pattern_series.get("hourly_by_day", [[0] * 24] * 7), dtype=float)

    fig, ax = plt.subplots(figsize=(13, 3.5))
    fig.suptitle("요일 × 시간대 사용 히트맵", fontsize=14, fontweight="bold", y=1.04)

    im = ax.imshow(data, cmap="YlOrRd", aspect="auto", interpolation="nearest")

    ax.set_xticks(range(24))
    ax.set_xticklabels([f"{h}시" for h in range(24)], fontsize=7.5)
    ax.set_yticks(range(7))
    ax.set_yticklabels(_DAY_LABELS, fontsize=9)

    cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label("스냅샷 수", fontsize=9)

    ax.spines[:].set_visible(False)
    ax.tick_params(length=0)

    return _fig_to_base64(fig)


def build_segment_summary_chart(pattern: dict) -> str:
    avg_hours  = pattern.get("average_continuous_usage_hours", 0.0)
    inactive   = pattern.get("inactive_segments", [])
    active_r   = pattern.get("active_snapshot_ratio", 0.0) * 100
    uptime     = pattern.get("uptime", {})
    avg_uptime = uptime.get("average_uptime_hours", 0.0)
    long_r     = uptime.get("long_usage_ratio", 0.0) * 100

    inactive_hours = [s.get("duration_hours", 0) for s in inactive]

    fig = plt.figure(figsize=(11, 4))
    fig.suptitle("사용 세그먼트 요약", fontsize=14, fontweight="bold", y=1.01)
    gs = gridspec.GridSpec(1, 2, figure=fig, wspace=0.45)

    ax_stat = fig.add_subplot(gs[0])
    labels = ["활성 비율 (%)", "평균 연속\n사용 (시간)", "평균 부팅\n유지 (시간)", "장시간 사용\n비율 (%)"]
    values = [active_r, avg_hours, avg_uptime, long_r]
    colors = [_C_BLUE, _C_GREEN, _C_BLUE, _C_ORANGE if long_r >= 30 else _C_GREEN]
    bars = ax_stat.barh(labels, values, color=colors, height=0.5, edgecolor="white")
    ax_stat.set_xlim(0, max(max(values) * 1.25, 1))
    for bar, val in zip(bars, values):
        ax_stat.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                     f"{val:.1f}", va="center", fontsize=9)
    ax_stat.spines["top"].set_visible(False)
    ax_stat.spines["right"].set_visible(False)
    ax_stat.set_title("사용 패턴 지표", fontsize=11)

    ax_gap = fig.add_subplot(gs[1])
    if inactive_hours:
        ax_gap.hist(inactive_hours, bins=min(10, len(inactive_hours)),
                    color=_C_GRAY, edgecolor="white")
        ax_gap.set_xlabel("비활성 구간 길이 (시간)", fontsize=9)
        ax_gap.set_ylabel("횟수", fontsize=9)
        ax_gap.set_title(f"비활성 구간 분포 (총 {len(inactive_hours)}회)", fontsize=11)
    else:
        ax_gap.text(0.5, 0.5, "비활성 구간 없음", ha="center", va="center",
                    transform=ax_gap.transAxes, fontsize=12, color=_C_GRAY)
        ax_gap.axis("off")
        ax_gap.set_title("비활성 구간 분포", fontsize=11)
    ax_gap.spines["top"].set_visible(False)
    ax_gap.spines["right"].set_visible(False)

    return _fig_to_base64(fig)


# ── KAN-98: 디스크 / 프로세스 차트 ──────────────────────────────────────────────

_CATEGORY_COLORS = {
    "game":        "#7B68EE",
    "development": "#4472C4",
    "browser":     "#70AD47",
    "office":      "#ED7D31",
    "media":       "#FFC000",
    "system":      "#A6A6A6",
    "etc":         "#D9D9D9",
}


def build_disk_chart(disk: dict) -> str:
    drives = list(disk.items())
    if not drives:
        fig, ax = plt.subplots(figsize=(5, 3))
        ax.text(0.5, 0.5, "디스크 정보 없음", ha="center", va="center",
                transform=ax.transAxes, fontsize=12, color=_C_GRAY)
        ax.axis("off")
        return _fig_to_base64(fig)

    n = len(drives)
    fig, axes = plt.subplots(1, n, figsize=(max(4.5 * n, 5), 4.5))
    fig.suptitle("드라이브 사용 현황", fontsize=14, fontweight="bold", y=1.02)
    if n == 1:
        axes = [axes]

    for ax, (mountpoint, info) in zip(axes, drives):
        total_gb  = info.get("total_gb") or 0
        pct_avg   = (info.get("percent_stats") or {}).get("average") or 0
        used_avg  = total_gb * pct_avg / 100 if total_gb else 0
        free_avg  = total_gb - used_avg
        drive_type = info.get("drive_type", "Unknown")
        danger    = info.get("danger_ratio", 0.0) * 100

        used_color = _C_RED if pct_avg >= 90 else (_C_ORANGE if pct_avg >= 70 else _C_GREEN)

        wedges, _ = ax.pie(
            [max(used_avg, 0), max(free_avg, 0)],
            colors=[used_color, "#E8E8E8"],
            startangle=90,
            wedgeprops={"width": 0.55, "edgecolor": "white", "linewidth": 1.5},
        )

        label = mountpoint.rstrip("\\").rstrip("/") or mountpoint
        ax.text(0, 0.08, f"{pct_avg:.1f}%", ha="center", va="center",
                fontsize=18, fontweight="bold", color=used_color)
        ax.text(0, -0.22, f"{used_avg:.0f} / {total_gb:.0f} GB", ha="center", va="center",
                fontsize=8.5, color="#555555")

        ax.set_title(f"{label}  ({drive_type})", fontsize=10, fontweight="bold", pad=10)
        if danger > 0:
            ax.text(0, -1.55, f"위험 비율 {danger:.0f}%", ha="center", fontsize=8,
                    color=_C_RED)

    plt.tight_layout()
    return _fig_to_base64(fig)


def _draw_process_bars(ax, items: list[dict], value_key: str, unit: str, title: str) -> None:
    if not items:
        ax.text(0.5, 0.5, "데이터 없음", ha="center", va="center",
                transform=ax.transAxes, fontsize=11, color=_C_GRAY)
        ax.axis("off")
        ax.set_title(title, fontsize=11)
        return

    names  = [p["name"][:20] for p in reversed(items)]
    values = [p.get(value_key) or 0.0 for p in reversed(items)]
    cats   = [p.get("category", "etc") for p in reversed(items)]
    colors = [_CATEGORY_COLORS.get(c, _CATEGORY_COLORS["etc"]) for c in cats]

    bars = ax.barh(names, values, color=colors, height=0.6, edgecolor="white")
    ax.set_xlabel(unit, fontsize=9)
    ax.set_title(title, fontsize=11)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="y", labelsize=8)

    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + max(values) * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}", va="center", fontsize=7.5)


def build_process_chart(process: dict) -> str:
    top_freq = process.get("top_by_frequency", [])
    top_cpu  = process.get("top_by_cpu", [])
    top_mem  = process.get("top_by_memory", [])

    fig = plt.figure(figsize=(15, 5.5))
    fig.suptitle("주요 프로세스", fontsize=14, fontweight="bold", y=1.02)
    gs = gridspec.GridSpec(1, 3, figure=fig, wspace=0.55)

    _draw_process_bars(fig.add_subplot(gs[0]), top_freq[:10],
                       "appearance_ratio", "출현 비율", "출현 빈도 Top 10")
    _draw_process_bars(fig.add_subplot(gs[1]), top_cpu[:10],
                       "avg_cpu_percent", "CPU (%)", "CPU 사용 Top 10")
    _draw_process_bars(fig.add_subplot(gs[2]), top_mem[:10],
                       "avg_memory_mb", "메모리 (MB)", "메모리 사용 Top 10")

    legend_patches = [
        plt.Rectangle((0, 0), 1, 1, color=color, label=cat)
        for cat, color in _CATEGORY_COLORS.items()
    ]
    fig.legend(handles=legend_patches, loc="lower center", ncol=len(_CATEGORY_COLORS),
               fontsize=8, frameon=False, bbox_to_anchor=(0.5, -0.04))

    return _fig_to_base64(fig)


def build_category_chart(process: dict) -> str:
    summary = process.get("category_summary", {})
    filtered = {k: v for k, v in summary.items() if k not in ("etc",) and v > 0}
    if not filtered:
        filtered = {k: v for k, v in summary.items() if v > 0}

    fig, ax = plt.subplots(figsize=(7, 4.5))
    fig.suptitle("프로세스 카테고리 분포", fontsize=14, fontweight="bold", y=1.02)

    if not filtered:
        ax.text(0.5, 0.5, "데이터 없음", ha="center", va="center",
                transform=ax.transAxes, fontsize=12, color=_C_GRAY)
        ax.axis("off")
        return _fig_to_base64(fig)

    labels = list(filtered.keys())
    values = list(filtered.values())
    colors = [_CATEGORY_COLORS.get(k, _CATEGORY_COLORS["etc"]) for k in labels]
    explode = [0.04] * len(labels)

    wedges, texts, autotexts = ax.pie(
        values, labels=labels, colors=colors, explode=explode,
        autopct="%1.1f%%", startangle=90,
        wedgeprops={"edgecolor": "white", "linewidth": 1.5},
        textprops={"fontsize": 9},
    )
    for at in autotexts:
        at.set_fontsize(8)

    return _fig_to_base64(fig)
