import math
import threading
import tkinter as tk
from tkinter import messagebox

from src.consent import (
  CONSENT_TITLE,
  CONSENT_BODY,
  DECLINE_MESSAGE,
  build_consent_state,
  record_agreement,
  record_decline,
)
from src.settings import (
  KNOWLEDGE_LEVELS,
  KNOWLEDGE_LEVEL_LABELS,
  ANALYSIS_DAYS_MIN,
  ANALYSIS_DAYS_MAX,
  PARTS,
  PART_OPTIONS,
  PART_OPTIONS_BASIC,
  PART_OPTION_LABELS,
  PART_DESCRIPTIONS,
  OWNED_CAPABLE_PARTS,
  build_settings_state,
)
from src.hardware import get_hardware_info
from src.storage import save_user_profile, save_user_preferences, delete_all_monitoring_data, read_user_profile, init_log_line_count, get_log_line_count
from src.validators import validate_analysis_days, validate_parts_not_all_keep, validate_owned_parts_selected
from src.recommendation.chipset_tier_mapper import search_passmark_candidates
from src.monitor import start_monitoring_loop, stop_monitoring_loop, is_monitoring_running
from src.background import join_background_task
from src.config import USAGE_LOG_PATH, ANALYSIS_DIR
from src.startup_state import StartupState
from src.normalization.core import read_jsonl
from src.analysis.resource_usage import analyze_resource_usage
from src.analysis.usage_pattern_summary import create_usage_pattern_summary, save_normalized_usage
from src.analysis.disk_usage import analyze_disk_usage
from src.analysis.process_usage import analyze_process_usage
from src.analysis.user_type import classify_user_type
from src.analysis.score_cpu import score_cpu
from src.analysis.score_ram import score_ram
from src.analysis.score_gpu_vram import score_gpu_vram
from src.analysis.score_ssd import score_ssd
from src.analysis.score_hdd import score_hdd
from src.analysis.score_psu import score_psu
from src.startup_registry import register_startup, unregister_startup
from src.version import __version__

SETTINGS_TITLE = "BuildSense - 사용자 설정"

# ── 다크 UI 공통 상수 / 유틸 ──────────────────────────────────────

_PART_ICONS = {
  "CPU":      "⬡",
  "GPU":      "⊡",
  "RAM":      "▦",
  "SSD":      "⊞",
  "HDD":      "◫",
  "메인보드": "⌬",
  "파워":     "⚡",
}

_CONSENT_ITEMS = [
  ("⬡", "CPU",                "사용률"),
  ("▦", "RAM",                "사용량"),
  ("⊡", "NVIDIA GPU",         "사용률"),
  ("⊟", "VRAM",               "사용량"),
  ("☰", "실행 중인 프로세스", "목록"),
  ("◷", "시스템 가동",        "시간"),
  ("◈", "현재 하드웨어",      "정보"),
]


def _rrect(c, x1, y1, x2, y2, r, fill, tag=""):
  """Canvas에 둥근 모서리 사각형을 그린다."""
  kw = dict(fill=fill, outline=fill)
  if tag:
    kw["tags"] = tag
  c.create_arc(x1,     y1,     x1+2*r, y1+2*r, start=90,  extent=90,  **kw)
  c.create_arc(x2-2*r, y1,     x2,     y1+2*r, start=0,   extent=90,  **kw)
  c.create_arc(x2-2*r, y2-2*r, x2,     y2,     start=270, extent=90,  **kw)
  c.create_arc(x1,     y2-2*r, x1+2*r, y2,     start=180, extent=90,  **kw)
  c.create_rectangle(x1+r, y1,   x2-r, y2,   **kw)
  c.create_rectangle(x1,   y1+r, x2,   y2-r, **kw)


def _hex_mix(c1: str, c2: str, t: float) -> str:
  """두 hex 색상을 t 비율로 혼합한다 (0=c1, 1=c2)."""
  r1,g1,b1 = int(c1[1:3],16), int(c1[3:5],16), int(c1[5:7],16)
  r2,g2,b2 = int(c2[1:3],16), int(c2[3:5],16), int(c2[5:7],16)
  return "#{:02x}{:02x}{:02x}".format(
    int(r1+(r2-r1)*t), int(g1+(g2-g1)*t), int(b1+(b2-b1)*t)
  )


# ── 다크 테마 색상 팔레트 (Figma 기반, 전 화면 공통) ──────────────────
BG       = "#1A1F2E"
CARD     = "#1E2438"
TEAL     = "#00C9A7"
BLUE     = "#4C7DFF"
RED      = "#E05252"
WHITE    = "#E8EAF0"
GRAY     = "#9AA1C2"
INFO_BG  = "#0D2820"
WARN_BG  = "#2B1515"
DIVIDER  = "#252D45"
ICON_BG  = "#162840"
BADGE_BG = "#1E3A6B"
BADGE_FG = "#7FAEFF"
BTN_EXIT = "#7C1F1F"
BTN_CONT_OFF = "#252D45"
BTN_CONT_ON  = "#1A7A50"
BTN_START    = "#15B36B"
DOT_GRN  = "#00C96E"
P        = 28   # 좌우 패딩

_PILL_W, _PILL_H = 160, 44


