"""
BuildSense 보고서 데모 — 더미 데이터 기반 예시 HTML 생성

[사용된 더미 데이터]
- 사용자 프로필 : 분석 기간 7일, 중급 사용자, 전 부품 추천 모드
- 모니터링 기간 : 2026-05-21 ~ 2026-05-27 (7일), 총 420 스냅샷 (60초 간격)
- 사용 시간대  : 주로 18~24시 (저녁 게임 세션), 주말 낮 추가
- CPU 사용률   : 평소 45~65%, 게임 중 75~92% (고부하 에피소드 4회)
- RAM 사용률   : 평소 55~70%, 피크 88%
- GPU 사용률   : 게임 세션 80~97%, 비게임 10~30%
- VRAM        : 총 8 GB, 게임 중 6.2~7.6 GB 사용
- 디스크 C:   : SSD NVMe 500 GB, 평균 사용률 72% (위험 구간 5%)
- 디스크 D:   : HDD 2 TB, 평균 사용률 48%
- 주요 프로세스: GTA5.exe(게임), steam.exe, discord.exe, Code.exe(개발), chrome.exe
"""

import json
import random
import sys
import webbrowser
from datetime import datetime, timedelta, timezone
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from src.report.report_data_collector import collect_report_data
from src.report.report_generator import _build_charts
from src.report.html_builder import build_html

random.seed(42)

# ── 더미 프로필 ──────────────────────────────────────────────────────────────

PROFILE = {
    "analysis_days": 7,
    "knowledge_level": "intermediate",
    "parts": {
        "cpu":  "recommend",
        "gpu":  "recommend",
        "ram":  "recommend",
        "ssd":  "recommend",
        "hdd":  "recommend",
        "psu":  "recommend",
    },
}

# ── 더미 프로세스 풀 ─────────────────────────────────────────────────────────

_GAME_PROCS = [
    {"name": "GTA5.exe",      "cpu_percent": 35.0, "memory_mb": 4200},
    {"name": "steam.exe",     "cpu_percent":  4.5, "memory_mb":  320},
    {"name": "SteamWebHelper","cpu_percent":  1.2, "memory_mb":  210},
    {"name": "discord.exe",   "cpu_percent":  2.1, "memory_mb":  280},
    {"name": "NVIDIA Share",  "cpu_percent":  1.8, "memory_mb":  180},
]

_DEV_PROCS = [
    {"name": "Code.exe",      "cpu_percent": 12.0, "memory_mb":  820},
    {"name": "node.exe",      "cpu_percent": 18.0, "memory_mb":  540},
    {"name": "python.exe",    "cpu_percent":  8.5, "memory_mb":  310},
    {"name": "chrome.exe",    "cpu_percent":  6.2, "memory_mb": 1100},
    {"name": "discord.exe",   "cpu_percent":  2.1, "memory_mb":  280},
]

_IDLE_PROCS = [
    {"name": "chrome.exe",    "cpu_percent":  3.2, "memory_mb":  540},
    {"name": "discord.exe",   "cpu_percent":  1.4, "memory_mb":  260},
    {"name": "explorer.exe",  "cpu_percent":  0.8, "memory_mb":  120},
    {"name": "antimalware",   "cpu_percent":  0.5, "memory_mb":   90},
]


def _jitter(base, lo, hi):
    return max(0.0, min(100.0, base + random.uniform(lo, hi)))


def _make_snapshot(ts: datetime, mode: str) -> dict:
    is_game = mode == "game"
    is_dev  = mode == "dev"

    cpu   = _jitter(82 if is_game else (55 if is_dev else 30), -12, 12)
    ram   = _jitter(78 if is_game else (65 if is_dev else 52), -8,  8)
    gpu   = _jitter(88 if is_game else 18, -10, 10) if is_game else _jitter(18, -10, 10)
    vram_total = 8192
    vram_used  = int(_jitter(87 if is_game else 28, -8, 8) / 100 * vram_total)

    procs = _GAME_PROCS if is_game else (_DEV_PROCS if is_dev else _IDLE_PROCS)

    return {
        "timestamp": ts.isoformat(),
        "cpu_percent": round(cpu, 1),
        "ram_percent": round(ram, 1),
        "gpu_name": "NVIDIA GeForce RTX 4070",
        "gpu_percent": round(gpu, 1),
        "vram_used_mb": vram_used,
        "vram_total_mb": vram_total,
        "boot_time": (ts - timedelta(hours=random.uniform(4, 18))).isoformat(),
        "uptime_seconds": random.uniform(14400, 64800),
        "disks": [
            {
                "mountpoint": "C:\\",
                "device": "PhysicalDrive0",
                "fstype": "NTFS",
                "total_gb": 500.0,
                "used_gb": round(random.uniform(345, 375), 1),
                "free_gb": round(random.uniform(125, 155), 1),
                "percent": round(random.uniform(69, 75), 1),
            },
            {
                "mountpoint": "D:\\",
                "device": "PhysicalDrive1",
                "fstype": "NTFS",
                "total_gb": 2000.0,
                "used_gb": round(random.uniform(920, 1000), 1),
                "free_gb": round(random.uniform(1000, 1080), 1),
                "percent": round(random.uniform(46, 50), 1),
            },
        ],
        "processes": [
            {**p, "cpu_percent": round(p["cpu_percent"] + random.uniform(-2, 2), 1)}
            for p in procs
        ],
    }


def _generate_logs() -> list[dict]:
    logs = []
    base = datetime(2026, 5, 21, 0, 0, 0, tzinfo=timezone.utc)

    sessions = [
        # (day_offset, start_hour, duration_hours, mode)
        (0, 19, 2.5, "game"),
        (1, 20, 3.0, "game"),
        (2, 14, 1.5, "dev"),
        (2, 20, 2.0, "game"),
        (3, 10, 2.0, "dev"),
        (3, 21, 1.5, "game"),
        (4, 19, 3.5, "game"),
        (5, 11, 2.0, "dev"),
        (5, 16, 1.0, "idle"),
        (5, 20, 2.5, "game"),
        (6, 13, 1.5, "dev"),
        (6, 19, 2.0, "game"),
    ]

    for day, start_h, duration, mode in sessions:
        session_start = base + timedelta(days=day, hours=start_h)
        n = int(duration * 3600 / 60)
        for i in range(n):
            ts = session_start + timedelta(minutes=i)
            logs.append(_make_snapshot(ts, mode))

    return logs


# ── 보고서 생성 ──────────────────────────────────────────────────────────────

def main():
    print("더미 데이터 생성 중...")
    logs = _generate_logs()
    print(f"  스냅샷 수: {len(logs)}개")

    print("데이터 분석 중...")
    data = collect_report_data(logs, PROFILE)

    print("차트 생성 중 (12개)...")
    charts = _build_charts(data)

    print("HTML 조립 중...")
    html = build_html(data, charts)

    out = Path(__file__).parent / "reports"
    out.mkdir(exist_ok=True)
    path = out / f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    path.write_text(html, encoding="utf-8")

    print(f"\n보고서 저장: {path}")
    webbrowser.open(path.as_uri())


if __name__ == "__main__":
    main()
