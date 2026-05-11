import subprocess

_NVIDIA_SMI_QUERY = [
  "nvidia-smi",
  "--query-gpu=utilization.gpu,memory.used,memory.total,name",
  "--format=csv,noheader,nounits",
]
_CREATE_NO_WINDOW = 0x08000000


def is_nvidia_gpu_available() -> bool:
  try:
    result = subprocess.run(
      ["nvidia-smi"],
      capture_output=True,
      timeout=5,
      creationflags=_CREATE_NO_WINDOW,
    )
    return result.returncode == 0
  except Exception:
    return False


def _query_nvidia_smi() -> list[str] | None:
  try:
    result = subprocess.run(
      _NVIDIA_SMI_QUERY,
      capture_output=True,
      text=True,
      timeout=8,
      creationflags=_CREATE_NO_WINDOW,
    )
    if result.returncode != 0:
      return None
    line = result.stdout.strip().splitlines()[0]
    return [v.strip() for v in line.split(",")]
  except Exception:
    return None


def get_gpu_usage() -> float | None:
  parts = _query_nvidia_smi()
  if parts is None or len(parts) < 1:
    return None
  try:
    return float(parts[0])
  except ValueError:
    return None


def get_vram_usage() -> tuple[float | None, float | None]:
  """(vram_used_mb, vram_total_mb) 반환. 실패 시 (None, None)."""
  parts = _query_nvidia_smi()
  if parts is None or len(parts) < 3:
    return None, None
  try:
    return float(parts[1]), float(parts[2])
  except ValueError:
    return None, None


def get_gpu_name() -> str | None:
  parts = _query_nvidia_smi()
  if parts is None or len(parts) < 4:
    return None
  name = parts[3].strip()
  return name if name else None


def collect_gpu_snapshot() -> dict:
  vram_used, vram_total = get_vram_usage()
  return {
    "gpu_name": get_gpu_name(),
    "gpu_percent": get_gpu_usage(),
    "vram_used_mb": vram_used,
    "vram_total_mb": vram_total,
  }
