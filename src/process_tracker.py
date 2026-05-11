import psutil


def get_running_processes() -> list[dict]:
  processes = []
  for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
    try:
      info = proc.info
      processes.append({
        "pid": info["pid"],
        "name": info["name"] or "",
        "cpu_percent": round(info["cpu_percent"] or 0.0, 2),
        "memory_percent": round(info["memory_percent"] or 0.0, 2),
      })
    except (psutil.NoSuchProcess, psutil.AccessDenied):
      continue
  return processes
