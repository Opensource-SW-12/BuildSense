from datetime import datetime, timedelta, timezone
from enum import Enum

from src.storage import read_user_profile, get_usage_log_first_timestamp


class StartupState(Enum):
  FRESH   = "fresh"
  RESUME  = "resume"
  ANALYZE = "analyze"


def detect_startup_state() -> StartupState:
  profile = read_user_profile()
  if profile is None:
    return StartupState.FRESH

  first_ts = get_usage_log_first_timestamp()
  if first_ts is None:
    return StartupState.FRESH

  try:
    start_dt = datetime.fromisoformat(first_ts)
    end_dt = start_dt + timedelta(days=profile.get("analysis_days", 7))
    if datetime.now(timezone.utc) >= end_dt:
      return StartupState.ANALYZE
    return StartupState.RESUME
  except Exception:
    return StartupState.FRESH
