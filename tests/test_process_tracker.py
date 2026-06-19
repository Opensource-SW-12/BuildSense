from unittest.mock import patch, MagicMock

from src.process_tracker import get_running_processes


def _fake_proc(pid, name, cpu_percent, memory_mb, exe=""):
    proc = MagicMock()
    proc.info = {
        "pid": pid,
        "name": name,
        "cpu_percent": cpu_percent,
        "memory_info": MagicMock(rss=memory_mb * 1024 * 1024),
    }
    proc.exe.return_value = exe
    return proc


class TestGetRunningProcesses:
    @patch("src.process_tracker._CPU_COUNT", 8)
    @patch("src.process_tracker.psutil.process_iter")
    def test_multicore_cpu_percent_normalized_to_100_scale(self, mock_iter):
        """psutil 프로세스 cpu_percent는 코어 1개 기준이라 8코어를 전부 쓰는
        프로세스는 raw 800%로 나온다 — 전체 시스템 용량 기준 100%로 정규화돼야 한다."""
        mock_iter.return_value = [_fake_proc(1, "hog.exe", cpu_percent=800.0, memory_mb=100.0)]
        result = get_running_processes()
        assert result[0]["cpu_percent"] == 100.0

    @patch("src.process_tracker._CPU_COUNT", 8)
    @patch("src.process_tracker.psutil.process_iter")
    def test_single_core_cpu_percent_normalized_proportionally(self, mock_iter):
        mock_iter.return_value = [_fake_proc(1, "light.exe", cpu_percent=80.0, memory_mb=50.0)]
        result = get_running_processes()
        assert result[0]["cpu_percent"] == 10.0
