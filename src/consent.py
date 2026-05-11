CONSENT_TITLE = "BuildSense - 데이터 수집 동의"

CONSENT_BODY = (
  "BuildSense는 맞춤형 하드웨어 추천 보고서를 생성하기 위해\n"
  "PC 사용 데이터를 수집합니다.\n"
  "\n"
  "모든 데이터는 이 기기에만 저장됩니다.\n"
  "외부 서버로 전송되는 정보는 없습니다.\n"
  "\n"
  "분석 기간 동안 수집되는 데이터:\n"
  "  - CPU 사용률\n"
  "  - RAM 사용량\n"
  "  - NVIDIA GPU 사용률\n"
  "  - VRAM 사용량\n"
  "  - 실행 중인 프로세스 목록\n"
  "  - 시스템 가동 시간\n"
  "  - 현재 하드웨어 정보\n"
  "\n"
  "언제든지 거부할 수 있습니다. 거부하면 프로그램이 종료되며\n"
  "어떠한 데이터도 수집되지 않습니다."
)

DECLINE_MESSAGE = (
  "데이터 수집 동의를 거부하셨습니다.\n"
  "BuildSense를 종료합니다."
)


def build_consent_state() -> dict:
  return {"agreed": False}


def record_agreement(state: dict) -> None:
  state["agreed"] = True


def record_decline(state: dict) -> None:
  state["agreed"] = False
