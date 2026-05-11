import tkinter as tk
from datetime import datetime, timedelta, timezone

from src.settings import KNOWLEDGE_LEVEL_LABELS, PART_OPTION_LABELS
from src.storage import (
  read_user_profile,
  get_usage_log_line_count,
  get_usage_log_first_timestamp,
  delete_all_monitoring_data,
  write_abort_signal,
)


def show_instance_status_window() -> None:
  root = tk.Tk()
  root.title("BuildSense - 모니터링 상태")
  root.resizable(False, False)

  _center(root, 520, 620)
  _build_ui(root)
  root.mainloop()


def _center(root: tk.Tk, w: int, h: int) -> None:
  root.update_idletasks()
  sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
  root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")


def _build_ui(root: tk.Tk) -> None:
  outer = tk.Frame(root)
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
    lambda e: inner.after_idle(lambda: canvas.configure(scrollregion=canvas.bbox("all"))),
  )
  canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))
  canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", lambda ev: canvas.yview_scroll(int(-1 * ev.delta / 120), "units")))
  canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

  _section_header(inner)
  _section_status(inner)
  _section_settings(inner)
  _section_abort(inner, root)

  tk.Frame(inner, height=8).pack()
  tk.Button(inner, text="닫기", width=10, command=root.destroy).pack(anchor="e")


def _section_header(parent: tk.Frame) -> None:
  tk.Label(
    parent,
    text="BuildSense 실행 중",
    font=("Segoe UI", 14, "bold"),
    anchor="w",
  ).pack(fill=tk.X, pady=(0, 4))
  tk.Label(
    parent,
    text="현재 다른 프로세스에서 모니터링이 진행 중입니다.",
    font=("Segoe UI", 10),
    fg="#555555",
    anchor="w",
  ).pack(fill=tk.X, pady=(0, 14))


def _section_status(parent: tk.Frame) -> None:
  frame = tk.LabelFrame(parent, text="모니터링 현황", font=("Segoe UI", 10, "bold"), padx=12, pady=8)
  frame.pack(fill=tk.X, pady=(0, 10))

  profile = read_user_profile()
  line_count = get_usage_log_line_count()
  first_ts = get_usage_log_first_timestamp()

  start_str = "알 수 없음"
  remaining_str = "알 수 없음"

  if first_ts:
    try:
      start_dt = datetime.fromisoformat(first_ts)
      start_str = start_dt.astimezone().strftime("%Y-%m-%d %H:%M")
      if profile:
        end_dt = start_dt + timedelta(days=profile.get("analysis_days", 7))
        remaining = end_dt - datetime.now(timezone.utc)
        remaining_str = f"{max(0, remaining.days)}일"
    except Exception:
      pass

  _info_row(frame, "시작 일시:", start_str)
  _info_row(frame, "수집된 데이터:", f"{line_count:,}개 스냅샷")
  _info_row(frame, "남은 기간:", remaining_str)


def _section_settings(parent: tk.Frame) -> None:
  profile = read_user_profile()
  if not profile:
    return

  frame = tk.LabelFrame(parent, text="사용자 설정", font=("Segoe UI", 10, "bold"), padx=12, pady=8)
  frame.pack(fill=tk.X, pady=(0, 10))

  kl = KNOWLEDGE_LEVEL_LABELS.get(profile.get("knowledge_level", ""), "-")
  _info_row(frame, "컴퓨터 지식 수준:", kl)
  _info_row(frame, "분석 기간:", f"{profile.get('analysis_days', '-')}일")

  parts = profile.get("parts", {})
  if parts:
    tk.Label(frame, text="부품 선택:", font=("Segoe UI", 10), anchor="w").pack(fill=tk.X, pady=(6, 2))
    for part, state in parts.items():
      option = PART_OPTION_LABELS.get(state.get("option", ""), "-")
      text = f"  {part}:  {option}"
      if state.get("manual_input"):
        text += f"  ({state['manual_input']})"
      tk.Label(frame, text=text, font=("Segoe UI", 9), fg="#444444", anchor="w").pack(fill=tk.X)


def _section_abort(parent: tk.Frame, root: tk.Tk) -> None:
  frame = tk.LabelFrame(parent, text="중도 종료", font=("Segoe UI", 10, "bold"), padx=12, pady=8)
  frame.pack(fill=tk.X, pady=(0, 10))

  tk.Label(
    frame,
    text="지금까지 저장된 데이터가 모두 삭제되며 분석을 포기합니다.",
    font=("Segoe UI", 9),
    fg="#cc3300",
    anchor="w",
    wraplength=450,
    justify=tk.LEFT,
  ).pack(fill=tk.X, pady=(0, 10))

  confirm_var = tk.StringVar(value="no")

  abort_btn = tk.Button(frame, text="종료", width=10, state=tk.DISABLED)

  def _on_choice():
    abort_btn.config(state=tk.NORMAL if confirm_var.get() == "yes" else tk.DISABLED)

  radio_frame = tk.Frame(frame)
  radio_frame.pack(anchor="w", pady=(0, 8))
  tk.Label(radio_frame, text="정말로 종료할까요?  ", font=("Segoe UI", 10)).pack(side=tk.LEFT)
  tk.Radiobutton(radio_frame, text="아니오", variable=confirm_var, value="no",  font=("Segoe UI", 10), command=_on_choice).pack(side=tk.LEFT)
  tk.Radiobutton(radio_frame, text="네",    variable=confirm_var, value="yes", font=("Segoe UI", 10), command=_on_choice).pack(side=tk.LEFT, padx=(8, 0))

  def _on_abort():
    delete_all_monitoring_data()
    write_abort_signal()
    for w in root.winfo_children():
      w.destroy()
    root.geometry("360x180")
    done = tk.Frame(root, padx=24, pady=30)
    done.pack(fill=tk.BOTH, expand=True)
    tk.Label(done, text="분석이 종료되었습니다.", font=("Segoe UI", 13, "bold"), anchor="center").pack(expand=True)
    tk.Button(done, text="확인", width=12, command=root.destroy).pack(pady=(12, 0))

  abort_btn.config(command=_on_abort)
  abort_btn.pack(anchor="w")


def _info_row(parent: tk.Frame, label: str, value: str) -> None:
  row = tk.Frame(parent)
  row.pack(fill=tk.X, pady=2)
  tk.Label(row, text=label, font=("Segoe UI", 10), anchor="w", width=16).pack(side=tk.LEFT)
  tk.Label(row, text=value, font=("Segoe UI", 10), anchor="w").pack(side=tk.LEFT)
