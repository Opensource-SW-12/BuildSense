import subprocess

_NVIDIA_SMI_QUERY = [
  "nvidia-smi",
  "--query-gpu=utilization.gpu,memory.used,memory.total,name",
  "--format=csv,noheader,nounits",
]
_CREATE_NO_WINDOW = 0x08000000


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


def collect_gpu_snapshot() -> dict:
  parts = _query_nvidia_smi()
  if parts is None or len(parts) < 4:
    return {"gpu_name": None, "gpu_percent": None, "vram_used_mb": None, "vram_total_mb": None}

  try:
    gpu_percent = float(parts[0])
  except ValueError:
    gpu_percent = None

  try:
    vram_used  = float(parts[1])
    vram_total = float(parts[2])
  except ValueError:
    vram_used, vram_total = None, None

  gpu_name = parts[3].strip() or None

  return {
    "gpu_name":     gpu_name,
    "gpu_percent":  gpu_percent,
    "vram_used_mb": vram_used,
    "vram_total_mb": vram_total,
  }
