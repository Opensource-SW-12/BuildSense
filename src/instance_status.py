import tkinter as tk

from src.app import BG, WHITE, BTN_CONT_ON, _pill


def show_instance_status_window() -> None:
  root = tk.Tk()
  root.title("BuildSense")
  root.resizable(False, False)
  root.configure(bg=BG)

  _center(root, 380, 200)

  body = tk.Frame(root, bg=BG, padx=24, pady=30)
  body.pack(fill=tk.BOTH, expand=True)

  tk.Label(body, text="이미 프로그램이 실행중입니다.", fg=WHITE, bg=BG,
           font=("Segoe UI", 13, "bold")).pack(expand=True)

  close_btn = _pill(body, "닫기", BTN_CONT_ON, WHITE, width=120)
  close_btn.pack(pady=(8, 0))
  close_btn.bind("<Button-1>", lambda e: root.destroy())

  root.mainloop()


def _center(root: tk.Tk, w: int, h: int) -> None:
  root.update_idletasks()
  sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
  root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
