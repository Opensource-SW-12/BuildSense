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
  ANALYSIS_DAYS_DEFAULT,
  PARTS,
  PART_OPTIONS,
  PART_OPTION_LABELS,
  build_settings_state,
)

SETTINGS_TITLE = "BuildSense - 사용자 설정"


class BuildSenseApp:
  def __init__(self):
    self.root = tk.Tk()
    self.consent_state = build_consent_state()
    self.settings_state = build_settings_state()
    self._knowledge_var = None
    self._days_var = None
    self._part_vars = {}
    self._part_entries = {}
    self._part_entry_frames = {}
    self._part_radio_widgets = {}
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
    self._center_window(560, 400)

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

    btn_frame = tk.Frame(frame)
    btn_frame.pack(fill=tk.X, pady=(16, 0))

    tk.Button(
      btn_frame,
      text="거부",
      width=12,
      command=self._on_decline,
    ).pack(side=tk.RIGHT, padx=(8, 0))

    tk.Button(
      btn_frame,
      text="동의",
      width=12,
      command=self._on_agree,
    ).pack(side=tk.RIGHT)

  def _show_settings_screen(self):
    self._clear_window()
    self.root.title(SETTINGS_TITLE)
    self.root.resizable(False, False)
    self._center_window(580, 580)

    self._part_vars = {}
    self._part_entries = {}
    self._part_entry_frames = {}
    self._part_radio_widgets = {}

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
      lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
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
    days_frame.pack(fill=tk.X, pady=(0, 16))

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

    tk.Frame(inner, height=1, bg="#cccccc").pack(fill=tk.X, pady=(0, 16))

    # ── 섹션 3: 추천 부품 선택 ────────────────────────────────────────
    tk.Label(
      inner,
      text="추천 부품 선택",
      font=("Segoe UI", 11, "bold"),
      anchor="w",
    ).pack(fill=tk.X, pady=(0, 10))

    for i, part in enumerate(PARTS):
      part_state = self.settings_state["parts"][part]

      container = tk.Frame(inner)
      container.pack(fill=tk.X, pady=(0, 4))

      tk.Label(
        container,
        text=part,
        font=("Segoe UI", 10, "bold"),
        anchor="w",
      ).pack(fill=tk.X)

      var = tk.StringVar(value=part_state["option"])
      self._part_vars[part] = var

      radio_frame = tk.Frame(container)
      radio_frame.pack(fill=tk.X, pady=(4, 0))

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

      # "이미 결정" 선택 시에만 표시되는 직접 입력 필드
      entry_frame = tk.Frame(container)
      self._part_entry_frames[part] = entry_frame

      tk.Label(entry_frame, text="직접 입력:", font=("Segoe UI", 10)).pack(side=tk.LEFT)
      entry_var = tk.StringVar(value=part_state["manual_input"])
      tk.Entry(
        entry_frame,
        textvariable=entry_var,
        font=("Segoe UI", 10),
        width=36,
      ).pack(side=tk.LEFT, padx=(6, 0))
      self._part_entries[part] = entry_var

      if part_state["option"] == "decided":
        entry_frame.pack(fill=tk.X, pady=(6, 0))

      if i < len(PARTS) - 1:
        tk.Frame(inner, height=1, bg="#eeeeee").pack(fill=tk.X, pady=(8, 4))

    # 초기 지식 수준에 따른 부품 섹션 상태 반영
    self._on_knowledge_change()

  def _show_analysis_placeholder(self):
    self._clear_window()
    self.root.title("BuildSense - 분석 준비")
    self._center_window(480, 240)

    frame = tk.Frame(self.root, padx=24, pady=20)
    frame.pack(fill=tk.BOTH, expand=True)

    tk.Label(
      frame,
      text="분석 준비",
      font=("Segoe UI", 14, "bold"),
      anchor="w",
    ).pack(fill=tk.X, pady=(0, 12))

    tk.Label(
      frame,
      text="설정이 완료되었습니다. 분석 화면은 추후 구현 예정입니다.",
      font=("Segoe UI", 10),
      anchor="w",
    ).pack(fill=tk.X)

  def _show_review_dialog(self):
    dialog = tk.Toplevel(self.root)
    dialog.title("설정 재점검")
    dialog.resizable(False, False)
    dialog.grab_set()
    self._center_toplevel(dialog, 400, 340)

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

    tk.Button(
      btn_frame,
      text="분석 시작",
      width=12,
      command=lambda: [dialog.destroy(), self._show_analysis_placeholder()],
    ).pack(side=tk.RIGHT)

  # ------------------------------------------------------------------
  # 버튼 핸들러
  # ------------------------------------------------------------------

  def _on_agree(self):
    record_agreement(self.consent_state)
    self._show_settings_screen()

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
    is_beginner = self._knowledge_var.get() == "beginner"
    widget_state = tk.DISABLED if is_beginner else tk.NORMAL
    for part in PARTS:
      for rb in self._part_radio_widgets[part]:
        rb.config(state=widget_state)
      if is_beginner:
        self._part_vars[part].set("recommend")
        self._part_entry_frames[part].pack_forget()

  def _on_part_option_change(self, part: str):
    value = self._part_vars[part].get()
    entry_frame = self._part_entry_frames[part]
    if value == "decided":
      entry_frame.pack(fill=tk.X, pady=(6, 0))
    else:
      entry_frame.pack_forget()

  # ------------------------------------------------------------------
  # 검증 및 상태 동기화
  # ------------------------------------------------------------------

  def _validate_days(self) -> bool:
    try:
      days = int(self._days_var.get())
    except (ValueError, tk.TclError):
      messagebox.showwarning(
        title="입력 오류",
        message=(
          "분석 기간은 숫자로 입력해야 합니다.\n"
          f"기본값({ANALYSIS_DAYS_DEFAULT}일)으로 재설정합니다."
        ),
      )
      self._days_var.set(ANALYSIS_DAYS_DEFAULT)
      return False

    if days < ANALYSIS_DAYS_MIN:
      messagebox.showwarning(
        title="입력 오류",
        message=(
          f"분석 기간은 최소 {ANALYSIS_DAYS_MIN}일 이상이어야 합니다.\n"
          f"{ANALYSIS_DAYS_MIN}일로 재설정합니다."
        ),
      )
      self._days_var.set(ANALYSIS_DAYS_MIN)
      return False

    if days > ANALYSIS_DAYS_MAX:
      messagebox.showwarning(
        title="입력 오류",
        message=(
          f"분석 기간은 최대 {ANALYSIS_DAYS_MAX}일까지 가능합니다.\n"
          f"{ANALYSIS_DAYS_MAX}일로 재설정합니다."
        ),
      )
      self._days_var.set(ANALYSIS_DAYS_MAX)
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
