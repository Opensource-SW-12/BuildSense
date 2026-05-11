import subprocess
import psutil


def get_hardware_info() -> dict:
  return {
    "CPU":  _get_cpu(),
    "GPU":  _get_gpu(),
    "RAM":  _get_ram(),
    "SSD":  _get_disk_by_type("SSD"),
    "HDD":  _get_disk_by_type("HDD"),
    "파워": "확인할 수 없음",
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


def _get_disk_by_type(media_type: str) -> str:
  cmd = (
    "Get-PhysicalDisk | "
    "Select-Object FriendlyName,MediaType | "
    "ConvertTo-Csv -NoTypeInformation"
  )
  out = _run_ps(cmd)
  if not out:
    return "확인할 수 없음"

  matches = []
  for line in out.splitlines()[1:]:  # 헤더 제외
    cols = [c.strip('"') for c in line.split('","')]
    if len(cols) == 2 and cols[1].strip() == media_type:
      name = cols[0].strip()
      if name:
        matches.append(name)

  return ", ".join(matches) if matches else "없음"
