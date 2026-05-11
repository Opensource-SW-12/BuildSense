import json
from pathlib import Path

from src.config import DATA_DIR, LOGS_DIR, REPORTS_DIR, USER_PROFILE_PATH, USAGE_LOG_PATH


def ensure_app_directories() -> None:
  DATA_DIR.mkdir(parents=True, exist_ok=True)
  LOGS_DIR.mkdir(parents=True, exist_ok=True)
  REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def get_user_profile_path() -> Path:
  return USER_PROFILE_PATH


def get_usage_log_path() -> Path:
  return USAGE_LOG_PATH


def get_reports_dir() -> Path:
  return REPORTS_DIR


def save_user_profile(profile: dict) -> None:
  DATA_DIR.mkdir(parents=True, exist_ok=True)
  with open(USER_PROFILE_PATH, "w", encoding="utf-8") as f:
    json.dump(profile, f, ensure_ascii=False, indent=2)
