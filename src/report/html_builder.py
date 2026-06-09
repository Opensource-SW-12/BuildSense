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

_PART_KO = {
    "CPU":         "CPU",
    "GPU":         "GPU",
    "RAM":         "RAM",
    "SSD":         "SSD",
    "HDD":         "HDD",
    "PSU":         "파워 서플라이",
    "Motherboard": "메인보드",
}

_KNOWLEDGE_LEVEL_KO = {
    "beginner":     "전혀 모름",
    "intermediate": "어느 정도 알고 있음",
    "advanced":     "잘 알고 있음",
}

_PART_OPTION_KO = {
    "recommend": "추천",
    "keep":      "유지",
}

_RGB_PREFERENCE_KO = {
    "yes":  "선호함",
    "no":   "선호하지 않음",
    "none": "상관없음",
}

_COLOR_PREFERENCE_KO = {
    "black": "검정",
    "white": "흰색",
    "none":  "상관없음",
}

_PROCESS_CATEGORY_KO = {
    "game":        "게임",
    "development": "개발·프로그래밍",
    "creative":    "영상·이미지 편집",
    "business":    "업무·생산성",
    "streaming":   "스트리밍·방송",
    "browser":     "웹 브라우저",
    "etc":         "기타",
}

_BUDGET_MODE_KO = {
    "recommended": "맞춤 설정 (추천)",
    "max":         "최고 가격",
    "custom":      "직접 설정",
}

