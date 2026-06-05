import subprocess
import psutil

from src.platform_mapper import infer_socket_from_cpu_name


def get_hardware_info() -> dict:
  ssd, hdd = _get_disks_by_type()
  cpu_name  = _get_cpu()
  return {
    "CPU":        cpu_name,
    "CPU_socket": infer_socket_from_cpu_name(cpu_name),
    "GPU":        _get_gpu(),
    "RAM":        _get_ram(),
    "SSD":        ssd,
    "HDD":        hdd,
    "파워":       "확인할 수 없음",
  }


def _run_ps(command: str) -> str:
  try:
    result = subprocess.run(
      ["powershell", "-Command", command],
      capture_output=True,
      text=True,
      timeout=8,
      creationflags=subprocess.CREATE_NO_WINDOW,
    )
    return result.stdout.strip()
  except Exception:
    return ""


def _get_cpu() -> str:
  out = _run_ps("(Get-WmiObject Win32_Processor).Name")
  return out or "확인할 수 없음"


def _get_gpu() -> str:
  try:
    result = subprocess.run(
      ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
      capture_output=True,
      text=True,
      timeout=6,
      creationflags=subprocess.CREATE_NO_WINDOW,
    )
    out = result.stdout.strip()
    return out or "확인할 수 없음"
  except Exception:
    return "확인할 수 없음"


def _get_ram() -> str:
  try:
    gb = psutil.virtual_memory().total / (1024 ** 3)
    return f"{gb:.0f} GB"
  except Exception:
    return "확인할 수 없음"


def _get_disks_by_type() -> tuple[str, str]:
  """(ssd_result, hdd_result) — PowerShell 1회 실행으로 SSD/HDD 동시 탐지."""
  cmd = (
    "Get-PhysicalDisk | "
    "Select-Object FriendlyName,MediaType | "
    "ConvertTo-Csv -NoTypeInformation"
  )
  out = _run_ps(cmd)
  if not out:
    return "확인할 수 없음", "확인할 수 없음"

  ssd_matches: list[str] = []
  hdd_matches: list[str] = []
  for line in out.splitlines()[1:]:  # 헤더 제외
    cols = [c.strip('"') for c in line.split('","')]
    if len(cols) == 2:
      name = cols[0].strip()
      media_type = cols[1].strip()
      if name:
        if media_type == "SSD":
          ssd_matches.append(name)
        elif media_type == "HDD":
          hdd_matches.append(name)

  return (
    ", ".join(ssd_matches) if ssd_matches else "없음",
    ", ".join(hdd_matches) if hdd_matches else "없음",
  )
