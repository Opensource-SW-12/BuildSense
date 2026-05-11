import tkinter as tk
from tkinter import messagebox

from src.app import BuildSenseApp
from src.storage import ensure_app_directories
from src.background import acquire_single_instance_lock


def main():
  if not acquire_single_instance_lock():
    root = tk.Tk()
    root.withdraw()
    messagebox.showwarning("BuildSense", "BuildSense가 이미 실행 중입니다.")
    root.destroy()
    return

  ensure_app_directories()
  app = BuildSenseApp()
  app.run()


if __name__ == "__main__":
  main()
