from src.app import BuildSenseApp
from src.storage import ensure_app_directories


def main():
  ensure_app_directories()
  app = BuildSenseApp()
  app.run()


if __name__ == "__main__":
  main()
