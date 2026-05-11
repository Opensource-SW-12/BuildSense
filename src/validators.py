from dataclasses import dataclass
from enum import Enum

from src.settings import ANALYSIS_DAYS_MIN, ANALYSIS_DAYS_MAX, ANALYSIS_DAYS_DEFAULT, PARTS


# ------------------------------------------------------------------
# 에러 코드 정의
# 새 에러는 이 Enum에만 추가하면 됩니다.
# ------------------------------------------------------------------

class ErrorCode(Enum):
  # 분석 기간
  DAYS_NOT_NUMBER = "E001"
  DAYS_BELOW_MIN  = "E002"
  DAYS_ABOVE_MAX  = "E003"
  # 부품 선택
  PARTS_ALL_KEEP  = "E004"


# ------------------------------------------------------------------
# 검증 결과 컨테이너
# ------------------------------------------------------------------

@dataclass
class ValidationResult:
  valid:      bool
  message:    str            = ""
  error_code: ErrorCode | None = None
  corrected:  int | None     = None


# ------------------------------------------------------------------
# 검증 함수
# ------------------------------------------------------------------

def validate_analysis_days(raw_value) -> ValidationResult:
  try:
    days = int(raw_value)
  except (ValueError, TypeError):
    return ValidationResult(
      valid=False,
      message=(
        "분석 기간은 숫자로 입력해야 합니다.\n"
        f"기본값({ANALYSIS_DAYS_DEFAULT}일)으로 재설정합니다."
      ),
      error_code=ErrorCode.DAYS_NOT_NUMBER,
      corrected=ANALYSIS_DAYS_DEFAULT,
    )

  if days < ANALYSIS_DAYS_MIN:
    return ValidationResult(
      valid=False,
      message=(
        f"분석 기간은 최소 {ANALYSIS_DAYS_MIN}일 이상이어야 합니다.\n"
        f"{ANALYSIS_DAYS_MIN}일로 재설정합니다."
      ),
      error_code=ErrorCode.DAYS_BELOW_MIN,
      corrected=ANALYSIS_DAYS_MIN,
    )

  if days > ANALYSIS_DAYS_MAX:
    return ValidationResult(
      valid=False,
      message=(
        f"분석 기간은 최대 {ANALYSIS_DAYS_MAX}일까지 가능합니다.\n"
        f"{ANALYSIS_DAYS_MAX}일로 재설정합니다."
      ),
      error_code=ErrorCode.DAYS_ABOVE_MAX,
      corrected=ANALYSIS_DAYS_MAX,
    )

  return ValidationResult(valid=True)


def validate_parts_not_all_keep(parts_state: dict) -> ValidationResult:
  all_keep = all(parts_state[part]["option"] == "keep" for part in PARTS)
  if all_keep:
    return ValidationResult(
      valid=False,
      message="분석 항목이 없습니다.\n추천받을 부품을 하나 이상 선택해 주세요.",
      error_code=ErrorCode.PARTS_ALL_KEEP,
    )
  return ValidationResult(valid=True)
