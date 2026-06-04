import webbrowser
from datetime import datetime
from pathlib import Path

from src.storage import read_user_profile, get_report_path, ensure_reports_directory
from src.report.report_data_collector import load_usage_logs, collect_report_data
from src.report.chart_builder import (
    build_cpu_chart, build_ram_chart, build_gpu_chart, build_vram_chart,
    build_time_pattern_chart, build_usage_heatmap, build_segment_summary_chart,
    build_disk_chart, build_process_chart, build_category_chart,
    build_score_radar_chart, build_score_summary_chart,
)
from src.report.html_builder import build_html


def _build_charts(data: dict) -> dict:
    rs  = data.get("raw_series", {})
    ps  = data.get("pattern_series", {})
    res = data.get("resource", {})

    return {
        "cpu":          build_cpu_chart(res.get("cpu", {}),  rs.get("cpu", [])),
        "ram":          build_ram_chart(res.get("ram", {}),  rs.get("ram", [])),
        "gpu":          build_gpu_chart(res.get("gpu", {}),  rs.get("gpu", [])),
        "vram":         build_vram_chart(res.get("vram", {}), rs.get("vram_used_mb", [])),
        "time_pattern": build_time_pattern_chart(ps),
        "heatmap":      build_usage_heatmap(ps),
        "segment":      build_segment_summary_chart(data.get("pattern", {})),
        "disk":         build_disk_chart(data.get("disk", {})),
        "process":      build_process_chart(data.get("process", {})),
        "category":     build_category_chart(data.get("process", {})),
        "score_radar":  build_score_radar_chart(data.get("scores", {})),
        "score_summary": build_score_summary_chart(data.get("scores", {})),
    }


def generate_report() -> Path:
    logs = load_usage_logs()
    if not logs:
        raise RuntimeError("분석할 모니터링 데이터가 없습니다. 먼저 모니터링을 실행해주세요.")

    profile = read_user_profile()
    data    = collect_report_data(logs, profile)
    charts  = _build_charts(data)
    html    = build_html(data, charts)

    ensure_reports_directory()
    filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    path = get_report_path(filename)
    path.write_text(html, encoding="utf-8")

    webbrowser.open(path.as_uri())
    return path
