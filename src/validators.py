from src.settings import ANALYSIS_DAYS_MIN, ANALYSIS_DAYS_MAX, ANALYSIS_DAYS_DEFAULT, PARTS


def validate_analysis_days(raw_value) -> tuple[bool, str, int]:
  """
  분석 기간 입력값을 검증합니다.
  반환: (유효 여부, 오류 메시지, 보정된 값)
  """
  try:
    days = int(raw_value)
  except (ValueError, TypeError):
    return (
      False,
      (
        "분석 기간은 숫자로 입력해야 합니다.\n"
        f"기본값({ANALYSIS_DAYS_DEFAULT}일)으로 재설정합니다."
      ),
      ANALYSIS_DAYS_DEFAULT,
    )

  if days < ANALYSIS_DAYS_MIN:
    return (
      False,
      (
        f"분석 기간은 최소 {ANALYSIS_DAYS_MIN}일 이상이어야 합니다.\n"
        f"{ANALYSIS_DAYS_MIN}일로 재설정합니다."
      ),
      ANALYSIS_DAYS_MIN,
    )

  if days > ANALYSIS_DAYS_MAX:
    return (
      False,
      (
        f"분석 기간은 최대 {ANALYSIS_DAYS_MAX}일까지 가능합니다.\n"
        f"{ANALYSIS_DAYS_MAX}일로 재설정합니다."
      ),
      ANALYSIS_DAYS_MAX,
    )

  return True, "", days


def validate_parts_not_all_keep(parts_state: dict) -> tuple[bool, str]:
  """
  모든 부품이 '유지' 상태인지 검증합니다.
  반환: (유효 여부, 오류 메시지)
  """
  all_keep = all(parts_state[part]["option"] == "keep" for part in PARTS)
  if all_keep:
    return (
      False,
      "분석 항목이 없습니다.\n추천받을 부품을 하나 이상 선택해 주세요.",
    )
  return True, ""
