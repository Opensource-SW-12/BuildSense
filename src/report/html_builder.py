import html
from datetime import datetime

_USER_TYPE_KO = {
    "game":        "게임",
    "development": "개발",
    "browser":     "브라우저",
    "office":      "오피스",
    "media":       "미디어",
    "system":      "시스템",
    "etc":         "기타",
}

_GRADE_KO = {
    "low":      ("낮음",    "#2E7D32", "#E8F5E9"),
    "medium":   ("보통",    "#E65100", "#FFF3E0"),
    "high":     ("높음",    "#C62828", "#FFEBEE"),
    "unknown":  ("미감지",  "#666666", "#F5F5F5"),
    "gold":     ("낮음",    "#2E7D32", "#E8F5E9"),
    "platinum": ("보통",    "#E65100", "#FFF3E0"),
    "titanium": ("높음",    "#C62828", "#FFEBEE"),
}

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif;
    background: #F0F2F5; color: #333; line-height: 1.6;
}
.container { max-width: 1200px; margin: 0 auto; padding: 24px; }
.header {
    background: linear-gradient(135deg, #1A3A5C 0%, #2D6A9F 100%);
    color: white; padding: 36px 32px; border-radius: 14px; margin-bottom: 28px;
}
.header h1 { font-size: 26px; margin-bottom: 6px; letter-spacing: -0.5px; }
.header .sub { opacity: 0.75; font-size: 14px; }
.card {
    background: white; border-radius: 12px; padding: 28px;
    margin-bottom: 24px; box-shadow: 0 2px 10px rgba(0,0,0,0.07);
}
.card h2 {
    font-size: 17px; color: #1A3A5C;
    border-left: 4px solid #4472C4; padding-left: 12px; margin-bottom: 22px;
}
.meta-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 14px;
}
.meta-item { background: #F8F9FA; border-radius: 8px; padding: 14px 16px; }
.meta-item .label { font-size: 11px; color: #999; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
.meta-item .value { font-size: 18px; font-weight: 700; color: #1A3A5C; }
.meta-item .value.small { font-size: 14px; }
.tag {
    display: inline-block; padding: 4px 12px; border-radius: 20px;
    font-size: 12px; font-weight: 700; margin-right: 6px; margin-bottom: 4px;
}
.chart-img { width: 100%; height: auto; display: block; border-radius: 6px; }
.chart-row { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 16px; }
.chart-row.single { grid-template-columns: 1fr; }
.chart-row.three { grid-template-columns: 1fr 1fr 1fr; }
.chart-wrap { }
.chart-wrap h3 { font-size: 13px; color: #666; margin-bottom: 8px; font-weight: 600; }
.score-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; align-items: start; }
@media (max-width: 768px) {
    .chart-row, .score-grid { grid-template-columns: 1fr; }
}
footer { text-align: center; padding: 28px; color: #BBB; font-size: 12px; }
footer span { color: #888; }
"""


def _img(b64: str, alt: str = "") -> str:
    return f'<img class="chart-img" src="data:image/png;base64,{b64}" alt="{html.escape(alt)}">'


def _tag(grade: str) -> str:
    label, fg, bg = _GRADE_KO.get(grade, ("?", "#666", "#EEE"))
    return f'<span class="tag" style="color:{fg};background:{bg}">{label}</span>'


def _meta(label: str, value: str, small: bool = False) -> str:
    cls = "small" if small else ""
    return (
        f'<div class="meta-item">'
        f'<div class="label">{html.escape(label)}</div>'
        f'<div class="value {cls}">{html.escape(str(value))}</div>'
        f'</div>'
    )


def _section_summary(data: dict) -> str:
    total      = data.get("total_snapshots", 0)
    user_types = (data.get("user_type") or {}).get("user_type", [])
    profile    = data.get("profile") or {}
    pattern    = data.get("pattern") or {}
    uptime     = pattern.get("uptime") or {}
    avg_uptime = uptime.get("average_uptime_hours", 0.0)
    active_r   = pattern.get("active_snapshot_ratio", 0.0) * 100
    analysis_days = profile.get("analysis_days", "-")

    type_tags = "".join(
        f'<span class="tag" style="color:#1565C0;background:#E3F2FD">'
        f'{_USER_TYPE_KO.get(t, t)}</span>'
        for t in user_types
    ) or '<span class="tag" style="color:#666;background:#F5F5F5">분류 없음</span>'

    metas = "".join([
        _meta("총 스냅샷", f"{total:,} 회"),
        _meta("분석 기간", f"{analysis_days} 일"),
        _meta("평균 부팅 유지", f"{avg_uptime:.1f} 시간"),
        _meta("활성 비율", f"{active_r:.1f} %"),
    ])

    return f"""
<div class="card">
  <h2>분석 요약</h2>
  <div style="margin-bottom:16px">
    <div class="label" style="font-size:12px;color:#999;margin-bottom:8px">사용자 유형</div>
    {type_tags}
  </div>
  <div class="meta-grid">{metas}</div>
</div>"""


def _section_resource(charts: dict) -> str:
    rows = ""
    for key, label in [("cpu", "CPU"), ("ram", "RAM"), ("gpu", "GPU"), ("vram", "VRAM")]:
        b64 = charts.get(key)
        if b64:
            rows += f'<div class="chart-wrap">{_img(b64, label)}</div>'

    return f"""
<div class="card">
  <h2>리소스 사용량</h2>
  <div class="chart-row">{rows}</div>
</div>"""


def _section_pattern(charts: dict) -> str:
    time_b64    = charts.get("time_pattern", "")
    heatmap_b64 = charts.get("heatmap", "")
    segment_b64 = charts.get("segment", "")

    return f"""
<div class="card">
  <h2>사용 패턴</h2>
  <div class="chart-row single" style="margin-bottom:20px">
    {_img(time_b64, "사용 시간 분포")}
  </div>
  <div class="chart-row single" style="margin-bottom:20px">
    {_img(heatmap_b64, "히트맵")}
  </div>
  <div class="chart-row single">
    {_img(segment_b64, "세그먼트 요약")}
  </div>
</div>"""


def _section_disk_process(charts: dict) -> str:
    disk_b64     = charts.get("disk", "")
    process_b64  = charts.get("process", "")
    category_b64 = charts.get("category", "")

    return f"""
<div class="card">
  <h2>디스크 현황</h2>
  <div class="chart-row single">{_img(disk_b64, "디스크")}</div>
</div>
<div class="card">
  <h2>프로세스 분석</h2>
  <div class="chart-row single" style="margin-bottom:20px">
    {_img(process_b64, "프로세스")}
  </div>
  <div class="chart-row" style="grid-template-columns:1fr 2fr">
    <div>{_img(category_b64, "카테고리")}</div>
    <div style="display:flex;align-items:center;padding:16px;background:#F8F9FA;border-radius:8px">
      <p style="color:#666;font-size:13px;line-height:1.9">
        카테고리 분포는 각 프로세스의 출현 빈도를 기반으로 집계됩니다.<br>
        <b>게임</b>·<b>개발</b> 비중이 높을수록 GPU·CPU 부하와 연관성이 높습니다.
      </p>
    </div>
  </div>
</div>"""


def _section_scores(data: dict, charts: dict) -> str:
    scores     = data.get("scores") or {}
    radar_b64  = charts.get("score_radar", "")
    summary_b64 = charts.get("score_summary", "")

    part_map = [
        ("cpu",      "CPU"),
        ("ram",      "RAM"),
        ("gpu_vram", "GPU / VRAM"),
        ("ssd",      "SSD"),
        ("hdd",      "HDD"),
        ("psu",      "PSU"),
    ]

    rows = ""
    for key, label in part_map:
        s = scores.get(key)
        if s is None:
            continue
        grade = s.get("grade", "unknown")
        score = s.get("score", 0.0)
        rows += (
            f'<tr style="border-bottom:1px solid #F0F0F0">'
            f'<td style="padding:10px 8px;font-weight:600">{label}</td>'
            f'<td style="padding:10px 8px">{_tag(grade)}</td>'
            f'<td style="padding:10px 8px;color:#888;font-size:13px">{score:.3f}</td>'
            f'</tr>'
        )

    table = f"""
<table style="width:100%;border-collapse:collapse;font-size:14px">
  <thead>
    <tr style="background:#F8F9FA;color:#999;font-size:11px;text-transform:uppercase">
      <th style="padding:10px 8px;text-align:left">부품</th>
      <th style="padding:10px 8px;text-align:left">등급</th>
      <th style="padding:10px 8px;text-align:left">점수</th>
    </tr>
  </thead>
  <tbody>{rows}</tbody>
</table>"""

    return f"""
<div class="card">
  <h2>업그레이드 필요도</h2>
  <div class="score-grid">
    <div>{_img(radar_b64, "레이더 차트")}</div>
    <div>
      <div style="margin-bottom:20px">{_img(summary_b64, "점수 요약")}</div>
      {table}
    </div>
  </div>
</div>"""


def build_html(report_data: dict, charts: dict) -> str:
    now_str = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")

    body = (
        _section_summary(report_data)
        + _section_resource(charts)
        + _section_pattern(charts)
        + _section_disk_process(charts)
        + _section_scores(report_data, charts)
    )

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>BuildSense 분석 보고서</title>
  <style>{_CSS}</style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>BuildSense 분석 보고서</h1>
      <div class="sub">생성 일시: {html.escape(now_str)}</div>
    </div>
    {body}
    <footer>
      <span>BuildSense</span> &nbsp;·&nbsp; 본 보고서는 모니터링 데이터를 기반으로 자동 생성되었습니다.
    </footer>
  </div>
</body>
</html>"""
