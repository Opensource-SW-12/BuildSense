import json
from pathlib import Path

from src.config import DATA_DIR, LOGS_DIR, REPORTS_DIR, ANALYSIS_DIR, EXPORTS_DIR, SPECS_DIR, PRICES_DIR, USER_PROFILE_PATH, USER_PREFERENCES_PATH, USAGE_LOG_PATH


def ensure_app_directories() -> None:
  DATA_DIR.mkdir(parents=True, exist_ok=True)
  LOGS_DIR.mkdir(parents=True, exist_ok=True)
  REPORTS_DIR.mkdir(parents=True, exist_ok=True)
  ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
  EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
  SPECS_DIR.mkdir(parents=True, exist_ok=True)
  PRICES_DIR.mkdir(parents=True, exist_ok=True)


def get_user_profile_path() -> Path:
  return USER_PROFILE_PATH


def get_usage_log_path() -> Path:
  return USAGE_LOG_PATH


def get_reports_dir() -> Path:
  return REPORTS_DIR


def ensure_reports_directory() -> None:
  REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def get_report_path(filename: str) -> Path:
  return REPORTS_DIR / filename


_log_line_count: int = 0


def init_log_line_count() -> None:
  """RESUME 상태 진입 시 파일에서 초기값을 읽어 카운터를 설정한다."""
  global _log_line_count
  _log_line_count = get_usage_log_line_count()


def get_log_line_count() -> int:
  return _log_line_count


def append_usage_log(snapshot: dict) -> None:
  global _log_line_count
  try:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(USAGE_LOG_PATH, "a", encoding="utf-8") as f:
      f.write(json.dumps(snapshot, ensure_ascii=False) + "\n")
    _log_line_count += 1
  except Exception:
    pass


def save_user_profile(profile: dict) -> None:
  DATA_DIR.mkdir(parents=True, exist_ok=True)
  with open(USER_PROFILE_PATH, "w", encoding="utf-8") as f:
    json.dump(profile, f, ensure_ascii=False, indent=2)


def save_user_preferences(prefs: dict) -> None:
  DATA_DIR.mkdir(parents=True, exist_ok=True)
  with open(USER_PREFERENCES_PATH, "w", encoding="utf-8") as f:
    json.dump(prefs, f, ensure_ascii=False, indent=2)


def load_user_preferences() -> dict | None:
  try:
    if not USER_PREFERENCES_PATH.exists():
      return None
    with open(USER_PREFERENCES_PATH, "r", encoding="utf-8") as f:
      return json.load(f)
  except Exception:
    return None


def read_user_profile() -> dict | None:
  try:
    if not USER_PROFILE_PATH.exists():
      return None
    with open(USER_PROFILE_PATH, "r", encoding="utf-8") as f:
      return json.load(f)
  except Exception:
    return None


def get_usage_log_line_count() -> int:
  try:
    if not USAGE_LOG_PATH.exists():
      return 0
    with open(USAGE_LOG_PATH, "r", encoding="utf-8") as f:
      return sum(1 for _ in f)
  except Exception:
    return 0


def get_usage_log_first_timestamp() -> str | None:
  try:
    if not USAGE_LOG_PATH.exists():
      return None
    with open(USAGE_LOG_PATH, "r", encoding="utf-8") as f:
      first_line = f.readline().strip()
    if first_line:
      return json.loads(first_line).get("timestamp")
    return None
  except Exception:
    return None


def delete_all_monitoring_data() -> None:
  global _log_line_count
  for path in (USAGE_LOG_PATH, USER_PROFILE_PATH):
    try:
      if path.exists():
        path.unlink()
    except Exception:
      pass
  _log_line_count = 0


_ABORT_SIGNAL_PATH = DATA_DIR / "buildsense_abort.signal"


def write_abort_signal() -> None:
  try:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    _ABORT_SIGNAL_PATH.touch()
  except Exception:
    pass


def check_and_clear_abort_signal() -> bool:
  try:
    if _ABORT_SIGNAL_PATH.exists():
      _ABORT_SIGNAL_PATH.unlink()
      return True
    return False
  except Exception:
    return False
