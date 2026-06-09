import json
import re
from pathlib import Path


CPU_MAX_SCORE = 80000
GPU_MAX_SCORE = 41588
MAX_TIER = 29

try:
    from src.config import SPECS_DIR as _SPECS_DIR
    CPU_STATIC_PATH = _SPECS_DIR / "cpu_passmark_static.json"
    GPU_STATIC_PATH = _SPECS_DIR / "gpu_passmark_static.json"
except Exception:
    CPU_STATIC_PATH = Path("data/specs/cpu_passmark_static.json")
    GPU_STATIC_PATH = Path("data/specs/gpu_passmark_static.json")


def normalize_text(text):
    if text is None:
        return ""
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9가-힣]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_price_usd(price):
    if price in (None, "", "NA"):
        return "NA"
    price_text = str(price).replace("$", "").replace(",", "").strip()
    try:
        return float(price_text)
    except ValueError:
        return "NA"


def _load_static_items(path: Path) -> list[dict] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list) and data:
            return data
    except Exception:
        pass
    return None


def load_cpu_passmark_items() -> list[dict]:
    """정적 CPU PassMark DB(cpu_passmark_static.json)를 반환한다."""
    return _load_static_items(CPU_STATIC_PATH) or []


def load_gpu_passmark_items() -> list[dict]:
    """정적 GPU PassMark DB(gpu_passmark_static.json)를 반환한다."""
    return _load_static_items(GPU_STATIC_PATH) or []


def calculate_performance_tier(score, max_score, max_tier=MAX_TIER):
    if score in (None, "", "NA"):
        return None
    try:
        score = float(str(score).replace(",", ""))
    except ValueError:
        return None
    if max_score <= 0:
        return None
    tier = int((score / max_score) * max_tier)
    if tier < 1:
        return 1
    if tier > max_tier:
        return max_tier
    return tier


def calculate_cpu_tier(score):
    return calculate_performance_tier(score, CPU_MAX_SCORE)


def calculate_gpu_tier(score):
    return calculate_performance_tier(score, GPU_MAX_SCORE)
