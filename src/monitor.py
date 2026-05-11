from datetime import datetime, timezone

import psutil

from src.gpu import collect_gpu_snapshot
from src.process_tracker import get_running_processes, get_system_boot_time, get_system_uptime_seconds
from src.background import start_background_task, stop_background_task, is_background_running, get_stop_event
from src.storage import append_usage_log

MONITOR_INTERVAL_SECONDS = 60


def get_cpu_usage() -> float:
  return psutil.cpu_percent(interval=1)


def get_ram_usage() -> float:
  return psutil.virtual_memory().percent


def collect_monitoring_snapshot() -> dict:
  try:
    gpu = collect_gpu_snapshot()
  except Exception:
    gpu = {"gpu_name": None, "gpu_percent": None, "vram_used_mb": None, "vram_total_mb": None}

  try:
    processes = get_running_processes()
  except Exception:
    processes = []

  try:
    boot_time = get_system_boot_time()
    uptime_seconds = get_system_uptime_seconds()
  except Exception:
    boot_time = None
    uptime_seconds = None

  return {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "cpu_percent": get_cpu_usage(),
    "ram_percent": get_ram_usage(),
    "gpu_name": gpu.get("gpu_name"),
    "gpu_percent": gpu.get("gpu_percent"),
    "vram_used_mb": gpu.get("vram_used_mb"),
    "vram_total_mb": gpu.get("vram_total_mb"),
    "boot_time": boot_time,
    "uptime_seconds": uptime_seconds,
    "processes": processes,
  }


def _monitoring_loop(interval_seconds: int) -> None:
  stop_event = get_stop_event()
  while not stop_event.is_set():
    try:
      snapshot = collect_monitoring_snapshot()
      append_usage_log(snapshot)
    except Exception:
      pass
    stop_event.wait(timeout=interval_seconds)


def start_monitoring_loop(interval_seconds: int = MONITOR_INTERVAL_SECONDS) -> bool:
  return start_background_task(_monitoring_loop, interval_seconds)


def stop_monitoring_loop() -> None:
  stop_background_task()


def is_monitoring_running() -> bool:
  return is_background_running()
