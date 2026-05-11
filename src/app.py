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


class BuildSenseApp:
  def __init__(self):
    self.root = tk.Tk()
    self.consent_state = build_consent_state()
    self._show_consent_screen()

  def run(self):
    self.root.mainloop()

  # ------------------------------------------------------------------
  # Screens
  # ------------------------------------------------------------------

  def _show_consent_screen(self):
    self.root.title(CONSENT_TITLE)
    self.root.resizable(False, False)
    self._center_window(560, 400)

    frame = tk.Frame(self.root, padx=24, pady=20)
    frame.pack(fill=tk.BOTH, expand=True)

    tk.Label(
      frame,
      text="Data Collection Consent",
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
      text="Decline",
      width=12,
      command=self._on_decline,
    ).pack(side=tk.RIGHT, padx=(8, 0))

    tk.Button(
      btn_frame,
      text="Agree",
      width=12,
      command=self._on_agree,
    ).pack(side=tk.RIGHT)

  def _show_setup_placeholder(self):
    for widget in self.root.winfo_children():
      widget.destroy()

    self.root.title("BuildSense - Setup")
    self._center_window(480, 240)

    frame = tk.Frame(self.root, padx=24, pady=20)
    frame.pack(fill=tk.BOTH, expand=True)

    tk.Label(
      frame,
      text="Setup",
      font=("Segoe UI", 14, "bold"),
      anchor="w",
    ).pack(fill=tk.X, pady=(0, 12))

    tk.Label(
      frame,
      text="Consent recorded. Setup screen coming soon.",
      font=("Segoe UI", 10),
      anchor="w",
    ).pack(fill=tk.X)

  # ------------------------------------------------------------------
  # Button handlers
  # ------------------------------------------------------------------

  def _on_agree(self):
    record_agreement(self.consent_state)
    self._show_setup_placeholder()

  def _on_decline(self):
    record_decline(self.consent_state)
    messagebox.showinfo(title="BuildSense", message=DECLINE_MESSAGE)
    self.root.destroy()

  # ------------------------------------------------------------------
  # Helpers
  # ------------------------------------------------------------------

  def _center_window(self, width: int, height: int):
    self.root.update_idletasks()
    sw = self.root.winfo_screenwidth()
    sh = self.root.winfo_screenheight()
    x = (sw - width) // 2
    y = (sh - height) // 2
    self.root.geometry(f"{width}x{height}+{x}+{y}")
