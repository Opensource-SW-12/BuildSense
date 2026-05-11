KNOWLEDGE_LEVELS = [
  ("전혀 모름", "beginner"),
  ("어느 정도 알고 있음", "intermediate"),
  ("잘 알고 있음", "advanced"),
]

ANALYSIS_DAYS_MIN = 3
ANALYSIS_DAYS_MAX = 28
ANALYSIS_DAYS_DEFAULT = 7

PARTS = ["CPU", "GPU", "RAM", "SSD/HDD", "파워"]

PART_OPTIONS = [
  ("추천", "recommend"),
  ("제외", "exclude"),
  ("유지", "keep"),
  ("이미 결정", "decided"),
]


KNOWLEDGE_LEVEL_LABELS = {value: label for label, value in KNOWLEDGE_LEVELS}
PART_OPTION_LABELS = {value: label for label, value in PART_OPTIONS}


def build_settings_state() -> dict:
  return {
    "knowledge_level": "beginner",
    "analysis_days": ANALYSIS_DAYS_DEFAULT,
    "parts": {
      part: {"option": "recommend", "manual_input": ""}
      for part in PARTS
    },
  }
