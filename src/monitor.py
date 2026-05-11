import threading
from datetime import datetime, timezone

import psutil

from src.process_tracker import get_running_processes, get_system_uptime_seconds

MONITOR_INTERVAL_SECONDS = 60


def get_cpu_usage() -> float:
  return psutil.cpu_percent(interval=1)


def get_ram_usage() -> float:
  return psutil.virtual_memory().percent


def collect_monitoring_snapshot() -> dict:
  return {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "cpu_percent": get_cpu_usage(),
    "ram_percent": get_ram_usage(),
    "uptime_seconds": get_system_uptime_seconds(),
    "processes": get_running_processes(),
  }


class UsageMonitor:
  def __init__(self) -> None:
    self._snapshots: list[dict] = []
    self._thread: threading.Thread | None = None
    self._stop_event = threading.Event()

  def start(self) -> None:
    if self._thread and self._thread.is_alive():
      return
    self._stop_event.clear()
    self._thread = threading.Thread(target=self._run, daemon=True)
    self._thread.start()

  def stop(self) -> None:
    self._stop_event.set()

  def get_snapshots(self) -> list[dict]:
    return list(self._snapshots)

  def _run(self) -> None:
    while not self._stop_event.is_set():
      try:
        snapshot = collect_monitoring_snapshot()
        self._snapshots.append(snapshot)
      except Exception:
        pass
      self._stop_event.wait(timeout=MONITOR_INTERVAL_SECONDS)
