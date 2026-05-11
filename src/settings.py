KNOWLEDGE_LEVELS = [
  ("초보자", "beginner"),
  ("중급자", "intermediate"),
  ("고급자", "advanced"),
]

ANALYSIS_DAYS_MIN = 3
ANALYSIS_DAYS_MAX = 28
ANALYSIS_DAYS_DEFAULT = 7

PARTS = ["CPU", "GPU", "RAM", "SSD/HDD", "파워"]

PART_OPTIONS = [
  ("추천", "recommend"),
  ("제외", "exclude"),
  ("현재 유지", "keep"),
  ("이미 결정", "decided"),
]


def build_settings_state() -> dict:
  return {
    "knowledge_level": "beginner",
    "analysis_days": ANALYSIS_DAYS_DEFAULT,
    "parts": {
      part: {"option": "recommend", "manual_input": ""}
      for part in PARTS
    },
  }
