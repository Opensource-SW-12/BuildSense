import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
USER_PROFILE_PATH = DATA_DIR / "user_profile.json"


def save_user_profile(profile: dict) -> None:
  DATA_DIR.mkdir(parents=True, exist_ok=True)
  with open(USER_PROFILE_PATH, "w", encoding="utf-8") as f:
    json.dump(profile, f, ensure_ascii=False, indent=2)
