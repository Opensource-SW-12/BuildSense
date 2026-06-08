KNOWLEDGE_LEVELS = [
  ("전혀 모름", "beginner"),
  ("어느 정도 알고 있음", "intermediate"),
  ("잘 알고 있음", "advanced"),
]

ANALYSIS_DAYS_MIN = 3
ANALYSIS_DAYS_MAX = 30
ANALYSIS_DAYS_DEFAULT = 7

PARTS = ["CPU", "GPU", "RAM", "SSD", "HDD", "메인보드", "파워"]

PART_OPTIONS = [
  ("추천", "recommend"),
  ("유지", "keep"),
]

KNOWLEDGE_LEVEL_LABELS = {value: label for label, value in KNOWLEDGE_LEVELS}
PART_OPTION_LABELS = {value: label for label, value in PART_OPTIONS}

PART_DESCRIPTIONS = {
  "CPU": {
    "beginner":     "전반적인 처리 속도를 담당합니다. 게임·영상 작업에 영향을 줍니다.",
    "intermediate": "클록 속도와 코어 수가 멀티태스킹 성능에 영향을 줍니다.",
    "advanced":     "IPC·클록·코어 수가 워크로드별 성능 병목을 결정합니다.",
  },
  "GPU": {
    "beginner":     "게임 화면과 영상을 처리합니다.",
    "intermediate": "3D 렌더링, 게임, 영상 편집 성능을 결정합니다.",
    "advanced":     "VRAM 용량과 셰이더 처리량이 렌더링 성능에 직결됩니다.",
  },
  "RAM": {
    "beginner":     "여러 프로그램을 동시에 실행할 때 필요합니다.",
    "intermediate": "용량과 속도(MHz)가 멀티태스킹 성능에 영향을 줍니다.",
    "advanced":     "용량·클록·CAS 레이턴시가 대역폭과 응답성을 결정합니다.",
  },
  "SSD": {
    "beginner":     "운영체제와 프로그램이 빠르게 실행되도록 저장합니다.",
    "intermediate": "빠른 읽기·쓰기 속도로 부팅과 로딩을 단축합니다.",
    "advanced":     "NVMe PCIe Gen4/5 순차 읽기·쓰기 속도가 체감 성능을 좌우합니다.",
  },
  "HDD": {
    "beginner":     "사진, 영상 등 대용량 파일을 저장하는 공간입니다.",
    "intermediate": "대용량 저장에 적합하며 SSD보다 가격 대비 용량이 큽니다.",
    "advanced":     "RPM·캐시 크기·플래터 밀도가 순차 처리량을 결정합니다.",
  },
  "메인보드": {
    "beginner":     "CPU·RAM·저장장치를 연결하는 기판입니다. CPU 소켓이 맞아야 장착됩니다.",
    "intermediate": "칩셋과 소켓이 CPU 호환성을 결정하며, RAM 슬롯·M.2 수가 확장성에 영향을 줍니다.",
    "advanced":     "칩셋 등급(Z/X/B/H)이 오버클럭·PCIe 레인·M.2 슬롯 수를 결정합니다.",
  },
  "파워": {
    "beginner":     "컴퓨터에 전기를 공급하는 부품입니다.",
    "intermediate": "와트 수와 80PLUS 등급이 안정성과 전력 효율에 영향을 줍니다.",
    "advanced":     "TDP 기반 여유 용량 계산과 레일 전류 스펙이 시스템 안정성의 핵심입니다.",
  },
}


def build_settings_state() -> dict:
  parts = {part: {"option": "recommend"} for part in PARTS}
  return {
    "knowledge_level": "intermediate",
    "analysis_days": ANALYSIS_DAYS_DEFAULT,
    "parts": parts,
  }