_GRADE_KO = {
    "low":      ("낮음",    "#00D4AA", "#0D2B24"),
    "medium":   ("보통",    "#FF8C42", "#2B1A0D"),
    "high":     ("높음",    "#FF5252", "#2B0D0D"),
    "unknown":  ("미감지",  "#A6AEC8", "#1E2433"),
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
.header .sub { color: #A6AEC8; font-size: 13px; }
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
    font-size: 10px; color: #A6AEC8; margin-bottom: 6px;
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
.chart-wrap h3 { font-size: 12px; color: #A6AEC8; margin-bottom: 8px; font-weight: 600; }
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
table thead th { color: #A6AEC8; font-size: 10px; text-transform: uppercase; letter-spacing: 0.6px; }
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
.rec-pct { font-size: 11px; color: #A6AEC8; min-width: 34px; text-align: right; }
.rec-reason { font-size: 13px; color: #A0AEC0; line-height: 1.7; margin-bottom: 10px; }
.rec-spec {
    font-size: 12px; color: #A6AEC8; padding: 7px 12px;
    background: #161B2E; border-radius: 6px; margin-bottom: 12px;
}
.rec-spec strong { color: #00D4AA; }
.rec-cand-title {
    font-size: 10px; color: #A6AEC8; text-transform: uppercase;
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
    color: #A6AEC8; font-size: 11px; text-decoration: none;
    padding: 2px 8px; border: 1px solid #2D3748; border-radius: 4px; white-space: nowrap;
}
.rec-cand-link:hover { color: #00D4AA; border-color: #00D4AA; }
.rec-search-hint {
    font-size: 12px; color: #A6AEC8; padding: 8px 12px;
    background: #161B2E; border-radius: 6px; font-style: italic;
}
"""


def _img(b64: str, alt: str = "") -> str:
    return f'<img class="chart-img" src="data:image/png;base64,{b64}" alt="{html.escape(alt)}">'


def _tag(grade: str) -> str:
    label, fg, bg = _GRADE_KO.get(grade, ("?", "#A6AEC8", "#1E2433"))
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
    ) or '<span class="tag" style="color:#A6AEC8;background:#1E2433;border-color:#2D3748">분류 없음</span>'

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
    <div style="font-size:11px;color:#A6AEC8;margin-bottom:8px;text-transform:uppercase;letter-spacing:0.8px">사용자 유형</div>
    {type_tags}
  </div>
  <div class="meta-grid">{metas}</div>
</div>"""


_HW_PART_KO = {
    "CPU": "CPU",
    "GPU": "GPU",
    "RAM": "RAM",
    "SSD": "SSD",
    "HDD": "HDD",
}

def _hw_spec_block(hw_info: dict) -> str:
    """현재 시스템 사양 블록 HTML을 반환한다. hw_info가 비어 있으면 빈 문자열."""
    if not hw_info:
        return ""
    rows = ""
    for key, label in _HW_PART_KO.items():
        val = hw_info.get(key) or "확인할 수 없음"
        val_escaped = html.escape(str(val))
        color = "#A6AEC8" if val == "확인할 수 없음" else "#E8EAF6"
        rows += (
            f'<div style="display:flex;gap:8px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.05)">'
            f'<span style="width:100px;font-size:12px;color:#A6AEC8;flex-shrink:0">{label}</span>'
            f'<span style="font-size:13px;color:{color};word-break:break-all">{val_escaped}</span>'
            f'</div>'
        )
    return f"""
  <div style="margin-top:22px">
    <div style="font-size:11px;color:#A6AEC8;margin-bottom:8px;text-transform:uppercase;letter-spacing:0.8px">현재 시스템 사양</div>
    <div style="background:#0F1117;border-radius:8px;padding:8px 12px">{rows}</div>
  </div>"""


def _section_user_input(data: dict) -> str:
    profile = data.get("profile") or {}
    prefs   = data.get("user_preferences") or {}

    # ── 최초 입력 (분석 시작 전 설정) ─────────────────────────────
    knowledge_level = profile.get("knowledge_level")
    initial_metas = "".join([
        _meta("컴퓨터 지식 수준", _KNOWLEDGE_LEVEL_KO.get(knowledge_level, "-"), small=True),
        _meta("분석 기간", f"{profile.get('analysis_days', '-')} 일", small=True),
        _meta("데이터 수집 동의", "동의함" if (profile.get("consent") or {}).get("agreed") else "-", small=True),
    ])

    parts_config = profile.get("parts") or {}
    part_tags = "".join(
        f'<span class="tag" style="color:#A6AEC8;background:#1E2433;border-color:#2D3748">'
        f'{html.escape(part)} · {_PART_OPTION_KO.get((parts_config.get(part) or {}).get("option"), "-")}</span>'
        for part in ["CPU", "GPU", "RAM", "SSD", "HDD", "메인보드", "파워"]
        if part in parts_config
    )

    # ── 최종 입력 (분석 종료 후 답변) ─────────────────────────────
    if prefs:
        budget_mode = prefs.get("budget_mode", "recommended")
        budgets     = prefs.get("budgets") or {}
        mode_label  = _BUDGET_MODE_KO.get(budget_mode, "-")

        if budget_mode == "custom" and budgets:
            parts_str  = " · ".join(
                f"{_PART_KO.get(k, k)} {v:,}원"
                for k, v in budgets.items()
            )
            budget_text = f"{mode_label} ({parts_str})"
        else:
            budget_text = mode_label

        rgb_text   = _RGB_PREFERENCE_KO.get(prefs.get("rgb_preference"), "-")
        color_text = _COLOR_PREFERENCE_KO.get(prefs.get("color_preference"), "-")

        final_metas = "".join([
            _meta("예산 설정",  budget_text, small=True),
            _meta("RGB 선호도", rgb_text,    small=True),
            _meta("색상 선호도", color_text,  small=True),
        ])

        proc_categories = prefs.get("unknown_process_categories") or {}
        proc_tags = "".join(
            f'<span class="tag" style="color:#A6AEC8;background:#1E2433;border-color:#2D3748">'
            f'{html.escape(name)} · {_PROCESS_CATEGORY_KO.get(cat, cat)}</span>'
            for name, cat in proc_categories.items()
        )
        proc_block = (
            f'<div style="font-size:11px;color:#A6AEC8;margin:14px 0 8px;text-transform:uppercase;letter-spacing:0.8px">미분류 프로그램 분류</div>'
            f'<div style="display:flex;flex-wrap:wrap;gap:8px">{proc_tags}</div>'
        ) if proc_tags else ""

        final_block = f"""
  <div style="margin-top:22px">
    <div style="font-size:11px;color:#A6AEC8;margin-bottom:8px;text-transform:uppercase;letter-spacing:0.8px">최종 입력 — 분석 종료 후 답변</div>
    <div class="meta-grid">{final_metas}</div>
    {proc_block}
  </div>"""
    else:
        final_block = """
  <div style="margin-top:22px">
    <div style="font-size:11px;color:#A6AEC8;margin-bottom:8px;text-transform:uppercase;letter-spacing:0.8px">최종 입력 — 분석 종료 후 답변</div>
    <p style="color:#A6AEC8;font-size:13px">기록된 답변이 없습니다.</p>
  </div>"""

    hw_block = _hw_spec_block(data.get("hw_info") or {})

    return f"""
<div class="card">
  <h2>사용자 입력 정보</h2>
  <div>
    <div style="font-size:11px;color:#A6AEC8;margin-bottom:8px;text-transform:uppercase;letter-spacing:0.8px">최초 입력 — 분석 시작 전 설정</div>
    <div class="meta-grid">{initial_metas}</div>
    <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:12px">{part_tags}</div>
  </div>
  {final_block}
  {hw_block}
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
      <p style="color:#A6AEC8;font-size:13px;line-height:2.0">
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
            f'<td style="padding:11px 10px;color:#A6AEC8;font-size:13px;font-family:monospace">{score:.3f}</td>'
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

    if part in ("CPU", "GPU") and target_tier is not None:
        if current_tier is not None:
            inner = f"<strong>Tier {current_tier} → Tier {target_tier}</strong>"
        else:
            inner = f"목표 <strong>Tier {target_tier}</strong>"
        return f'<div class="rec-spec">{inner}</div>'

    note = html.escape(target_spec.get("note", ""))
    if part == "PSU":
        label    = html.escape(target_spec.get("recommended_efficiency", ""))
        min_watt = target_spec.get("min_wattage")
        if label:
            watt_str = f"<strong>{min_watt}W</strong> 이상, " if min_watt else ""
            return (
                f'<div class="rec-spec">'
                f'권장 용량: {watt_str}효율 등급 <strong>80+ {label}</strong>'
                + (f'<br><span style="font-size:11px">{note}</span>' if note else "")
                + "</div>"
            )
    if part == "Motherboard":
        socket = html.escape(target_spec.get("socket", ""))
        if socket:
            inner = f"소켓: <strong>{socket}</strong>"
            if note:
                inner += f'<br><span style="font-size:11px">{note}</span>'
            return f'<div class="rec-spec">{inner}</div>'
    if note:
        return f'<div class="rec-spec">{note}</div>'
    return ""


def _rec_budget_guide_html(item: dict, user_budget: int | None) -> str:
    """후보 가격을 바탕으로 권장 예산 가이드를 표시하고, 사용자가 입력한 예산이
    부족한 경우 경고를 함께 보여준다."""
    candidates = item.get("candidates") or []
    prices = [c.get("price_krw") for c in candidates if isinstance(c.get("price_krw"), int)]
    if not prices:
        return ""

    min_price = min(prices)
    guide = (
        f'<div class="rec-spec" style="margin-top:0">'
        f'권장 예산 가이드 — 이 등급의 업그레이드를 만족스럽게 진행하려면 '
        f'<strong>최소 약 {min_price:,} 원</strong> 이상을 고려하세요.'
        f"</div>"
    )

    if isinstance(user_budget, int) and user_budget > 0 and user_budget < min_price:
        guide += (
            f'<div class="rec-spec" style="margin-top:0;color:#FF8C42;background:rgba(255,140,66,0.08)">'
            f'⚠ 입력한 예산({user_budget:,} 원)으로는 이 부품의 추천 후보를 구매하기에 부족할 수 있습니다. '
            f'예산을 조정하거나 더 낮은 등급의 제품을 고려해보세요.'
            f"</div>"
        )

    return guide


def _rec_candidates_html(item: dict) -> str:
    part        = item["part"]
    candidates  = item.get("candidates") or []
    search_query = html.escape(item.get("search_query") or "")

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

        spec_suffix = ""
        if part == "Motherboard":
            spec_parts = []
            if c.get("chipset"):
                spec_parts.append(html.escape(c["chipset"]))
            if c.get("form_factor"):
                spec_parts.append(html.escape(c["form_factor"]))
            m2 = c.get("m2_interfaces") or []
            if m2:
                spec_parts.append(f"M.2×{len(m2)}")
            if spec_parts:
                spec_suffix = (
                    f' <span style="color:#A6AEC8;font-size:11px">'
                    f'[{" | ".join(spec_parts)}]</span>'
                )

        rows += (
            f'<div class="rec-cand-row">'
            f'<span class="rec-cand-name">{name}{spec_suffix}</span>'
            f'<span class="rec-cand-price">{price}</span>'
            f'{link}'
            f"</div>"
        )

    return f'<div class="rec-cand-title">후보 제품</div>{rows}'


def _section_recommendations(items: list[dict], user_preferences: dict | None = None) -> str:
    prefs       = user_preferences or {}
    budget_mode = prefs.get("budget_mode", "recommended")
    budgets     = prefs.get("budgets") or {}

    if not items:
        return """
<div class="card">
  <h2>하드웨어 업그레이드 추천</h2>
  <div class="info-banner" style="color:#A6AEC8;background:rgba(166,174,200,0.06);border-color:rgba(166,174,200,0.2)">
    현재 사용 패턴에서 즉각적인 업그레이드가 권고되는 부품이 없습니다.
  </div>
</div>"""

    cards = ""
    for item in items:
        part      = item["part"]
        grade     = item.get("grade", "unknown")
        priority  = item.get("priority", 0.0)
        reason    = html.escape(item.get("reason", ""))
        is_psu    = (part == "PSU")
        is_board  = (part == "Motherboard")
        part_label = html.escape(_PART_KO.get(part, part))

        if is_psu:
            grade_tag     = '<span class="tag" style="color:#A6AEC8;background:#1E2433;border-color:#2D3748">의존성</span>'
            priority_html = ""
        elif is_board:
            grade_tag = (
                '<span class="tag" style="color:#00D4AA;background:rgba(0,212,170,0.1);'
                'border-color:rgba(0,212,170,0.3)">호환 필요</span>'
            )
            bar_pct       = min(int(priority / 1.5 * 100), 100)
            priority_html = (
                f'<div class="rec-priority">'
                f'<div class="rec-bar-bg">'
                f'<div class="rec-bar-fill" style="width:{bar_pct}%"></div>'
                f"</div>"
                f'<span class="rec-pct">{bar_pct}%</span>'
                f"</div>"
            )
        else:
            grade_tag     = _tag(grade)
            bar_pct       = min(int(priority / 1.5 * 100), 100)
            priority_html = (
                f'<div class="rec-priority">'
                f'<div class="rec-bar-bg">'
                f'<div class="rec-bar-fill" style="width:{bar_pct}%"></div>'
                f"</div>"
                f'<span class="rec-pct">{bar_pct}%</span>'
                f"</div>"
            )

        part_budget = budgets.get(part) if budget_mode == "custom" else None
        spec_html   = _rec_spec_html(item)
        budget_html = _rec_budget_guide_html(item, part_budget)
        cand_html   = _rec_candidates_html(item)
        card_class  = "rec-card rec-psu" if is_psu else "rec-card"

        cards += (
            f'<div class="{card_class}">'
            f'<div class="rec-header">'
            f'<span class="rec-part">{part_label}</span>'
            f'{grade_tag}'
            f'{priority_html}'
            f"</div>"
            f'<p class="rec-reason">{reason}</p>'
            f'{spec_html}'
            f'{budget_html}'
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
        + _section_user_input(report_data)
        + _section_resource(charts)
        + _section_pattern(charts)
        + _section_disk_process(charts)
        + _section_scores(report_data, charts)
        + _section_recommendations(report_data.get("recommendations") or [], report_data.get("user_preferences"))
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
