from unittest.mock import patch

from src.recommendation.user_input_dialog import find_impactful_unknown_processes


def _logs_with(name: str, cpu: float, mem: float, count: int, total: int):
    logs = [{"processes": [{"name": name, "cpu_percent": cpu, "memory_mb": mem}]} for _ in range(count)]
    logs += [{"processes": []} for _ in range(total - count)]
    return logs


class TestFindImpactfulUnknownProcesses:
    @patch("src.recommendation.user_input_dialog._load_known_process_names", return_value=set())
    def test_system_idle_process_excluded(self, _mock_known):
        """System Idle Process는 CPU 100%/메모리 무관하게 항상 제외되어야 한다 —
        사용자에게 '용도'를 물어볼 대상이 아닌 OS 커널 프로세스이기 때문."""
        logs = _logs_with("system idle process", cpu=100.0, mem=0.0, count=20, total=20)
        assert find_impactful_unknown_processes(logs) == []

    @patch("src.recommendation.user_input_dialog._load_known_process_names", return_value=set())
    def test_dwm_and_msmpeng_excluded(self, _mock_known):
        logs = []
        for _ in range(20):
            logs.append({"processes": [
                {"name": "dwm.exe", "cpu_percent": 70.0, "memory_mb": 80.0},
                {"name": "msmpeng.exe", "cpu_percent": 60.0, "memory_mb": 300.0},
            ]})
        assert find_impactful_unknown_processes(logs) == []

    @patch("src.recommendation.user_input_dialog._load_known_process_names", return_value=set())
    def test_real_user_app_still_detected(self, _mock_known):
        """OS 프로세스가 아닌 실제 사용자 앱은 그대로 미분류로 잡혀야 한다."""
        logs = _logs_with("claude.exe", cpu=25.0, mem=178.0, count=20, total=20)
        results = find_impactful_unknown_processes(logs)
        assert len(results) == 1
        assert results[0]["name"] == "claude.exe"
