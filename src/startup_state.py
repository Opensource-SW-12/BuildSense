from datetime import datetime, timedelta, timezone
from enum import Enum

from src.storage import read_user_profile, get_usage_log_first_timestamp


class StartupState(Enum):
  FRESH   = "fresh"
  RESUME  = "resume"
  ANALYZE = "analyze"


def is_analysis_period_elapsed(profile: dict, first_ts: str) -> bool:
  """모니터링 시작 시각(first_ts) 기준으로 analysis_days가 지났는지 판별한다.
  앱을 재시작할 때(detect_startup_state)뿐 아니라, 앱이 재부팅 없이 계속 켜져
  있는 동안에도 모니터링 화면에서 주기적으로 호출되어야 한다 — 그렇지 않으면
  PC가 분석 기간 내내 재부팅되지 않을 경우 분석 종료 화면이 영원히 뜨지 않는다."""
  start_dt = datetime.fromisoformat(first_ts)
  end_dt = start_dt + timedelta(days=profile.get("analysis_days", 7))
  return datetime.now(timezone.utc) >= end_dt


def detect_startup_state() -> StartupState:
  profile = read_user_profile()
  if profile is None:
    return StartupState.FRESH

  first_ts = get_usage_log_first_timestamp()
  if first_ts is None:
    return StartupState.FRESH

  try:
    if is_analysis_period_elapsed(profile, first_ts):
      return StartupState.ANALYZE
    return StartupState.RESUME
  except Exception:
    return StartupState.FRESH
