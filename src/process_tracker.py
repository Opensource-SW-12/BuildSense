import time
from datetime import datetime, timezone

import psutil

_TOP_PROCESS_COUNT = 15
_CPU_COUNT = psutil.cpu_count() or 1


def get_running_processes() -> list[dict]:
  processes = []
  for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
    try:
      info = proc.info
      memory_mb = round(info["memory_info"].rss / (1024 * 1024), 2) if info["memory_info"] else 0.0
      # psutil의 프로세스 cpu_percent는 코어 1개 기준이라 멀티코어 프로세스는
      # 코어 수만큼 100%를 넘길 수 있다 (예: 8코어에서 800%) — 전체 시스템 용량
      # 기준 0~100% 스케일로 정규화해 다른 cpu_percent 값들과 일관되게 맞춘다.
      cpu = (info["cpu_percent"] or 0.0) / _CPU_COUNT
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
