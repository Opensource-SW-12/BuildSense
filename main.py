import sys
from pathlib import Path
from dotenv import load_dotenv

_base = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
load_dotenv(_base / ".env")

from src.app import BuildSenseApp
from src.storage import ensure_app_directories
from src.background import acquire_single_instance_lock
from src.instance_status import show_instance_status_window
from src.startup_state import detect_startup_state
from src.startup_registry import unregister_startup


def main():
  if "--unregister-startup" in sys.argv:
    unregister_startup()
    return

  if not acquire_single_instance_lock():
    show_instance_status_window()
    return

  ensure_app_directories()
  state = detect_startup_state()
  app = BuildSenseApp(startup_state=state)
  app.run()


if __name__ == "__main__":
  main()
