import time
from datetime import datetime, timezone

import psutil

_TOP_PROCESS_COUNT = 15


def get_running_processes() -> list[dict]:
  processes = []
  for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
    try:
      info = proc.info
      memory_mb = round(info["memory_info"].rss / (1024 * 1024), 2) if info["memory_info"] else 0.0
      cpu = info["cpu_percent"] or 0.0
      try:
        exe = proc.exe()
      except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
        exe = ""
      processes.append({
        "pid": info["pid"],
        "name": info["name"] or "",
        "cpu_percent": round(cpu, 2),
        "memory_mb": memory_mb,
        "exe": exe,
      })
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
      continue

  processes.sort(key=lambda p: (p["cpu_percent"], p["memory_mb"]), reverse=True)
  return processes[:_TOP_PROCESS_COUNT]


def get_system_boot_time() -> str:
  return datetime.fromtimestamp(psutil.boot_time(), tz=timezone.utc).isoformat()


def get_system_uptime_seconds() -> float:
  return round(time.time() - psutil.boot_time(), 1)


def get_boot_and_uptime() -> tuple[str, float]:
  """boot_time과 uptime_seconds를 psutil.boot_time() 1회 호출로 반환."""
  boot_ts = psutil.boot_time()
  boot_time = datetime.fromtimestamp(boot_ts, tz=timezone.utc).isoformat()
  uptime_seconds = round(time.time() - boot_ts, 1)
  return boot_time, uptime_seconds


def collect_process_uptime_snapshot() -> dict:
  return {
    "boot_time": get_system_boot_time(),
    "uptime_seconds": get_system_uptime_seconds(),
    "processes": get_running_processes(),
  }
