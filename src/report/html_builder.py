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
    "low":      ("낮음",    "#00D4AA", "#0D2B24"),
    "medium":   ("보통",    "#FF8C42", "#2B1A0D"),
    "high":     ("높음",    "#FF5252", "#2B0D0D"),
    "unknown":  ("미감지",  "#8892A4", "#1E2433"),
    "gold":     ("낮음",    "#00D4AA", "#0D2B24"),
    "platinum": ("보통",    "#FF8C42", "#2B1A0D"),
    "titanium": ("높음",    "#FF5252", "#2B0D0D"),
}

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif;
    background: #0F1117; color: #E2E8F0; line-height: 1.6;
}
.container { max-width: 1200px; margin: 0 auto; padding: 28px 24px; }
.header {
    background: linear-gradient(135deg, #0D1B2E 0%, #1A2F4A 100%);
    border: 1px solid #2D3F5A;
    color: white; padding: 36px 32px; border-radius: 14px; margin-bottom: 24px;
    position: relative; overflow: hidden;
}
.header::before {
    content: ''; position: absolute; top: -40px; right: -40px;
    width: 200px; height: 200px; border-radius: 50%;
    background: radial-gradient(circle, rgba(0,212,170,0.08) 0%, transparent 70%);
}
.header-badge {
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(0,212,170,0.12); border: 1px solid rgba(0,212,170,0.3);
    color: #00D4AA; padding: 4px 14px; border-radius: 20px;
    font-size: 11px; font-weight: 700; letter-spacing: 1px; margin-bottom: 14px;
    text-transform: uppercase;
}
.header h1 { font-size: 24px; font-weight: 700; margin-bottom: 6px; color: #F0F4F8; }
.header .sub { color: #8892A4; font-size: 13px; }
.card {
    background: #161B2E; border: 1px solid #2D3748;
    border-radius: 12px; padding: 28px;
    margin-bottom: 20px;
}
.card h2 {
    font-size: 15px; color: #F0F4F8; font-weight: 700;
    border-left: 3px solid #00D4AA; padding-left: 12px; margin-bottom: 22px;
    letter-spacing: -0.3px;
}
.meta-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px;
}
.meta-item {
    background: #0F1420; border: 1px solid #2D3748;
    border-radius: 8px; padding: 14px 16px;
}
.meta-item .label {
    font-size: 10px; color: #8892A4; margin-bottom: 6px;
    text-transform: uppercase; letter-spacing: 0.8px;
}
.meta-item .value { font-size: 20px; font-weight: 700; color: #00D4AA; }
.meta-item .value.small { font-size: 14px; color: #F0F4F8; }
.tag {
    display: inline-block; padding: 3px 12px; border-radius: 20px;
    font-size: 11px; font-weight: 700; margin-right: 6px; margin-bottom: 4px;
    border: 1px solid transparent;
}
.chart-img { width: 100%; height: auto; display: block; border-radius: 8px; }
.chart-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 16px; }
.chart-row.single { grid-template-columns: 1fr; }
.chart-row.three { grid-template-columns: 1fr 1fr 1fr; }
.chart-wrap h3 { font-size: 12px; color: #8892A4; margin-bottom: 8px; font-weight: 600; }
.score-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; align-items: start; }
.info-banner {
    display: flex; align-items: center; gap: 10px;
    background: rgba(0,212,170,0.08); border: 1px solid rgba(0,212,170,0.25);
    border-radius: 8px; padding: 12px 16px; margin-bottom: 18px;
    color: #00D4AA; font-size: 13px; font-weight: 600;
}
.info-banner::before { content: '●'; font-size: 8px; }
table { border-collapse: collapse; }
table thead tr { background: #0F1420; }
table thead th { color: #8892A4; font-size: 10px; text-transform: uppercase; letter-spacing: 0.6px; }
table tbody tr { border-bottom: 1px solid #1E2740; }
table tbody tr:hover { background: #1A2035; }
@media (max-width: 768px) {
    .chart-row, .score-grid { grid-template-columns: 1fr; }
}
footer {
    text-align: center; padding: 32px; color: #4A5568; font-size: 12px;
    border-top: 1px solid #1E2740; margin-top: 8px;
}
footer span { color: #00D4AA; font-weight: 700; }
/* Recommendation section */
.rec-list { display: flex; flex-direction: column; gap: 14px; }
.rec-card {
    background: #0F1420; border: 1px solid #2D3748;
    border-radius: 10px; padding: 18px 20px;
}
.rec-card.rec-psu {
    border-color: rgba(0,212,170,0.2);
    background: rgba(0,212,170,0.03);
}
.rec-header {
    display: flex; align-items: center; gap: 10px; margin-bottom: 10px; flex-wrap: wrap;
}
.rec-part { font-size: 14px; font-weight: 700; color: #F0F4F8; min-width: 44px; }
.rec-priority {
    margin-left: auto; display: flex; align-items: center; gap: 8px;
}
.rec-bar-bg {
    width: 110px; height: 5px; background: #1E2740; border-radius: 3px; overflow: hidden;
}
.rec-bar-fill { height: 100%; border-radius: 3px; background: linear-gradient(90deg, #00D4AA, #00A080); }
.rec-pct { font-size: 11px; color: #8892A4; min-width: 34px; text-align: right; }
.rec-reason { font-size: 13px; color: #A0AEC0; line-height: 1.7; margin-bottom: 10px; }
.rec-spec {
    font-size: 12px; color: #8892A4; padding: 7px 12px;
    background: #161B2E; border-radius: 6px; margin-bottom: 12px;
}
.rec-spec strong { color: #00D4AA; }
.rec-cand-title {
    font-size: 10px; color: #8892A4; text-transform: uppercase;
    letter-spacing: 0.8px; margin-bottom: 8px; font-weight: 600;
}
.rec-cand-row {
    display: flex; align-items: center; gap: 10px;
    padding: 8px 12px; border-radius: 6px; background: #161B2E;
    margin-bottom: 6px; font-size: 13px;
}
.rec-cand-name { flex: 1; color: #E2E8F0; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.rec-cand-price { color: #00D4AA; font-weight: 700; font-size: 13px; white-space: nowrap; }
.rec-cand-link {
    color: #8892A4; font-size: 11px; text-decoration: none;
    padding: 2px 8px; border: 1px solid #2D3748; border-radius: 4px; white-space: nowrap;
}
.rec-cand-link:hover { color: #00D4AA; border-color: #00D4AA; }
.rec-search-hint {
    font-size: 12px; color: #8892A4; padding: 8px 12px;
    background: #161B2E; border-radius: 6px; font-style: italic;
}
"""


def _img(b64: str, alt: str = "") -> str:
    return f'<img class="chart-img" src="data:image/png;base64,{b64}" alt="{html.escape(alt)}">'


def _tag(grade: str) -> str:
    label, fg, bg = _GRADE_KO.get(grade, ("?", "#8892A4", "#1E2433"))
    return f'<span class="tag" style="color:{fg};background:{bg};border-color:{fg}40">{label}</span>'


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
        f'<span class="tag" style="color:#00D4AA;background:rgba(0,212,170,0.1);border-color:rgba(0,212,170,0.3)">'
        f'{_USER_TYPE_KO.get(t, t)}</span>'
        for t in user_types
    ) or '<span class="tag" style="color:#8892A4;background:#1E2433;border-color:#2D3748">분류 없음</span>'

    metas = "".join([
        _meta("총 스냅샷", f"{total:,} 회"),
        _meta("분석 기간", f"{analysis_days} 일"),
        _meta("평균 부팅 유지", f"{avg_uptime:.1f} 시간"),
        _meta("활성 비율", f"{active_r:.1f} %"),
    ])

    return f"""
<div class="card">
  <h2>분석 요약</h2>
  <div class="info-banner">모든 데이터는 이 기기에만 저장됩니다. 외부 서버로 전송되는 정보는 없습니다.</div>
  <div style="margin-bottom:18px">
    <div style="font-size:11px;color:#8892A4;margin-bottom:8px;text-transform:uppercase;letter-spacing:0.8px">사용자 유형</div>
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
  <div class="chart-row single" style="margin-bottom:16px">
    {_img(time_b64, "사용 시간 분포")}
  </div>
  <div class="chart-row single" style="margin-bottom:16px">
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
  <div class="chart-row single" style="margin-bottom:16px">
    {_img(process_b64, "프로세스")}
  </div>
  <div class="chart-row" style="grid-template-columns:1fr 2fr">
    <div>{_img(category_b64, "카테고리")}</div>
    <div style="display:flex;align-items:center;padding:20px;background:#0F1420;border-radius:8px;border:1px solid #2D3748">
      <p style="color:#8892A4;font-size:13px;line-height:2.0">
        카테고리 분포는 각 프로세스의 출현 빈도를 기반으로 집계됩니다.<br>
        <span style="color:#00D4AA;font-weight:600">게임</span>·<span style="color:#00D4AA;font-weight:600">개발</span> 비중이 높을수록 GPU·CPU 부하와 연관성이 높습니다.
      </p>
    </div>
  </div>
</div>"""


def _section_scores(data: dict, charts: dict) -> str:
    scores      = data.get("scores") or {}
    radar_b64   = charts.get("score_radar", "")
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
            f'<tr>'
            f'<td style="padding:11px 10px;font-weight:600;color:#F0F4F8">{label}</td>'
            f'<td style="padding:11px 10px">{_tag(grade)}</td>'
            f'<td style="padding:11px 10px;color:#8892A4;font-size:13px;font-family:monospace">{score:.3f}</td>'
            f'</tr>'
        )

    table = f"""
<table style="width:100%;font-size:14px">
  <thead>
    <tr>
      <th style="padding:10px 10px;text-align:left">부품</th>
      <th style="padding:10px 10px;text-align:left">등급</th>
      <th style="padding:10px 10px;text-align:left">점수</th>
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


def _format_price(price_krw: int | None) -> str:
    if price_krw is None:
        return "가격 미확인"
    return f"₩ {price_krw:,}"


def _rec_spec_html(item: dict) -> str:
    part        = item["part"]
    current_tier = item.get("current_tier")
    target_tier  = item.get("target_tier")
    target_spec  = item.get("target_spec") or {}

    if part in ("CPU", "GPU") and target_tier:
        if current_tier:
            inner = f"<strong>Tier {current_tier} → Tier {target_tier}</strong>"
        else:
            inner = f"목표 <strong>Tier {target_tier}</strong>"
        return f'<div class="rec-spec">{inner}</div>'

    note = html.escape(target_spec.get("note", ""))
    if part == "PSU":
        label = html.escape(target_spec.get("recommended_efficiency", ""))
        if label:
            return (
                f'<div class="rec-spec">'
                f'권장 효율 등급: <strong>80+ {label}</strong>'
                + (f'<br><span style="font-size:11px">{note}</span>' if note else "")
                + "</div>"
            )
    if note:
        return f'<div class="rec-spec">{note}</div>'
    return ""


def _rec_candidates_html(item: dict) -> str:
    part        = item["part"]
    candidates  = item.get("candidates") or []
    search_query = html.escape(item.get("search_query") or "")

    if part == "PSU":
        return ""

    if not candidates:
        if search_query:
            return (
                f'<div class="rec-search-hint">'
                f'네이버 쇼핑 검색어: <strong>{search_query}</strong>'
                f"</div>"
            )
        return ""

    rows = ""
    for c in candidates[:3]:
        name  = html.escape((c.get("name") or "")[:60])
        price = _format_price(c.get("price_krw"))
        url   = c.get("product_url") or ""
        link  = (
            f'<a class="rec-cand-link" href="{html.escape(url)}" target="_blank">구매</a>'
            if url else ""
        )
        rows += (
            f'<div class="rec-cand-row">'
            f'<span class="rec-cand-name">{name}</span>'
            f'<span class="rec-cand-price">{price}</span>'
            f'{link}'
            f"</div>"
        )

    return f'<div class="rec-cand-title">후보 제품</div>{rows}'


def _section_recommendations(items: list[dict]) -> str:
    if not items:
        return """
<div class="card">
  <h2>하드웨어 업그레이드 추천</h2>
  <div class="info-banner" style="color:#8892A4;background:rgba(136,146,164,0.06);border-color:rgba(136,146,164,0.2)">
    현재 사용 패턴에서 즉각적인 업그레이드가 권고되는 부품이 없습니다.
  </div>
</div>"""

    cards = ""
    for item in items:
        part     = item["part"]
        grade    = item.get("grade", "unknown")
        priority = item.get("priority", 0.0)
        reason   = html.escape(item.get("reason", ""))
        is_psu   = (part == "PSU")

        if is_psu:
            grade_tag = '<span class="tag" style="color:#8892A4;background:#1E2433;border-color:#2D3748">의존성</span>'
            priority_html = ""
        else:
            grade_tag     = _tag(grade)
            bar_pct       = min(int(priority / 1.5 * 100), 100)
            priority_html = (
                f'<div class="rec-priority">'
                f'<div class="rec-bar-bg">'
                f'<div class="rec-bar-fill" style="width:{bar_pct}%"></div>'
                f"</div>"
                f'<span class="rec-pct">{int(priority * 100)}%</span>'
                f"</div>"
            )

        spec_html  = _rec_spec_html(item)
        cand_html  = _rec_candidates_html(item)
        card_class = "rec-card rec-psu" if is_psu else "rec-card"

        cards += (
            f'<div class="{card_class}">'
            f'<div class="rec-header">'
            f'<span class="rec-part">{html.escape(part)}</span>'
            f'{grade_tag}'
            f'{priority_html}'
            f"</div>"
            f'<p class="rec-reason">{reason}</p>'
            f'{spec_html}'
            f'{cand_html}'
            f"</div>"
        )

    return f"""
<div class="card">
  <h2>하드웨어 업그레이드 추천</h2>
  <div class="rec-list">{cards}</div>
</div>"""


def build_html(report_data: dict, charts: dict) -> str:
    now_str = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")

    body = (
        _section_summary(report_data)
        + _section_resource(charts)
        + _section_pattern(charts)
        + _section_disk_process(charts)
        + _section_scores(report_data, charts)
        + _section_recommendations(report_data.get("recommendations") or [])
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
      <div class="header-badge">BuildSense · 분석 보고서</div>
      <h1>맞춤형 하드웨어 업그레이드 보고서</h1>
      <div class="sub">생성 일시: {html.escape(now_str)}</div>
    </div>
    {body}
    <footer>
      <span>BuildSense</span> &nbsp;·&nbsp; 본 보고서는 모니터링 데이터를 기반으로 자동 생성되었습니다.
    </footer>
  </div>
</body>
</html>"""
