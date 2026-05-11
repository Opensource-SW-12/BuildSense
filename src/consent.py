CONSENT_TITLE = "BuildSense - Data Collection Consent"

CONSENT_BODY = (
  "BuildSense collects PC usage data to generate a personalized hardware\n"
  "recommendation report.\n"
  "\n"
  "All data is stored only on this device.\n"
  "Nothing is sent to any external server.\n"
  "\n"
  "Data collected during the analysis period:\n"
  "  - CPU usage\n"
  "  - RAM usage\n"
  "  - NVIDIA GPU usage\n"
  "  - VRAM usage\n"
  "  - Running process list\n"
  "  - System uptime\n"
  "  - Current hardware information\n"
  "\n"
  "You can decline at any time. If you decline, the program will close\n"
  "and no data will be collected."
)

DECLINE_MESSAGE = (
  "You declined the data collection consent.\n"
  "BuildSense will now close."
)


def build_consent_state() -> dict:
  return {"agreed": False}


def record_agreement(state: dict) -> None:
  state["agreed"] = True


def record_decline(state: dict) -> None:
  state["agreed"] = False