def _pill(parent, text, normal_bg, fg, width=_PILL_W, height=_PILL_H, font_size=10, bg=BG):
  """알약형 캔버스 버튼.
  c._draw(bg)로 다시 그리고, c._fg[0]/c._text[0]를 바꾼 뒤 c._draw()를 호출하면 갱신된다."""
  c = tk.Canvas(parent, width=width, height=height, bg=bg, highlightthickness=0, cursor="hand2")
  _fg = [fg]
  _text = [text]

  def draw(bg=None):
    c.delete("all")
    _rrect(c, 0, 0, width, height, height // 2, bg or c._normal)
    c.create_text(width // 2, height // 2, text=_text[0], fill=_fg[0], font=("Segoe UI", font_size, "bold"))

  c._draw   = draw
  c._fg     = _fg
  c._text   = _text
  c._normal = normal_bg
  draw()
  c.bind("<Enter>", lambda e: draw(_hex_mix(normal_bg, "#ffffff", 0.12)))
  c.bind("<Leave>", lambda e: draw())
  return c


def _make_toggle(parent, options, variable, on_change=None,
                 seg_w=104, seg_h=32, gap=8, sel_color=BLUE, bg=BG):
  """알약형 단일 선택 토글 그룹. row.set_enabled(bool)/row.redraw()로 제어 가능."""
  row = tk.Frame(parent, bg=bg)
  canvases = []
  _enabled = [True]

  def _redraw():
    cur = variable.get()
    for c, (label, value) in zip(canvases, options):
      sel = (value == cur)
      if not _enabled[0]:
        bg_c = _hex_mix(sel_color if sel else DIVIDER, BG, 0.55)
        fg_c = _hex_mix(WHITE if sel else GRAY, BG, 0.45)
      else:
        bg_c = sel_color if sel else DIVIDER
        fg_c = WHITE if sel else GRAY
      c.delete("all")
      _rrect(c, 0, 0, seg_w, seg_h, seg_h // 2, bg_c)
      c.create_text(seg_w // 2, seg_h // 2, text=label, fill=fg_c,
                    font=("Segoe UI", 9, "bold" if sel else "normal"))

  for label, value in options:
    c = tk.Canvas(row, width=seg_w, height=seg_h, bg=bg,
                  highlightthickness=0, cursor="hand2")
    c.pack(side=tk.LEFT, padx=(0, gap))

    def _click(e, v=value):
      if not _enabled[0]:
        return
      variable.set(v)
      _redraw()
      if on_change:
        on_change(v)

    c.bind("<Button-1>", _click)
    canvases.append(c)

  def _set_enabled(en):
    _enabled[0] = en
    for c in canvases:
      c.configure(cursor="hand2" if en else "arrow")
    _redraw()

  _redraw()
  row.set_enabled = _set_enabled
  row.redraw = _redraw
  return row


def _badge(parent, text, bg=BADGE_BG, fg=BADGE_FG):
  """작은 알약형 라벨 (캔버스, 클릭 불가)."""
  font = ("Segoe UI", 9, "bold")
  w = 24 + len(text) * 8
  h = 26
  c = tk.Canvas(parent, width=w, height=h, bg=BG, highlightthickness=0)
  _rrect(c, 0, 0, w, h, h // 2, bg)
  c.create_text(w // 2, h // 2, text=text, fill=fg, font=font)
  return c


class BuildSenseApp:
  def __init__(self, startup_state: StartupState = StartupState.FRESH):
    self.root = tk.Tk()
    self.consent_state = build_consent_state()
    self.settings_state = build_settings_state()
    self._hardware_info = {}
    self._knowledge_var = None
    self._days_var = None
    self._part_vars = {}
    self._part_hw_frames = {}
    self._part_radio_widgets = {}
    self._part_desc_labels = {}
    self._part_owned_frames = {}
    self._owned_query_vars = {}
    self._owned_results_frames = {}
    self._owned_selected_labels = {}
    self._owned_candidate_vars = {}
    self._report_path: str | None = None

    if startup_state == StartupState.RESUME:
      self._on_resume()   # KAN-62: feature-resume-monitoring-after-reboot
    elif startup_state == StartupState.ANALYZE:
      self._on_analyze()  # KAN-63: feature-trigger-analysis-pipeline
    else:
      self._show_consent_screen()

  def run(self):
    self.root.mainloop()

  def _on_resume(self):
    profile = read_user_profile()
    if profile is None:
      self._show_consent_screen()
      return

    self.settings_state["knowledge_level"] = profile.get("knowledge_level", "intermediate")
    self.settings_state["analysis_days"]   = profile.get("analysis_days", 7)
    self.settings_state["parts"]           = profile.get("parts", self.settings_state["parts"])

    init_log_line_count()
    start_monitoring_loop()
    register_startup()
    self._show_monitoring_screen()

  def _on_analyze(self):
    self._unknown_procs: list[dict] = []
    self._show_analysis_notification_screen()

  def _show_analysis_notification_screen(self):
    self._clear_window()
    self.root.title("BuildSense - 분석 기간 종료")
    self.root.resizable(False, False)
    self._center_window(480, 320)
    self.root.configure(bg=BG)

    body = tk.Frame(self.root, bg=BG, padx=36, pady=36)
    body.pack(fill=tk.BOTH, expand=True)

    icon_c = tk.Canvas(body, width=56, height=56, bg=BG, highlightthickness=0)
    icon_c.pack(pady=(4, 18))
    _rrect(icon_c, 0, 0, 56, 56, 14, ICON_BG)
    icon_c.create_text(28, 28, text="◷", fill=TEAL, font=("Segoe UI Symbol", 22))

    tk.Label(body, text="모니터링 기간이 종료되었습니다", fg=WHITE, bg=BG,
             font=("Segoe UI", 13, "bold")).pack(pady=(0, 8))

    tk.Label(body, text="추가 정보를 입력하면 더 정확한 업그레이드 추천을 받을 수 있습니다.",
             fg=GRAY, bg=BG, font=("Segoe UI", 10), wraplength=380,
             justify=tk.CENTER).pack(pady=(0, 26))

    btn_row = tk.Frame(body, bg=BG)
    btn_row.pack()

    self._extra_info_btn = _pill(btn_row, "추가 정보 입력 (확인 중...)", BTN_CONT_OFF, "#4A5070", width=220)
    self._extra_info_btn.pack(side=tk.LEFT, padx=(0, 10))
    self._extra_info_btn.configure(cursor="arrow")
    self._extra_info_btn.bind("<Enter>", lambda e: None)
    self._extra_info_btn.bind("<Leave>", lambda e: None)

    skip_btn = _pill(btn_row, "바로 분석하기", DIVIDER, GRAY, width=140)
    skip_btn.pack(side=tk.LEFT)
    skip_btn.bind("<Button-1>", lambda e: self._show_analyzing_screen())

    def _detect():
      from src.normalization.core import read_jsonl
      from src.recommendation.user_input_dialog import find_impactful_unknown_processes
      try:
        logs = read_jsonl(USAGE_LOG_PATH)
        procs = find_impactful_unknown_processes(logs)
      except Exception:
        procs = []
      if self.root.winfo_exists():
        self.root.after(0, lambda p=procs: self._on_unknown_procs_ready(p))

    threading.Thread(target=_detect, daemon=True).start()

  def _on_unknown_procs_ready(self, procs: list[dict]):
    self._unknown_procs = procs
    if not self.root.winfo_exists() or not self._extra_info_btn.winfo_exists():
      return
    try:
      suffix = f" ({len(procs)}개 미분류 포함)" if procs else ""
      btn = self._extra_info_btn
      btn._text[0] = f"추가 정보 입력{suffix}"
      btn._fg[0]   = WHITE
      btn._normal  = BTN_CONT_ON
      btn._draw(BTN_CONT_ON)
      btn.bind("<Enter>", lambda e: btn._draw(_hex_mix(BTN_CONT_ON, "#ffffff", 0.12)))
      btn.bind("<Leave>", lambda e: btn._draw())
      btn.bind("<Button-1>", lambda e: self._on_open_preference_dialog())
      btn.configure(cursor="hand2")
    except tk.TclError:
      pass

  def _on_open_preference_dialog(self):
    from src.recommendation.user_input_dialog import UserPreferenceDialog
    UserPreferenceDialog(
      parent=self.root,
      unknown_procs=self._unknown_procs,
      on_confirm=self._on_preferences_confirmed,
      on_cancel=self._show_analyzing_screen,
      knowledge_level=self.settings_state.get("knowledge_level"),
      parts=self.settings_state.get("parts", {}),
    )

  def _on_preferences_confirmed(self, prefs: dict):
    try:
      save_user_preferences(prefs)
    except Exception:
      pass
    self._show_analyzing_screen()

  def _show_analyzing_screen(self):
    self._clear_window()
    self.root.title("BuildSense - 분석 중")
    self.root.resizable(False, False)
    self._center_window(380, 280)
    self.root.configure(bg=BG)

    body = tk.Frame(self.root, bg=BG, padx=32, pady=36)
    body.pack(fill=tk.BOTH, expand=True)

    SPIN = 76
    spin_c = tk.Canvas(body, width=SPIN, height=SPIN, bg=BG, highlightthickness=0)
    spin_c.pack(pady=(8, 22))

    _SPIN_COLORS = [BLUE, "#2FA0E0", TEAL, "#1FD9A0"]
    _angle = [0]

    def _draw_spinner():
      if not spin_c.winfo_exists():
        return
      spin_c.delete("all")
      cx = cy = SPIN / 2
      r = SPIN / 2 - 5
      n = len(_SPIN_COLORS)
      for i, color in enumerate(_SPIN_COLORS):
        start = _angle[0] + i * (300 / n)
        spin_c.create_arc(cx - r, cy - r, cx + r, cy + r,
                          start=start, extent=300 / n - 6,
                          style=tk.ARC, outline=color, width=4)
      _angle[0] = (_angle[0] + 7) % 360
      self.root.after(40, _draw_spinner)

    _draw_spinner()

    tk.Label(body, text="사용 데이터를 분석하고 있습니다", fg=WHITE, bg=BG,
             font=("Segoe UI", 12, "bold")).pack(pady=(0, 6))
    tk.Label(body, text="잠시만 기다려 주세요...", fg=GRAY, bg=BG,
             font=("Segoe UI", 9)).pack()

    self.root.update()

    def _run():
      try:
        logs = read_jsonl(USAGE_LOG_PATH)
        result = {
          "resource_usage": analyze_resource_usage(logs),
          "usage_pattern":  create_usage_pattern_summary(logs),
          "disk_usage":     analyze_disk_usage(logs),
          "process_usage":  analyze_process_usage(logs),
        }
        result["scores"] = {
          "user_classification": classify_user_type(result, len(logs)),
          "cpu": score_cpu(result["resource_usage"]["cpu"]),
          "ram": score_ram(result["resource_usage"]["ram"]),
          "gpu_vram": score_gpu_vram(result["resource_usage"]["gpu"], result["resource_usage"]["vram"]),
          "ssd": score_ssd(result["disk_usage"]),
          "hdd": score_hdd(result["disk_usage"]),
          "psu": score_psu(result["usage_pattern"]),
        }
        save_normalized_usage(result)

        # 로그 삭제 전에 보고서 생성 (삭제 후에는 load_usage_logs 실패)
        try:
          from src.report.report_generator import generate_report
          report_path = generate_report(hw_info=self._hardware_info)
          self._report_path = str(report_path)
        except Exception:
          self._report_path = None

        delete_all_monitoring_data()
        unregister_startup()
        if self.root.winfo_exists():
          self.root.after(0, self._show_analysis_complete_screen)
      except Exception as e:
        if self.root.winfo_exists():
          self.root.after(0, lambda err=str(e): self._show_analysis_error_screen(err))

    threading.Thread(target=_run, daemon=True).start()

  def _show_analysis_complete_screen(self):
    self._clear_window()
    self.root.title("BuildSense - 분석 완료")
    self._center_window(440, 360)
    self.root.configure(bg=BG)

    body = tk.Frame(self.root, bg=BG, padx=36, pady=36)
    body.pack(fill=tk.BOTH, expand=True)

    icon_c = tk.Canvas(body, width=58, height=58, bg=BG, highlightthickness=0)
    icon_c.pack(pady=(4, 18))
    _rrect(icon_c, 0, 0, 58, 58, 14, INFO_BG)
    icon_c.create_text(29, 29, text="✓", fill=DOT_GRN, font=("Segoe UI", 22, "bold"))

    tk.Label(body, text="분석이 완료되었습니다", fg=WHITE, bg=BG,
             font=("Segoe UI", 13, "bold")).pack(pady=(0, 8))

    if self._report_path:
      tk.Label(body, text="보고서가 브라우저에서 열렸습니다.", fg=GRAY, bg=BG,
               font=("Segoe UI", 9)).pack(pady=(0, 22))

      def _reopen():
        from pathlib import Path
        from src.report.report_generator import _open_in_browser
        _open_in_browser(Path(self._report_path))

      reopen_btn = _pill(body, "보고서 다시 열기", DIVIDER, WHITE, width=180)
      reopen_btn.pack(pady=(0, 10))
      reopen_btn.bind("<Button-1>", lambda e: _reopen())
    else:
      tk.Label(body, text=f"결과 저장 경로:\n{ANALYSIS_DIR / 'normalized_usage.json'}",
               fg=GRAY, bg=BG, font=("Segoe UI", 9), wraplength=380,
               justify=tk.CENTER).pack(pady=(0, 22))

    ok_btn = _pill(body, "확인", BTN_CONT_ON, WHITE, width=140)
    ok_btn.pack()
    ok_btn.bind("<Button-1>", lambda e: self.root.destroy())

  def _show_analysis_error_screen(self, error_message: str):
    self._clear_window()
    self.root.title("BuildSense - 분석 오류")
    self._center_window(440, 300)
    self.root.configure(bg=BG)

    body = tk.Frame(self.root, bg=BG, padx=36, pady=36)
    body.pack(fill=tk.BOTH, expand=True)

    icon_c = tk.Canvas(body, width=58, height=58, bg=BG, highlightthickness=0)
    icon_c.pack(pady=(4, 18))
    _rrect(icon_c, 0, 0, 58, 58, 14, WARN_BG)
    icon_c.create_text(29, 29, text="!", fill=RED, font=("Segoe UI", 20, "bold"))

    tk.Label(body, text="분석 중 오류가 발생했습니다", fg=RED, bg=BG,
             font=("Segoe UI", 13, "bold")).pack(pady=(0, 10))

    err_card = tk.Frame(body, bg=CARD, padx=16, pady=12)
    err_card.pack(fill=tk.X, pady=(0, 22))
    tk.Label(err_card, text=error_message, fg=GRAY, bg=CARD,
             font=("Segoe UI", 9), wraplength=360, justify=tk.CENTER).pack()

    ok_btn = _pill(body, "확인", DIVIDER, WHITE, width=140)
    ok_btn.pack()
    ok_btn.bind("<Button-1>", lambda e: self.root.destroy())

  # ------------------------------------------------------------------
  # 화면 전환
  # ------------------------------------------------------------------

  def _show_consent_screen(self):
    self._clear_window()
    self.root.title(CONSENT_TITLE)
    self.root.resizable(False, False)
    self._center_window(580, 810)

    self.root.configure(bg=BG)

    # ── 스크롤 래퍼 ──────────────────────────────────────────────
    outer = tk.Frame(self.root, bg=BG)
    outer.pack(fill=tk.BOTH, expand=True)

    scr = tk.Canvas(outer, bg=BG, highlightthickness=0)
    scr.pack(fill=tk.BOTH, expand=True)

    body = tk.Frame(scr, bg=BG)
    win_id = scr.create_window((0, 0), anchor="nw", window=body)
    scr.bind("<Configure>", lambda e: scr.itemconfig(win_id, width=e.width))
    body.bind("<Configure>", lambda e: scr.configure(scrollregion=scr.bbox("all")))
    scr.bind("<Enter>", lambda e: scr.bind_all(
      "<MouseWheel>", lambda ev: scr.yview_scroll(int(-1 * (ev.delta / 120)), "units")))
    scr.bind("<Leave>", lambda e: scr.unbind_all("<MouseWheel>"))

    # ─── 1. 헤더 ─────────────────────────────────────────────────
    hdr = tk.Frame(body, bg=BG, padx=P, pady=20)
    hdr.pack(fill=tk.X)

    icon_c = tk.Canvas(hdr, width=52, height=52, bg=BG, highlightthickness=0)
    icon_c.pack(side=tk.LEFT, padx=(0, 16), anchor="n")
    _rrect(icon_c, 0, 0, 52, 52, 12, ICON_BG)
    icon_c.create_text(26, 26, text="⊛", fill=TEAL, font=("Segoe UI Symbol", 20))

    title_col = tk.Frame(hdr, bg=BG)
    title_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    bc = tk.Frame(title_col, bg=BG)
    bc.pack(anchor="w")
    tk.Label(bc, text="BUILDSENSE", fg=TEAL, bg=BG,
             font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT)
    tk.Label(bc, text="  ·  데이터 수집 동의", fg=GRAY, bg=BG,
             font=("Segoe UI", 8)).pack(side=tk.LEFT)
    tk.Label(bc, text=f"  v{__version__}", fg=GRAY, bg=BG,
             font=("Segoe UI", 8)).pack(side=tk.LEFT)

    tk.Label(title_col,
             text="맞춤형 하드웨어 추천을 위한\nPC 사용 데이터 수집",
             fg=WHITE, bg=BG, font=("Segoe UI", 15, "bold"),
             justify=tk.LEFT, anchor="w").pack(anchor="w", pady=(6, 0))

    # ─── 2. 설명 텍스트 ──────────────────────────────────────────
    desc = tk.Frame(body, bg=BG, padx=P)
    desc.pack(fill=tk.X)
    tk.Label(desc,
             text="BuildSense는 맞춤형 하드웨어 추천 보고서를 생성하기 위해 PC 사용 데이터를 수집합니다.",
             fg=GRAY, bg=BG, font=("Segoe UI", 10),
             wraplength=520, justify=tk.LEFT, anchor="w").pack(fill=tk.X, pady=(0, 14))

    # ─── 3. 정보 박스 (녹색 라운드) ──────────────────────────────
    INFO_H = 66
    info_c = tk.Canvas(body, height=INFO_H, bg=BG, highlightthickness=0)
    info_c.pack(fill=tk.X, padx=P, pady=(0, 16))

    def _draw_info(e=None):
      w = info_c.winfo_width()
      if w < 10:
        return
      info_c.delete("all")
      _rrect(info_c, 0, 0, w, INFO_H, 10, INFO_BG)
      info_c.create_oval(16, 29, 26, 39, fill=DOT_GRN, outline="")
      info_c.create_text(38, 22, anchor="w",
                         text="모든 데이터는 이 기기에만 저장됩니다.",
                         fill=TEAL, font=("Segoe UI", 10, "bold"))
      info_c.create_text(38, 46, anchor="w",
                         text="외부 서버로 전송되는 정보는 없습니다.",
                         fill=GRAY, font=("Segoe UI", 9))

    info_c.bind("<Configure>", lambda e: _draw_info())
    body.after(50, _draw_info)

    # ─── 4. 섹션 레이블 ──────────────────────────────────────────
    sec = tk.Frame(body, bg=BG, padx=P)
    sec.pack(fill=tk.X)
    tk.Label(sec, text="분석  기간  동안  수집되는  데이터",
             fg=GRAY, bg=BG, font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 6))

    # ─── 5. 데이터 리스트 박스 ────────────────────────────────────
    ITEM_H = 42
    LIST_H = len(_CONSENT_ITEMS) * (ITEM_H + 1) + 24

    list_c = tk.Canvas(body, height=LIST_H, bg=BG, highlightthickness=0)
    list_c.pack(fill=tk.X, padx=P, pady=(0, 14))

    row_wins: list[int] = []
    for i, (icon, name, suffix) in enumerate(_CONSENT_ITEMS):
      rf = tk.Frame(list_c, bg=CARD)
      tk.Label(rf, text=icon, fg=TEAL, bg=CARD,
               font=("Segoe UI Symbol", 11), width=2,
               anchor="center").pack(side=tk.LEFT, padx=(14, 8))
      tk.Label(rf, text=name, fg=WHITE, bg=CARD,
               font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
      tk.Label(rf, text=f"  {suffix}", fg=GRAY, bg=CARD,
               font=("Segoe UI", 10)).pack(side=tk.LEFT)
      row_wins.append(list_c.create_window(0, 0, anchor="nw", window=rf))

    div_ids: list[int] = []

    def _layout_list(e=None):
      w = list_c.winfo_width()
      if w < 10:
        return
      list_c.delete("bg")
      for d in div_ids:
        list_c.delete(d)
      div_ids.clear()
      _rrect(list_c, 0, 0, w, LIST_H, 10, CARD, tag="bg")
      list_c.tag_lower("bg")
      for i, win_id in enumerate(row_wins):
        y = 12 + i * (ITEM_H + 1)
        list_c.coords(win_id, 0, y)
        list_c.itemconfig(win_id, width=w, height=ITEM_H)
        if i < len(row_wins) - 1:
          div_ids.append(list_c.create_line(14, y + ITEM_H, w - 14, y + ITEM_H, fill=DIVIDER))

    list_c.bind("<Configure>", lambda e: _layout_list())
    body.after(80, _layout_list)

    # ─── 6. 경고 박스 (빨간 라운드) ──────────────────────────────
    WARN_H = 62
    warn_c = tk.Canvas(body, height=WARN_H, bg=BG, highlightthickness=0)
    warn_c.pack(fill=tk.X, padx=P, pady=(0, 14))

    def _draw_warn(e=None):
      w = warn_c.winfo_width()
      if w < 10:
        return
      warn_c.delete("all")
      _rrect(warn_c, 0, 0, w, WARN_H, 10, WARN_BG)
      warn_c.create_text(16, WARN_H // 2, anchor="w",
                         text="언제든지 거부할 수 있습니다. 거부하면 프로그램이 종료되며, 모든 데이터가 삭제됩니다.",
                         fill=RED, font=("Segoe UI", 9, "bold"),
                         width=w - 32, justify=tk.LEFT)

    warn_c.bind("<Configure>", lambda e: _draw_warn())
    body.after(80, _draw_warn)

    # ─── 7. 동의 체크박스 ────────────────────────────────────────
    agree_var = tk.BooleanVar(value=False)

    chk_row = tk.Frame(body, bg=BG, padx=P)
    chk_row.pack(fill=tk.X, pady=(0, 10))

    chk_c = tk.Canvas(chk_row, width=24, height=24, bg=BG, highlightthickness=0, cursor="hand2")
    chk_c.pack(side=tk.LEFT, padx=(0, 10), pady=4)

    def _draw_chk():
      chk_c.delete("all")
      if agree_var.get():
        chk_c.create_oval(1, 1, 23, 23, fill=TEAL, outline=TEAL)
        chk_c.create_text(12, 12, text="✓", fill=BG, font=("Segoe UI", 10, "bold"))
      else:
        chk_c.create_oval(1, 1, 23, 23, fill="", outline=GRAY, width=2)

    _draw_chk()

    chk_lbl = tk.Frame(chk_row, bg=BG)
    chk_lbl.pack(side=tk.LEFT, fill=tk.BOTH)
    tk.Label(chk_lbl, text="수집 항목과 이용 목적을 확인하였으며, 이에 ",
             fg=GRAY, bg=BG, font=("Segoe UI", 10)).pack(side=tk.LEFT)
    tk.Label(chk_lbl, text="동의합니다",
             fg=WHITE, bg=BG, font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)

    # ─── 8. 버튼 행 ──────────────────────────────────────────────
    btn_row = tk.Frame(body, bg=BG, padx=P)
    btn_row.pack(fill=tk.X, pady=(0, 22))

    # 계속 버튼 (비활성 상태로 시작) — 가장 오른쪽
    cont_btn = _pill(btn_row, "계속  →", BTN_CONT_OFF, "#4A5070")
    cont_btn.pack(side=tk.RIGHT)

    # 종료 버튼 — 계속 버튼 왼쪽
    exit_btn = _pill(btn_row, "×  종료", BTN_EXIT, WHITE)
    exit_btn.pack(side=tk.RIGHT, padx=(0, 8))
    exit_btn.bind("<Button-1>", lambda e: self._on_decline())
    _cont_enabled = [False]

    def _on_check_click(e=None):
      agree_var.set(not agree_var.get())
      _draw_chk()
      if agree_var.get():
        _cont_enabled[0] = True
        cont_btn._fg[0]  = WHITE       # 텍스트를 흰색으로 전환
        cont_btn._normal = BTN_CONT_ON
        cont_btn._draw(BTN_CONT_ON)
        cont_btn.bind("<Enter>", lambda e: cont_btn._draw(_hex_mix(BTN_CONT_ON, "#ffffff", 0.12)))
        cont_btn.bind("<Leave>", lambda e: cont_btn._draw(BTN_CONT_ON))
        cont_btn.bind("<Button-1>", lambda e: self._on_agree())
        cont_btn.configure(cursor="hand2")
      else:
        _cont_enabled[0] = False
        cont_btn._fg[0]  = "#4A5070"  # 텍스트를 다시 어두운 색으로
        cont_btn._normal = BTN_CONT_OFF
        cont_btn._draw(BTN_CONT_OFF)
        cont_btn.bind("<Enter>", lambda e: None)
        cont_btn.bind("<Leave>", lambda e: None)
        cont_btn.bind("<Button-1>", lambda e: None)
        cont_btn.configure(cursor="arrow")

    chk_c.bind("<Button-1>", _on_check_click)
    for w in (chk_lbl,) + tuple(chk_lbl.winfo_children()):
      try:
        w.bind("<Button-1>", _on_check_click)
      except Exception:
        pass

  def _show_loading_screen(self):
    self._clear_window()
    self.root.title("BuildSense")
    self.root.resizable(False, False)
    self._center_window(420, 380)
    self.root.configure(bg=BG)

    frame = tk.Frame(self.root, bg=BG, padx=32, pady=36)
    frame.pack(fill=tk.BOTH, expand=True)

    # ── 회전 그라데이션 스피너 ────────────────────────────────────
    SPIN = 96
    spin_c = tk.Canvas(frame, width=SPIN, height=SPIN, bg=BG, highlightthickness=0)
    spin_c.pack(pady=(4, 22))

    _SPIN_COLORS = [BLUE, "#2FA0E0", TEAL, "#1FD9A0"]
    _angle = [0]

    def _draw_spinner():
      if not spin_c.winfo_exists():
        return
      spin_c.delete("all")
      cx = cy = SPIN / 2
      r = SPIN / 2 - 6
      n = len(_SPIN_COLORS)
      for i, color in enumerate(_SPIN_COLORS):
        start = _angle[0] + i * (300 / n)
        spin_c.create_arc(cx - r, cy - r, cx + r, cy + r,
                          start=start, extent=300 / n - 6,
                          style=tk.ARC, outline=color, width=5)
      spin_c.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, fill=TEAL, outline="")
      _angle[0] = (_angle[0] + 6) % 360
      self.root.after(40, _draw_spinner)

    _draw_spinner()

    tk.Label(frame, text="잠시만 기다려주세요.", fg=WHITE, bg=BG,
             font=("Segoe UI", 14, "bold")).pack(pady=(0, 4))
    tk.Label(frame, text="시스템 정보를 확인중입니다.", fg=GRAY, bg=BG,
             font=("Segoe UI", 10)).pack(pady=(0, 18))

    status_lbl = tk.Label(frame, text="하드웨어 정보 수집 중...", fg=TEAL, bg=BG,
                          font=("Segoe UI", 10, "bold"))
    status_lbl.pack(pady=(0, 16))

    # ── 진행률 표시줄 ─────────────────────────────────────────────
    BAR_W, BAR_H = 320, 8
    bar_c = tk.Canvas(frame, width=BAR_W, height=BAR_H, bg=BG, highlightthickness=0)
    bar_c.pack(pady=(0, 8))
    pct_lbl = tk.Label(frame, text="0%", fg=GRAY, bg=BG, font=("Segoe UI", 9))
    pct_lbl.pack()

    _STATUS_MSGS = [
      "하드웨어 정보 수집 중...",
      "프로세스 목록 수집 중...",
      "디스크 정보 확인 중...",
      "그래픽 장치 확인 중...",
    ]
    _progress = [0]
    _msg_i = [0]
    _done = [False]

    def _tick():
      if not bar_c.winfo_exists():
        return
      if not _done[0] and _progress[0] < 90:
        _progress[0] += 2
        if _progress[0] % 22 == 0:
          _msg_i[0] = (_msg_i[0] + 1) % len(_STATUS_MSGS)
          status_lbl.config(text=_STATUS_MSGS[_msg_i[0]])

      pct = _progress[0]
      bar_c.delete("all")
      _rrect(bar_c, 0, 0, BAR_W, BAR_H, BAR_H // 2, DIVIDER)
      fill_w = max(BAR_H, int(BAR_W * pct / 100))
      _rrect(bar_c, 0, 0, fill_w, BAR_H, BAR_H // 2, _hex_mix(BLUE, TEAL, pct / 100))
      pct_lbl.config(text=f"{pct}%")
      self.root.after(80, _tick)

    _tick()
    self.root.update()

    def _load():
      self._hardware_info = get_hardware_info()
      _done[0] = True
      _progress[0] = 100
      if self.root.winfo_exists():
        status_lbl.config(text="완료되었습니다.") if status_lbl.winfo_exists() else None
        self.root.after(250, self._show_settings_screen)

    threading.Thread(target=_load, daemon=True).start()

  def _show_settings_screen(self):
    self._clear_window()
    self.root.title(SETTINGS_TITLE)
    self.root.resizable(False, False)
    self._center_window(620, 760)
    self.root.configure(bg=BG)

    self._part_vars = {}
    self._part_hw_frames = {}
    self._part_radio_widgets = {}
    self._part_desc_labels = {}
    self._part_owned_frames = {}
    self._owned_query_vars = {}
    self._owned_results_frames = {}
    self._owned_selected_labels = {}
    self._owned_candidate_vars = {}

    # ── 알약형 토글 그룹 헬퍼 (지식 수준 / 부품 옵션 공용) ─────────
    # ── 하단 고정 내비게이션 ───────────────────────────────────────
    nav_frame = tk.Frame(self.root, bg=BG, padx=P, pady=16)
    nav_frame.pack(side=tk.BOTTOM, fill=tk.X)

    back_btn = _pill(nav_frame, "←  뒤로", DIVIDER, GRAY, width=120)
    back_btn.pack(side=tk.LEFT)
    back_btn.bind("<Button-1>", lambda e: self._show_consent_screen())

    cont_btn = _pill(nav_frame, "계속  →", BTN_CONT_ON, WHITE, width=140)
    cont_btn.pack(side=tk.RIGHT)
    cont_btn.bind("<Button-1>", lambda e: self._on_settings_continue())

    # ── 스크롤 가능한 콘텐츠 영역 ──────────────────────────────────
    outer = tk.Frame(self.root, bg=BG)
    outer.pack(fill=tk.BOTH, expand=True)

    scr = tk.Canvas(outer, bg=BG, highlightthickness=0)
    scr.pack(fill=tk.BOTH, expand=True)

    body = tk.Frame(scr, bg=BG)
    win_id = scr.create_window((0, 0), anchor="nw", window=body)
    scr.bind("<Configure>", lambda e: scr.itemconfig(win_id, width=e.width))
    body.bind("<Configure>", lambda e: scr.configure(scrollregion=scr.bbox("all")))
    scr.bind("<Enter>", lambda e: scr.bind_all(
      "<MouseWheel>", lambda ev: scr.yview_scroll(int(-1 * (ev.delta / 120)), "units")))
    scr.bind("<Leave>", lambda e: scr.unbind_all("<MouseWheel>"))

    # ── 헤더 ──────────────────────────────────────────────────────
    hdr = tk.Frame(body, bg=BG, padx=P, pady=20)
    hdr.pack(fill=tk.X)

    bc = tk.Frame(hdr, bg=BG)
    bc.pack(anchor="w")
    tk.Label(bc, text="BUILDSENSE", fg=TEAL, bg=BG,
             font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT)
    tk.Label(bc, text="  ·  초기 설정", fg=GRAY, bg=BG,
             font=("Segoe UI", 8)).pack(side=tk.LEFT)

    tk.Label(hdr, text="모니터링 설정을 선택해 주세요", fg=WHITE, bg=BG,
             font=("Segoe UI", 15, "bold")).pack(anchor="w", pady=(6, 0))

    def _section_label(text):
      tk.Label(body, text=text, fg=WHITE, bg=BG,
               font=("Segoe UI", 11, "bold")).pack(
        anchor="w", padx=P, pady=(4, 10))

    def _divider():
      tk.Frame(body, height=1, bg=DIVIDER).pack(fill=tk.X, padx=P, pady=(6, 18))

    # ── 섹션 1: 컴퓨터 지식 수준 ──────────────────────────────────
    _section_label("컴퓨터 지식 수준")

    kl_row = tk.Frame(body, bg=BG, padx=P)
    kl_row.pack(fill=tk.X, pady=(0, 6))

    self._knowledge_var = tk.StringVar(value=self.settings_state["knowledge_level"])
    kl_toggle = _make_toggle(kl_row, KNOWLEDGE_LEVELS, self._knowledge_var,
                             on_change=lambda v: self._on_knowledge_change(),
                             seg_w=148, seg_h=36)
    kl_toggle.pack(anchor="w")
    self._kl_toggle = kl_toggle

    tk.Label(body, text="선택한 수준에 따라 부품별 설명과 추천 방식이 달라집니다.",
             fg=GRAY, bg=BG, font=("Segoe UI", 9)).pack(
      anchor="w", padx=P, pady=(10, 0))

    _divider()

    # ── 섹션 2: 분석 기간 ─────────────────────────────────────────
    _section_label("분석 기간")

    days_row = tk.Frame(body, bg=BG, padx=P)
    days_row.pack(fill=tk.X, pady=(0, 6))

    self._days_var = tk.IntVar(value=self.settings_state["analysis_days"])
    spin = tk.Spinbox(
      days_row,
      from_=ANALYSIS_DAYS_MIN,
      to=ANALYSIS_DAYS_MAX,
      textvariable=self._days_var,
      width=4,
      font=("Segoe UI", 11, "bold"),
      bg=CARD, fg=WHITE, buttonbackground=DIVIDER,
      insertbackground=WHITE, relief=tk.FLAT, highlightthickness=0,
      justify=tk.CENTER,
    )
    spin.pack(side=tk.LEFT, ipady=4, ipadx=4)
    tk.Label(days_row, text=f"일   (권장: {ANALYSIS_DAYS_MIN}~{ANALYSIS_DAYS_MAX}일)",
             fg=GRAY, bg=BG, font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(10, 0))

    tk.Label(body, text="※  정확한 분석을 위해 7일 이상의 수집 기간을 권장합니다.",
             fg=GRAY, bg=BG, font=("Segoe UI", 9)).pack(
      anchor="w", padx=P, pady=(10, 0))

    _divider()

    # ── 섹션 3: 추천 부품 선택 ────────────────────────────────────
    _section_label("추천 부품 선택")

    level = self.settings_state["knowledge_level"]
    cards_col = tk.Frame(body, bg=BG, padx=P)
    cards_col.pack(fill=tk.X, pady=(0, 24))

    for i, part in enumerate(PARTS):
      part_state = self.settings_state["parts"][part]

      card = tk.Frame(cards_col, bg=CARD, padx=18, pady=14)
      card.pack(fill=tk.X, pady=(0, 10))

      top_row = tk.Frame(card, bg=CARD)
      top_row.pack(fill=tk.X)

      icon_c = tk.Canvas(top_row, width=36, height=36, bg=CARD, highlightthickness=0)
      icon_c.pack(side=tk.LEFT, padx=(0, 12))
      _rrect(icon_c, 0, 0, 36, 36, 9, ICON_BG)
      icon_c.create_text(18, 18, text=_PART_ICONS.get(part, "◈"),
                         fill=TEAL, font=("Segoe UI Symbol", 13))

      name_col = tk.Frame(top_row, bg=CARD)
      name_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
      tk.Label(name_col, text=part, fg=WHITE, bg=CARD,
               font=("Segoe UI", 11, "bold")).pack(anchor="w")

      desc_label = tk.Label(
        name_col,
        text=PART_DESCRIPTIONS[part][level],
        font=("Segoe UI", 9),
        fg=GRAY, bg=CARD,
        anchor="w", wraplength=340, justify=tk.LEFT,
      )
      desc_label.pack(anchor="w", pady=(2, 0))
      self._part_desc_labels[part] = desc_label

      var = tk.StringVar(value=part_state["option"])
      self._part_vars[part] = var

      part_options = PART_OPTIONS if part in OWNED_CAPABLE_PARTS else PART_OPTIONS_BASIC
      toggle = _make_toggle(top_row, part_options, var,
                            on_change=lambda v, p=part: self._on_part_option_change(p),
                            seg_w=64, seg_h=30, gap=6, bg=CARD)
      toggle.pack(side=tk.RIGHT, anchor="n")
      self._part_radio_widgets[part] = toggle

      # 현재 장착 정보 (유지 선택 시)
      hw_frame = tk.Frame(card, bg=CARD)
      self._part_hw_frames[part] = hw_frame

      if part == "메인보드":
        socket = self._hardware_info.get("CPU_socket")
        hw_text = f"{socket} 소켓" if socket else "소켓 감지 불가"
      else:
        hw_text = self._hardware_info.get(part, "확인할 수 없음")

      hw_badge = _badge(hw_frame, f"현재 장착 · {hw_text}", bg=BADGE_BG, fg=BADGE_FG)
      hw_badge.pack(anchor="w")

      # 보유 제품 검색 (보유 선택 시, CPU/GPU만)
      owned_frame = None
      if part in OWNED_CAPABLE_PARTS:
        owned_frame = tk.Frame(card, bg=CARD)
        self._part_owned_frames[part] = owned_frame

        search_row = tk.Frame(owned_frame, bg=CARD)
        search_row.pack(fill=tk.X)

        query_var = tk.StringVar(value="")
        self._owned_query_vars[part] = query_var

        entry = tk.Entry(
          search_row, textvariable=query_var,
          font=("Segoe UI", 10),
          bg=BG, fg=WHITE, insertbackground=WHITE,
          relief=tk.FLAT, highlightthickness=1,
          highlightbackground=DIVIDER, highlightcolor=TEAL,
        )
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4, ipadx=6, padx=(0, 8))

        search_btn = _pill(search_row, "제품 찾기", BLUE, WHITE,
                           width=92, height=32, font_size=9, bg=CARD)
        search_btn.pack(side=tk.LEFT)
        search_btn.bind("<Button-1>", lambda e, p=part: self._on_search_owned_product(p))

        selected_label = tk.Label(
          owned_frame, text="", fg=TEAL, bg=CARD,
          font=("Segoe UI", 9, "bold"), anchor="w",
        )
        selected_label.pack(anchor="w", pady=(8, 0))
        self._owned_selected_labels[part] = selected_label

        owned_product = part_state.get("owned_product")
        if owned_product:
          selected_label.config(text=f"선택됨 · {owned_product.get('name', '')}")

        results_frame = tk.Frame(owned_frame, bg=CARD)
        results_frame.pack(fill=tk.X, pady=(8, 0))
        self._owned_results_frames[part] = results_frame

      if part_state["option"] == "keep":
        hw_frame.pack(fill=tk.X, pady=(12, 0))
      elif part_state["option"] == "owned" and owned_frame is not None:
        owned_frame.pack(fill=tk.X, pady=(12, 0))

    # 초기 지식 수준에 따른 부품 섹션 상태 반영
    self._on_knowledge_change()

  def _show_monitoring_screen(self):
    self._clear_window()
    self.root.title("BuildSense - 모니터링 중")
    self.root.resizable(False, False)
    self._center_window(520, 480)
    self.root.configure(bg=BG)

    body = tk.Frame(self.root, bg=BG, padx=P, pady=24)
    body.pack(fill=tk.BOTH, expand=True)

    # ── 헤더 (브레드크럼 + 펄싱 점 + 제목) ────────────────────────
    bc = tk.Frame(body, bg=BG)
    bc.pack(anchor="w")
    tk.Label(bc, text="BUILDSENSE", fg=TEAL, bg=BG,
             font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT)
    tk.Label(bc, text="  ·  모니터링", fg=GRAY, bg=BG,
             font=("Segoe UI", 8)).pack(side=tk.LEFT)

    title_row = tk.Frame(body, bg=BG)
    title_row.pack(fill=tk.X, pady=(8, 4))

    DOT = 20
    dot_c = tk.Canvas(title_row, width=DOT, height=DOT, bg=BG, highlightthickness=0)
    dot_c.pack(side=tk.LEFT, padx=(0, 10))

    _phase = [0.0]

    def _draw_pulse():
      if not dot_c.winfo_exists():
        return
      dot_c.delete("all")
      t = (math.sin(_phase[0]) + 1) / 2
      cx = cy = DOT / 2
      glow_r = 5 + t * 4
      dot_c.create_oval(cx - glow_r, cy - glow_r, cx + glow_r, cy + glow_r,
                        fill=_hex_mix(BG, DOT_GRN, 0.30 + t * 0.25), outline="")
      dot_c.create_oval(cx - 4, cy - 4, cx + 4, cy + 4, fill=DOT_GRN, outline="")
      _phase[0] += 0.25
      self.root.after(60, _draw_pulse)

    _draw_pulse()

    tk.Label(title_row, text="모니터링 실행중", fg=WHITE, bg=BG,
             font=("Segoe UI", 14, "bold")).pack(side=tk.LEFT)

    tk.Label(body, text="시스템 사용 데이터를 백그라운드에서 수집하고 있습니다.",
             fg=GRAY, bg=BG, font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 18))

    # ── 로그 경로 (코드 스타일 박스) ──────────────────────────────
    tk.Label(body, text="로그 경로", fg=GRAY, bg=BG,
             font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 6))

    path_box = tk.Frame(body, bg=CARD, padx=14, pady=10)
    path_box.pack(fill=tk.X, pady=(0, 18))
    tk.Label(path_box, text=str(USAGE_LOG_PATH), fg=TEAL, bg=CARD,
             font=("Consolas", 9), anchor="w",
             wraplength=440, justify=tk.LEFT).pack(fill=tk.X)

    # ── 정보 행 ──────────────────────────────────────────────────
    days_row = tk.Frame(body, bg=BG)
    days_row.pack(fill=tk.X, pady=(0, 10))
    tk.Label(days_row, text="분석 기간", fg=GRAY, bg=BG, font=("Segoe UI", 10)).pack(side=tk.LEFT)
    tk.Label(days_row, text=f"{self.settings_state['analysis_days']}일", fg=WHITE, bg=BG,
             font=("Segoe UI", 10, "bold")).pack(side=tk.RIGHT)

    data_row = tk.Frame(body, bg=BG)
    data_row.pack(fill=tk.X, pady=(0, 22))
    tk.Label(data_row, text="수집된 데이터", fg=GRAY, bg=BG, font=("Segoe UI", 10)).pack(side=tk.LEFT)
    data_lbl = tk.Label(data_row, text="측정 중...", fg=BADGE_FG, bg=BADGE_BG,
                        font=("Segoe UI", 9, "bold"), padx=12, pady=4)
    data_lbl.pack(side=tk.RIGHT)

    def _update_size():
      if not self.root.winfo_exists() or not data_lbl.winfo_exists():
        return
      try:
        if USAGE_LOG_PATH.exists():
          size = USAGE_LOG_PATH.stat().st_size
          if size < 1024:
            size_str = f"{size} B"
          elif size < 1024 * 1024:
            size_str = f"{size / 1024:.1f} KB"
          else:
            size_str = f"{size / (1024 * 1024):.2f} MB"
          lines = get_log_line_count()
          data_lbl.config(text=f"{size_str}  ·  {lines:,}개 스냅샷")
        else:
          data_lbl.config(text="0 B  ·  0개 스냅샷")
      except Exception:
        pass
      self.root.after(5000, _update_size)

    _update_size()

    # ── 중도 종료 ────────────────────────────────────────────────
    abort_card = tk.Frame(body, bg=CARD, padx=18, pady=16)

    tk.Label(abort_card,
             text="지금까지 저장된 데이터가 모두 삭제되며 분석을 포기합니다.",
             fg=RED, bg=CARD, font=("Segoe UI", 9, "bold"), anchor="w",
             wraplength=420, justify=tk.LEFT).pack(fill=tk.X, pady=(0, 14))

    confirm_row = tk.Frame(abort_card, bg=CARD)
    confirm_row.pack(fill=tk.X, pady=(0, 14))
    tk.Label(confirm_row, text="정말로 종료할까요?", fg=GRAY, bg=CARD,
             font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(0, 14))

    action_row = tk.Frame(abort_card, bg=CARD)
    action_row.pack(fill=tk.X)

    confirm_var = tk.StringVar(value="no")
    stop_btn = _pill(action_row, "종료", BTN_EXIT, "#8A5050", width=120, height=40, bg=CARD)

    def _refresh_stop_btn(v=None):
      if confirm_var.get() == "yes":
        stop_btn._fg[0] = WHITE
        stop_btn._normal = BTN_EXIT
        stop_btn._draw(BTN_EXIT)
        stop_btn.bind("<Enter>", lambda e: stop_btn._draw(_hex_mix(BTN_EXIT, "#ffffff", 0.12)))
        stop_btn.bind("<Leave>", lambda e: stop_btn._draw(BTN_EXIT))
        stop_btn.bind("<Button-1>", lambda e: _on_stop())
        stop_btn.configure(cursor="hand2")
      else:
        stop_btn._fg[0] = "#8A5050"
        stop_btn._normal = _hex_mix(BTN_EXIT, BG, 0.5)
        stop_btn._draw(stop_btn._normal)
        stop_btn.bind("<Enter>", lambda e: None)
        stop_btn.bind("<Leave>", lambda e: None)
        stop_btn.bind("<Button-1>", lambda e: None)
        stop_btn.configure(cursor="arrow")

    confirm_toggle = _make_toggle(confirm_row, [("아니오", "no"), ("예", "yes")], confirm_var,
                                  on_change=_refresh_stop_btn, seg_w=64, seg_h=30, gap=6, sel_color=RED, bg=CARD)
    confirm_toggle.pack(side=tk.LEFT)

    def _on_stop():
      stop_monitoring_loop()
      join_background_task()
      delete_all_monitoring_data()
      unregister_startup()
      self._clear_window()
      self._center_window(380, 200)
      self.root.configure(bg=BG)
      done = tk.Frame(self.root, bg=BG, padx=24, pady=30)
      done.pack(fill=tk.BOTH, expand=True)
      tk.Label(done, text="분석이 종료되었습니다.", fg=WHITE, bg=BG,
               font=("Segoe UI", 13, "bold")).pack(expand=True)
      ok_btn = _pill(done, "확인", BTN_CONT_ON, WHITE, width=120)
      ok_btn.pack(pady=(8, 0))
      ok_btn.bind("<Button-1>", lambda e: self.root.destroy())

    _refresh_stop_btn()
    stop_btn.pack(side=tk.LEFT)

    toggle_btn = _pill(body, "×  중도 종료", BTN_EXIT, WHITE, width=140)

    def _resize_to_content():
      self.root.update_idletasks()
      h = min(body.winfo_reqheight(), self.root.winfo_screenheight() - 80)
      self._center_window(520, h)

    def _show_abort_card():
      toggle_btn.pack_forget()
      abort_card.pack(fill=tk.X, pady=(0, 0))
      _resize_to_content()

    def _hide_abort_card():
      confirm_var.set("no")
      confirm_toggle.redraw()
      _refresh_stop_btn()
      abort_card.pack_forget()
      toggle_btn.pack(anchor="w")
      _resize_to_content()

    cancel_btn = _pill(action_row, "취소", DIVIDER, GRAY, width=90, height=40, bg=CARD)
    cancel_btn.pack(side=tk.RIGHT)
    cancel_btn.bind("<Button-1>", lambda e: _hide_abort_card())

    toggle_btn.bind("<Button-1>", lambda e: _show_abort_card())
    toggle_btn.pack(anchor="w")

    # 고정 높이로 인해 하단 여백이 과도하게 남던 문제 수정:
    # 콘텐츠의 실제 높이에 맞춰 창 크기를 잡고, 중도 종료 카드가 열리고 닫힐 때마다 다시 맞춘다
    _resize_to_content()

  def _show_review_dialog(self):
    dialog = tk.Toplevel(self.root)
    dialog.title("BuildSense - 설정 요약")
    dialog.resizable(False, False)
    dialog.configure(bg=BG)
    dialog.grab_set()

    body = tk.Frame(dialog, bg=BG, padx=P, pady=22)
    body.pack(fill=tk.BOTH, expand=True)

    # ── 헤더 ──────────────────────────────────────────────────────
    hdr = tk.Frame(body, bg=BG)
    hdr.pack(fill=tk.X, pady=(0, 20))

    icon_c = tk.Canvas(hdr, width=46, height=46, bg=BG, highlightthickness=0)
    icon_c.pack(side=tk.LEFT, padx=(0, 14))
    _rrect(icon_c, 0, 0, 46, 46, 11, ICON_BG)
    icon_c.create_text(23, 23, text="⚙", fill=TEAL, font=("Segoe UI Symbol", 17))

    title_col = tk.Frame(hdr, bg=BG)
    title_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    bc = tk.Frame(title_col, bg=BG)
    bc.pack(anchor="w")
    tk.Label(bc, text="BUILDSENSE", fg=TEAL, bg=BG,
             font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT)
    tk.Label(bc, text="  ·  설정 요약", fg=GRAY, bg=BG,
             font=("Segoe UI", 8)).pack(side=tk.LEFT)
    tk.Label(title_col, text="설정을 확인하고 분석을 시작하세요", fg=WHITE, bg=BG,
             font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(4, 0))

    state = self.settings_state
    kl_label = KNOWLEDGE_LEVEL_LABELS.get(
      state["knowledge_level"], state["knowledge_level"]
    )

    def _summary_row(label, value_text):
      row = tk.Frame(body, bg=CARD, padx=16, pady=12)
      row.pack(fill=tk.X, pady=(0, 8))
      tk.Label(row, text=label, fg=GRAY, bg=CARD, font=("Segoe UI", 10)).pack(side=tk.LEFT)
      _badge(row, value_text).pack(side=tk.RIGHT)

    _summary_row("컴퓨터 지식 수준", kl_label)
    _summary_row("분석 기간", f"{state['analysis_days']}일")

    # ── 추천 부품 선택 목록 ───────────────────────────────────────
    tk.Label(body, text="추천 부품 선택", fg=WHITE, bg=BG,
             font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(14, 8))

    list_card = tk.Frame(body, bg=CARD, padx=16, pady=4)
    list_card.pack(fill=tk.X, pady=(0, 20))

    for i, part in enumerate(PARTS):
      part_state = state["parts"][part]
      option = part_state["option"]
      option_label = PART_OPTION_LABELS.get(option, option)
      is_recommend = option == "recommend"

      row = tk.Frame(list_card, bg=CARD)
      row.pack(fill=tk.X, pady=10)

      ic = tk.Canvas(row, width=28, height=28, bg=CARD, highlightthickness=0)
      ic.pack(side=tk.LEFT, padx=(0, 10))
      _rrect(ic, 0, 0, 28, 28, 7, ICON_BG)
      ic.create_text(14, 14, text=_PART_ICONS.get(part, "◈"),
                     fill=TEAL, font=("Segoe UI Symbol", 10))

      name_text = part
      if option == "keep":
        hw = self._hardware_info.get(part, "")
        if hw:
          name_text += f"  ({hw})"
      elif option == "owned":
        owned_name = (part_state.get("owned_product") or {}).get("name")
        if owned_name:
          name_text += f"  ({owned_name})"
      tk.Label(row, text=name_text, fg=WHITE, bg=CARD,
               font=("Segoe UI", 10)).pack(side=tk.LEFT)

      _badge(row, option_label,
             bg=BADGE_BG if is_recommend else DIVIDER,
             fg=BADGE_FG if is_recommend else GRAY).pack(side=tk.RIGHT)

      if i < len(PARTS) - 1:
        tk.Frame(list_card, height=1, bg=DIVIDER).pack(fill=tk.X)

    # ── 버튼 행 ───────────────────────────────────────────────────
    btn_row = tk.Frame(body, bg=BG)
    btn_row.pack(fill=tk.X, pady=(4, 0))

    edit_btn = _pill(btn_row, "←  수정하기", DIVIDER, GRAY, width=130)
    edit_btn.pack(side=tk.LEFT)
    edit_btn.bind("<Button-1>", lambda e: dialog.destroy())

    def _on_start():
      result = validate_parts_not_all_keep(self.settings_state["parts"])
      if not result.valid:
        messagebox.showwarning(title="BuildSense", message=result.message)
        return

      result = validate_owned_parts_selected(self.settings_state["parts"])
      if not result.valid:
        messagebox.showwarning(title="BuildSense", message=result.message)
        return

      profile = {
        "consent": self.consent_state,
        "knowledge_level": self.settings_state["knowledge_level"],
        "analysis_days": self.settings_state["analysis_days"],
        "parts": self.settings_state["parts"],
      }

      try:
        save_user_profile(profile)
        messagebox.showinfo(
          title="BuildSense",
          message="설정이 저장되었습니다.\n분석을 시작합니다.",
        )
      except Exception as e:
        messagebox.showerror(
          title="저장 오류",
          message=f"프로필 저장에 실패했습니다.\n{e}",
        )
        return

      dialog.destroy()
      start_monitoring_loop()
      register_startup()
      self._show_monitoring_screen()

    start_btn = _pill(btn_row, "▶  분석 시작", BTN_START, WHITE, width=160)
    start_btn.pack(side=tk.RIGHT)
    start_btn.bind("<Button-1>", lambda e: _on_start())

    dialog.update_idletasks()
    height = min(body.winfo_reqheight() + 4, self.root.winfo_screenheight() - 80)
    self._center_toplevel(dialog, 460, height)

  # ------------------------------------------------------------------
  # 버튼 핸들러
  # ------------------------------------------------------------------

  def _on_agree(self):
    record_agreement(self.consent_state)
    self._show_loading_screen()

  def _on_decline(self):
    record_decline(self.consent_state)
    messagebox.showinfo(title="BuildSense", message=DECLINE_MESSAGE)
    self.root.destroy()

  def _on_settings_continue(self):
    if not self._validate_days():
      return
    self._sync_settings_state()
    self._show_review_dialog()

  def _on_knowledge_change(self):
    level = self._knowledge_var.get()
    is_beginner = level == "beginner"

    for part in PARTS:
      # 설명 텍스트 실시간 업데이트
      if part in self._part_desc_labels:
        self._part_desc_labels[part].config(text=PART_DESCRIPTIONS[part][level])

      # 토글 그룹 활성화 상태 변경
      toggle = self._part_radio_widgets.get(part)
      if toggle is not None:
        toggle.set_enabled(not is_beginner)

      # 전혀 모름: 모든 부품을 추천으로 초기화하고 하위 프레임 숨김
      if is_beginner:
        self._part_vars[part].set("recommend")
        if toggle is not None:
          toggle.redraw()
        self._part_hw_frames[part].pack_forget()
        owned_frame = self._part_owned_frames.get(part)
        if owned_frame is not None:
          owned_frame.pack_forget()

  def _on_part_option_change(self, part: str):
    value = self._part_vars[part].get()
    hw_frame = self._part_hw_frames[part]
    owned_frame = self._part_owned_frames.get(part)

    hw_frame.pack_forget()
    if owned_frame is not None:
      owned_frame.pack_forget()

    if value == "keep":
      hw_frame.pack(fill=tk.X, pady=(12, 0))
    elif value == "owned" and owned_frame is not None:
      owned_frame.pack(fill=tk.X, pady=(12, 0))

  def _on_search_owned_product(self, part: str):
    query = self._owned_query_vars[part].get().strip()
    category = "cpu" if part == "CPU" else "gpu"
    candidates = search_passmark_candidates(query, category) if query else []
    self._render_owned_candidates(part, candidates)

  def _render_owned_candidates(self, part: str, candidates: list[dict]):
    results_frame = self._owned_results_frames[part]
    for child in results_frame.winfo_children():
      child.destroy()

    if not candidates:
      tk.Label(results_frame, text="검색 결과가 없습니다.", fg=GRAY, bg=CARD,
               font=("Segoe UI", 9)).pack(anchor="w")
      return

    current = (self.settings_state["parts"][part].get("owned_product") or {}).get("name")
    var = tk.StringVar(value=current if any(item.get("name") == current for item in candidates) else "")
    self._owned_candidate_vars[part] = var

    for item in candidates:
      tk.Radiobutton(
        results_frame,
        text=item.get("name", ""),
        variable=var,
        value=item.get("name", ""),
        font=("Segoe UI", 9),
        command=lambda p=part, it=item: self._on_select_owned_candidate(p, it),
        bg=CARD, fg=GRAY, activebackground=CARD, activeforeground=WHITE,
        selectcolor=BG, highlightthickness=0,
      ).pack(anchor="w")

  def _on_select_owned_candidate(self, part: str, item: dict):
    self.settings_state["parts"][part]["owned_product"] = item
    label = self._owned_selected_labels.get(part)
    if label is not None:
      label.config(text=f"선택됨 · {item.get('name', '')}")

  # ------------------------------------------------------------------
  # 검증 및 상태 동기화
  # ------------------------------------------------------------------

  def _validate_days(self) -> bool:
    try:
      raw = self._days_var.get()
    except tk.TclError:
      raw = None

    result = validate_analysis_days(raw)
    if not result.valid:
      messagebox.showwarning(title="입력 오류", message=result.message)
      self._days_var.set(result.corrected)
      return False

    return True

  def _sync_settings_state(self):
    self.settings_state["knowledge_level"] = self._knowledge_var.get()
    self.settings_state["analysis_days"] = self._days_var.get()
    for part in PARTS:
      self.settings_state["parts"][part]["option"] = self._part_vars[part].get()

  # ------------------------------------------------------------------
  # 유틸리티
  # ------------------------------------------------------------------

  def _clear_window(self):
    for widget in self.root.winfo_children():
      widget.destroy()

  def _center_window(self, width: int, height: int):
    self.root.update_idletasks()
    sw = self.root.winfo_screenwidth()
    sh = self.root.winfo_screenheight()
    x = (sw - width) // 2
    y = (sh - height) // 2
    self.root.geometry(f"{width}x{height}+{x}+{y}")

  def _center_toplevel(self, dialog: tk.Toplevel, width: int, height: int):
    self.root.update_idletasks()
    rx = self.root.winfo_x()
    ry = self.root.winfo_y()
    rw = self.root.winfo_width()
    rh = self.root.winfo_height()
    x = rx + (rw - width) // 2
    y = ry + (rh - height) // 2
    dialog.geometry(f"{width}x{height}+{x}+{y}")
