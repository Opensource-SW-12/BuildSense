from dotenv import load_dotenv
load_dotenv()

from src.app import BuildSenseApp
from src.storage import ensure_app_directories
from src.background import acquire_single_instance_lock
from src.instance_status import show_instance_status_window
from src.startup_state import detect_startup_state


def main():
  if not acquire_single_instance_lock():
    show_instance_status_window()
    return

  ensure_app_directories()
  state = detect_startup_state()
  app = BuildSenseApp(startup_state=state)
  app.run()


if __name__ == "__main__":
  main()
