from src.app import BuildSenseApp
from src.storage import ensure_app_directories
from src.background import acquire_single_instance_lock
from src.instance_status import show_instance_status_window


def main():
  if not acquire_single_instance_lock():
    show_instance_status_window()
    return

  ensure_app_directories()
  app = BuildSenseApp()
  app.run()


if __name__ == "__main__":
  main()
