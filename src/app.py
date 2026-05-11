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
  ANALYSIS_DAYS_MIN,
  ANALYSIS_DAYS_MAX,
  PARTS,
  PART_OPTIONS,
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

    self._part_vars = {}
    self._part_entries = {}
    self._part_entry_frames = {}

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

      for label, value in PART_OPTIONS:
        tk.Radiobutton(
          radio_frame,
          text=label,
          variable=var,
          value=value,
          font=("Segoe UI", 10),
          command=lambda p=part: self._on_part_option_change(p),
        ).pack(side=tk.LEFT, padx=(0, 8))

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
    self._sync_settings_state()
    self._show_analysis_placeholder()

  def _on_part_option_change(self, part: str):
    value = self._part_vars[part].get()
    entry_frame = self._part_entry_frames[part]
    if value == "decided":
      entry_frame.pack(fill=tk.X, pady=(6, 0))
    else:
      entry_frame.pack_forget()

  # ------------------------------------------------------------------
  # 상태 동기화
  # ------------------------------------------------------------------

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
