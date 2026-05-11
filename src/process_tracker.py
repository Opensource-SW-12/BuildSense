import time
from datetime import datetime, timezone

import psutil


def get_running_processes() -> list[dict]:
  processes = []
  for proc in psutil.process_iter(["pid", "name"]):
    try:
      info = proc.info
      processes.append({
        "pid": info["pid"],
        "name": info["name"] or "",
      })
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
      continue
  return processes


def get_system_boot_time() -> str:
  return datetime.fromtimestamp(psutil.boot_time(), tz=timezone.utc).isoformat()


def get_system_uptime_seconds() -> float:
  return round(time.time() - psutil.boot_time(), 1)


def collect_process_uptime_snapshot() -> dict:
  return {
    "boot_time": get_system_boot_time(),
    "uptime_seconds": get_system_uptime_seconds(),
    "processes": get_running_processes(),
  }
