from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
REPORTS_DIR = BASE_DIR / "reports"
ANALYSIS_DIR = BASE_DIR / "analysis"
EXPORTS_DIR = BASE_DIR / "exports"

USER_PROFILE_PATH = DATA_DIR / "user_profile.json"
USAGE_LOG_PATH = LOGS_DIR / "usage.jsonl"
