"""
BuildSense 시뮬레이션 — 더미 모니터링 데이터로 "분석 기간 종료 → 추가 정보 입력
(사용자 답변) → 분석 → 보고서" 흐름을 실제 UI로 끝까지 테스트한다.

demo_report.py와 달리 차트/HTML만 만드는 게 아니라, 실제 BuildSenseApp을
StartupState.ANALYZE로 띄워 "추가 정보 입력" 다이얼로그(예산·RGB 선호·미분류
프로세스 분류)에 직접 답변해보고, 그 답변이 반영된 추천·보고서까지 확인할 수 있다.

원본 데이터 보호 정책:
  - 최초 실행 시: 원본 파일을 .orig에 복사 (이후 실행에서도 덮어쓰지 않음)
  - 매 실행 전: .orig이 있으면 원본이 보존된 것이므로 더미 데이터만 새로 씀
  - 앱 종료 후: 더미 파일을 삭제하고 .orig에서 원본 복원

사용법:
    simulate_user_answers.bat   (권장)
    python simulate_user_answers.py
"""

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from src.app import BuildSenseApp
from src.startup_state import StartupState
from src.storage import ensure_app_directories
from src.config import USER_PROFILE_PATH, USER_PREFERENCES_PATH, USAGE_LOG_PATH

import demo_report


def _orig_path(path: Path) -> Path:
    return path.with_suffix(path.suffix + ".orig")


def _save_orig(path: Path) -> None:
    """원본 파일을 .orig에 보존한다. .orig이 이미 있으면 건드리지 않는다."""
    orig = _orig_path(path)
    if orig.exists():
        return
    if path.exists():
        shutil.copy2(path, orig)
        print(f"  원본 보존: {path.name} → {orig.name}")


def _restore_orig(path: Path) -> None:
    """앱 종료 후 .orig → 원본으로 복원한다."""
    orig = _orig_path(path)
    if orig.exists():
        path.unlink(missing_ok=True)
        shutil.move(str(orig), str(path))
        print(f"  원본 복원: {orig.name} → {path.name}")
    else:
        path.unlink(missing_ok=True)
        print(f"  더미 파일 삭제: {path.name}")


def _write_dummy_profile() -> None:
    profile = {
        "consent": {"agreed": True},
        "knowledge_level": "intermediate",
        "analysis_days": 7,
        "parts": {part: {"option": "recommend"}
                  for part in ["CPU", "GPU", "RAM", "SSD", "HDD", "메인보드", "파워"]},
    }
    USER_PROFILE_PATH.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  더미 프로필 저장: {USER_PROFILE_PATH.name}")


def _write_dummy_logs() -> None:
    logs = demo_report._generate_logs()
    with open(USAGE_LOG_PATH, "w", encoding="utf-8") as f:
        for log in logs:
            f.write(json.dumps(log, ensure_ascii=False) + "\n")
    print(f"  더미 모니터링 로그 저장: {USAGE_LOG_PATH.name} ({len(logs)}개 스냅샷)")


def main():
    print("더미 데이터 준비 중...")
    ensure_app_directories()

    for path in (USER_PROFILE_PATH, USER_PREFERENCES_PATH, USAGE_LOG_PATH):
        _save_orig(path)

    _write_dummy_profile()
    _write_dummy_logs()

    print("\nBuildSense를 ANALYZE 상태로 실행합니다.")
    print("'모니터링 기간이 종료되었습니다' 화면 → '추가 정보 입력' 버튼을 눌러")
    print("예산 / RGB 선호 / 색상 선호 / 미분류 프로세스(GTA5.exe) 분류에 직접 답변해보세요.\n")

    try:
        app = BuildSenseApp(startup_state=StartupState.ANALYZE)
        app.run()
    finally:
        print("\n시뮬레이션 종료 - 원본 데이터 복원 중...")
        for path in (USER_PROFILE_PATH, USER_PREFERENCES_PATH, USAGE_LOG_PATH):
            _restore_orig(path)
        print("완료.")


if __name__ == "__main__":
    main()
