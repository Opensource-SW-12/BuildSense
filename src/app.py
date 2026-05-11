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
  PART_OPTION_LABELS,
  PART_DESCRIPTIONS,
  build_settings_state,
)
from src.hardware import get_hardware_info
from src.storage import save_user_profile
from src.validators import validate_analysis_days, validate_parts_not_all_keep
from src.monitor import start_monitoring_loop, stop_monitoring_loop, is_monitoring_running
from src.config import USAGE_LOG_PATH

SETTINGS_TITLE = "BuildSense - 사용자 설정"


class BuildSenseApp:
  def __init__(self):
    self.root = tk.Tk()
    self.consent_state = build_consent_state()
    self.settings_state = build_settings_state()
    self._hardware_info = {}
    self._knowledge_var = None
    self._days_var = None
    self._part_vars = {}
    self._part_entries = {}
    self._part_entry_frames = {}
    self._part_hw_frames = {}
    self._part_radio_widgets = {}
    self._part_desc_labels = {}
    self._show_consent_screen()

  def run(self):
    self.root.mainloop()

  # ------------------------------------------------------------------
  # 화면 전환
  # ------------------------------------------------------------------

  def _show_consent_screen(self):
    self._clear_window()
    self.root.title(CONSENT_TITLE)
    self.root.resizable(False, False)
    self._center_window(560, 430)

    frame = tk.Frame(self.root, padx=24, pady=20)
    frame.pack(fill=tk.BOTH, expand=True)

    tk.Label(
      frame,
      text="데이터 수집 동의",
      font=("Segoe UI", 14, "bold"),
      anchor="w",
    ).pack(fill=tk.X, pady=(0, 12))

    body = tk.Text(
      frame,
      height=14,
      wrap=tk.WORD,
      font=("Segoe UI", 10),
      relief=tk.FLAT,
      bg=self.root.cget("bg"),
      state=tk.NORMAL,
      cursor="arrow",
    )
    body.insert(tk.END, CONSENT_BODY)
    body.config(state=tk.DISABLED)
    body.pack(fill=tk.BOTH, expand=True)

    # 동의 체크박스
    agree_var = tk.BooleanVar(value=False)

    checkbox_frame = tk.Frame(frame)
    checkbox_frame.pack(fill=tk.X, pady=(12, 0))

    def _on_checkbox_toggle():
      continue_btn.config(
        state=tk.NORMAL if agree_var.get() else tk.DISABLED
      )

    tk.Checkbutton(
      checkbox_frame,
      text="동의합니다",
      variable=agree_var,
      font=("Segoe UI", 10),
      command=_on_checkbox_toggle,
    ).pack(side=tk.LEFT)

    # 버튼 줄 (체크박스 아래 별도 라인)
    btn_frame = tk.Frame(frame)
    btn_frame.pack(fill=tk.X, pady=(8, 0))

    continue_btn = tk.Button(
      btn_frame,
      text="계속",
      width=12,
      state=tk.DISABLED,
      command=self._on_agree,
    )
    continue_btn.pack(side=tk.RIGHT)

    tk.Button(
      btn_frame,
      text="종료",
      width=12,
      command=self._on_decline,
    ).pack(side=tk.RIGHT, padx=(0, 8))

  def _show_loading_screen(self):
    self._clear_window()
    self.root.title("BuildSense")
    self.root.resizable(False, False)
    self._center_window(320, 160)

    frame = tk.Frame(self.root, padx=24, pady=20)
    frame.pack(fill=tk.BOTH, expand=True)

    tk.Label(
      frame,
      text="잠시만 기다려 주세요",
      font=("Segoe UI", 12, "bold"),
      anchor="center",
    ).pack(expand=True)

    tk.Label(
      frame,
      text="하드웨어 정보를 확인하는 중입니다...",
      font=("Segoe UI", 9),
      fg="#666666",
      anchor="center",
    ).pack(expand=True)

    self.root.update()

    def _load():
      self._hardware_info = get_hardware_info()
      if self.root.winfo_exists():
        self.root.after(0, self._show_settings_screen)

    threading.Thread(target=_load, daemon=True).start()

  def _show_settings_screen(self):
    self._clear_window()
    self.root.title(SETTINGS_TITLE)
    self.root.resizable(False, False)
    self._center_window(580, 580)

    self._part_vars = {}
    self._part_entries = {}
    self._part_entry_frames = {}
    self._part_hw_frames = {}
    self._part_radio_widgets = {}
    self._part_desc_labels = {}

    # 하단 고정 내비게이션
    nav_frame = tk.Frame(self.root, padx=24, pady=10)
    nav_frame.pack(side=tk.BOTTOM, fill=tk.X)

    tk.Frame(nav_frame, height=1, bg="#cccccc").pack(fill=tk.X, pady=(0, 8))

    tk.Button(
      nav_frame,
      text="계속",
      width=12,
      command=self._on_settings_continue,
    ).pack(side=tk.RIGHT)

    tk.Button(
      nav_frame,
      text="뒤로",
      width=12,
      command=self._show_consent_screen,
    ).pack(side=tk.RIGHT, padx=(0, 8))

    # 스크롤 가능한 콘텐츠 영역
    outer = tk.Frame(self.root)
    outer.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(outer, highlightthickness=0)
    scrollbar = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    inner = tk.Frame(canvas, padx=24, pady=16)
    win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

    inner.bind(
      "<Configure>",
      lambda e: inner.after_idle(
        lambda: canvas.configure(scrollregion=canvas.bbox("all"))
      ),
    )
    canvas.bind(
      "<Configure>",
      lambda e: canvas.itemconfig(win_id, width=e.width),
    )

    def _on_mousewheel(event):
      canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
    canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

    # ── 섹션 1: 컴퓨터 지식 수준 ──────────────────────────────────────
    tk.Label(
      inner,
      text="컴퓨터 지식 수준",
      font=("Segoe UI", 11, "bold"),
      anchor="w",
    ).pack(fill=tk.X, pady=(0, 6))

    self._knowledge_var = tk.StringVar(value=self.settings_state["knowledge_level"])
    kl_frame = tk.Frame(inner)
    kl_frame.pack(fill=tk.X, pady=(0, 16))

    for label, value in KNOWLEDGE_LEVELS:
      tk.Radiobutton(
        kl_frame,
        text=label,
        variable=self._knowledge_var,
        value=value,
        font=("Segoe UI", 10),
        command=self._on_knowledge_change,
      ).pack(side=tk.LEFT, padx=(0, 16))

    tk.Frame(inner, height=1, bg="#cccccc").pack(fill=tk.X, pady=(0, 16))

    # ── 섹션 2: 분석 기간 ─────────────────────────────────────────────
    tk.Label(
      inner,
      text="분석 기간",
      font=("Segoe UI", 11, "bold"),
      anchor="w",
    ).pack(fill=tk.X, pady=(0, 6))

    self._days_var = tk.IntVar(value=self.settings_state["analysis_days"])
    days_frame = tk.Frame(inner)
    days_frame.pack(fill=tk.X, pady=(0, 4))

    tk.Label(days_frame, text="수집 기간:", font=("Segoe UI", 10)).pack(side=tk.LEFT)
    tk.Spinbox(
      days_frame,
      from_=ANALYSIS_DAYS_MIN,
      to=ANALYSIS_DAYS_MAX,
      textvariable=self._days_var,
      width=4,
      font=("Segoe UI", 10),
    ).pack(side=tk.LEFT, padx=(6, 4))
    tk.Label(
      days_frame,
      text=f"일  ({ANALYSIS_DAYS_MIN}~{ANALYSIS_DAYS_MAX}일)",
      font=("Segoe UI", 10),
    ).pack(side=tk.LEFT)

    tk.Label(
      inner,
      text="※  정확한 분석을 위해 7일 이상을 권장합니다.",
      font=("Segoe UI", 9),
      fg="#888888",
      anchor="w",
    ).pack(fill=tk.X, pady=(0, 16))

    tk.Frame(inner, height=1, bg="#cccccc").pack(fill=tk.X, pady=(0, 16))

    # ── 섹션 3: 추천 부품 선택 ────────────────────────────────────────
    tk.Label(
      inner,
      text="추천 부품 선택",
      font=("Segoe UI", 11, "bold"),
      anchor="w",
    ).pack(fill=tk.X, pady=(0, 10))

    level = self.settings_state["knowledge_level"]

    for i, part in enumerate(PARTS):
      part_state = self.settings_state["parts"][part]

      container = tk.Frame(inner)
      container.pack(fill=tk.X, pady=(0, 4))

      # 부품명
      tk.Label(
        container,
        text=part,
        font=("Segoe UI", 10, "bold"),
        anchor="w",
      ).pack(fill=tk.X)

      # 지식 수준별 설명 (동적 업데이트를 위해 참조 저장)
      desc_label = tk.Label(
        container,
        text=PART_DESCRIPTIONS[part][level],
        font=("Segoe UI", 9),
        fg="#555555",
        anchor="w",
        wraplength=500,
        justify=tk.LEFT,
      )
      desc_label.pack(fill=tk.X, pady=(2, 4))
      self._part_desc_labels[part] = desc_label

      # 옵션 라디오버튼
      var = tk.StringVar(value=part_state["option"])
      self._part_vars[part] = var

      radio_frame = tk.Frame(container)
      radio_frame.pack(fill=tk.X, pady=(2, 0))

      radio_widgets = []
      for label, value in PART_OPTIONS:
        rb = tk.Radiobutton(
          radio_frame,
          text=label,
          variable=var,
          value=value,
          font=("Segoe UI", 10),
          command=lambda p=part: self._on_part_option_change(p),
        )
        rb.pack(side=tk.LEFT, padx=(0, 8))
        radio_widgets.append(rb)
      self._part_radio_widgets[part] = radio_widgets

      # 현재 장착 정보 표시 프레임 (유지 선택 시)
      hw_frame = tk.Frame(container)
      self._part_hw_frames[part] = hw_frame

      hw_text = self._hardware_info.get(part, "확인할 수 없음")
      tk.Label(
        hw_frame,
        text=f"현재 장착:  {hw_text}",
        font=("Segoe UI", 9),
        fg="#336699",
        anchor="w",
      ).pack(fill=tk.X)

      # 직접 입력 프레임 (이미 결정 선택 시)
      entry_frame = tk.Frame(container)
      self._part_entry_frames[part] = entry_frame

      tk.Label(entry_frame, text="직접 입력:", font=("Segoe UI", 10)).pack(side=tk.LEFT)
      entry_var = tk.StringVar(value=part_state["manual_input"])
      tk.Entry(
        entry_frame,
        textvariable=entry_var,
        font=("Segoe UI", 10),
        width=34,
      ).pack(side=tk.LEFT, padx=(6, 0))
      self._part_entries[part] = entry_var

      # 저장된 상태에 따라 초기 표시
      if part_state["option"] == "keep":
        hw_frame.pack(fill=tk.X, pady=(4, 0))
      elif part_state["option"] == "decided":
        entry_frame.pack(fill=tk.X, pady=(6, 0))

      if i < len(PARTS) - 1:
        tk.Frame(inner, height=1, bg="#eeeeee").pack(fill=tk.X, pady=(10, 6))

    # 초기 지식 수준에 따른 부품 섹션 상태 반영
    self._on_knowledge_change()

  def _show_monitoring_screen(self):
    self._clear_window()
    self.root.title("BuildSense - 모니터링 중")
    self._center_window(480, 260)

    frame = tk.Frame(self.root, padx=24, pady=20)
    frame.pack(fill=tk.BOTH, expand=True)

    tk.Label(
      frame,
      text="모니터링 실행 중",
      font=("Segoe UI", 14, "bold"),
      anchor="w",
    ).pack(fill=tk.X, pady=(0, 16))

    tk.Label(
      frame,
      text=f"로그 경로:  {USAGE_LOG_PATH}",
      font=("Segoe UI", 9),
      fg="#555555",
      anchor="w",
      wraplength=440,
      justify=tk.LEFT,
    ).pack(fill=tk.X, pady=(0, 6))

    tk.Label(
      frame,
      text=f"분석 기간:  {self.settings_state['analysis_days']}일",
      font=("Segoe UI", 10),
      anchor="w",
    ).pack(fill=tk.X, pady=(0, 20))

    stop_btn = tk.Button(frame, text="모니터링 중지", width=16)

    def _on_stop():
      stop_monitoring_loop()
      stop_btn.config(state=tk.DISABLED, text="모니터링 중지됨")

    stop_btn.config(command=_on_stop)
    stop_btn.pack(anchor="w")

  def _show_review_dialog(self):
    dialog = tk.Toplevel(self.root)
    dialog.title("설정 재점검")
    dialog.resizable(False, False)
    dialog.grab_set()
    self._center_toplevel(dialog, 400, 360)

    frame = tk.Frame(dialog, padx=24, pady=20)
    frame.pack(fill=tk.BOTH, expand=True)

    tk.Label(
      frame,
      text="설정 요약",
      font=("Segoe UI", 12, "bold"),
      anchor="w",
    ).pack(fill=tk.X, pady=(0, 12))

    state = self.settings_state
    kl_label = KNOWLEDGE_LEVEL_LABELS.get(
      state["knowledge_level"], state["knowledge_level"]
    )

    tk.Label(
      frame,
      text=f"컴퓨터 지식 수준:  {kl_label}",
      font=("Segoe UI", 10),
      anchor="w",
    ).pack(fill=tk.X)

    tk.Label(
      frame,
      text=f"분석 기간:  {state['analysis_days']}일",
      font=("Segoe UI", 10),
      anchor="w",
    ).pack(fill=tk.X, pady=(4, 12))

    tk.Label(
      frame,
      text="추천 부품 선택:",
      font=("Segoe UI", 10, "bold"),
      anchor="w",
    ).pack(fill=tk.X, pady=(0, 4))

    for part in PARTS:
      part_state = state["parts"][part]
      option_label = PART_OPTION_LABELS.get(part_state["option"], part_state["option"])
      text = f"  {part}:  {option_label}"
      if part_state["option"] == "decided" and part_state["manual_input"]:
        text += f"  ({part_state['manual_input']})"
      elif part_state["option"] == "keep":
        hw = self._hardware_info.get(part, "")
        if hw:
          text += f"  ({hw})"
      tk.Label(
        frame,
        text=text,
        font=("Segoe UI", 10),
        anchor="w",
      ).pack(fill=tk.X)

    btn_frame = tk.Frame(frame)
    btn_frame.pack(fill=tk.X, pady=(16, 0))

    tk.Button(
      btn_frame,
      text="수정하기",
      width=12,
      command=dialog.destroy,
    ).pack(side=tk.RIGHT, padx=(8, 0))

    def _on_start():
      result = validate_parts_not_all_keep(self.settings_state["parts"])
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
      self._show_monitoring_screen()

    tk.Button(
      btn_frame,
      text="분석 시작",
      width=12,
      command=_on_start,
    ).pack(side=tk.RIGHT)

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
    widget_state = tk.DISABLED if is_beginner else tk.NORMAL

    for part in PARTS:
      # 설명 텍스트 실시간 업데이트
      if part in self._part_desc_labels:
        self._part_desc_labels[part].config(text=PART_DESCRIPTIONS[part][level])

      # 라디오버튼 활성화 상태 변경
      for rb in self._part_radio_widgets.get(part, []):
        rb.config(state=widget_state)

      # 전혀 모름: 모든 부품을 추천으로 초기화하고 하위 프레임 숨김
      if is_beginner:
        self._part_vars[part].set("recommend")
        self._part_entry_frames[part].pack_forget()
        self._part_hw_frames[part].pack_forget()

  def _on_part_option_change(self, part: str):
    value = self._part_vars[part].get()
    entry_frame = self._part_entry_frames[part]
    hw_frame = self._part_hw_frames[part]

    entry_frame.pack_forget()
    hw_frame.pack_forget()

    if value == "keep":
      hw_frame.pack(fill=tk.X, pady=(4, 0))
    elif value == "decided":
      entry_frame.pack(fill=tk.X, pady=(6, 0))

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
      self.settings_state["parts"][part]["manual_input"] = self._part_entries[part].get()

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
