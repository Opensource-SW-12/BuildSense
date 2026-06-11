"""
BuildSense 보고서 데모 — 더미 모니터링 데이터 + 실제 하드웨어 기반 추천

[더미 데이터 스펙]
- 모니터링 기간 : 2026-05-21 ~ 2026-05-27 (7일)
- 총 스냅샷     : 약 1,500개 (1분 간격)
- CPU 사용률    : 게임 중 82% 전후, 개발 55%, 유휴 30%
- RAM 사용률    : 게임 78%, 개발 65%, 유휴 52%
- GPU 사용률    : 게임 세션 88% 전후, 비게임(개발·유휴) 18%
- VRAM         : 총 8GB, 게임 중 87% 사용
- 디스크 C:    : NVMe 500GB, 평균 사용률 72%
- 디스크 D:    : HDD 2TB, 평균 사용률 48%
- 주요 프로세스 : GTA5.exe, steam.exe, Code.exe, node.exe, chrome.exe
- 활성 세션     : 낮 개발(10~15시) + 저녁 게임(18~24시) 혼합, 매일 새벽에는
                  PC 전원이 꺼져있는 것으로 처리해 절전모드 인식(KAN-167) 구간을 재현

이 모듈의 _generate_logs()는 simulate_user_answers.py에서도 사용한다 — 실제
BuildSenseApp을 ANALYZE 상태로 띄워 새 UI(추가 정보 입력 다이얼로그, 메인보드
옵션 등)와 실제 하드웨어 기반 추천·보고서 생성까지 보여주려면
simulate_user_answers.bat을 실행할 것.
"""

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

KST = timezone(timedelta(hours=9))

# ── 더미 프로필 / 사용자 입력 ─────────────────────────────────────────────────

PROFILE = {
    "consent": {"agreed": True},
    "knowledge_level": "intermediate",
    "analysis_days": 7,
    "parts": {
        part: {"option": "recommend"}
        for part in ["CPU", "GPU", "RAM", "SSD", "HDD", "메인보드", "파워"]
    },
}

USER_PREFERENCES = {
    "budget_mode": "recommended",
    "budgets": {},
    "rgb_preference": "none",
    "color_preference": "none",
    "unknown_process_categories": {},
}

# ── 더미 프로세스 풀 ─────────────────────────────────────────────────────────

_GAME_PROCS = [
    {"name": "GTA5.exe",   "cpu_percent": 35.0, "memory_mb": 4200},
    {"name": "steam.exe",  "cpu_percent":  4.0, "memory_mb":  320},
    {"name": "discord.exe","cpu_percent":  2.0, "memory_mb":  280},
]

_DEV_PROCS = [
    {"name": "Code.exe",   "cpu_percent": 12.0, "memory_mb":  820},
    {"name": "node.exe",   "cpu_percent": 18.0, "memory_mb":  540},
    {"name": "chrome.exe", "cpu_percent":  6.0, "memory_mb": 1100},
    {"name": "steam.exe",  "cpu_percent":  1.0, "memory_mb":  300},
]

_IDLE_PROCS = [
    {"name": "chrome.exe",   "cpu_percent": 3.0, "memory_mb": 540},
    {"name": "steam.exe",    "cpu_percent": 1.0, "memory_mb": 290},
    {"name": "discord.exe",  "cpu_percent": 1.4, "memory_mb": 260},
    {"name": "explorer.exe", "cpu_percent": 0.8, "memory_mb": 120},
]


def _jitter(base, lo, hi):
    return max(0.0, min(100.0, base + random.uniform(lo, hi)))


def _make_snapshot(ts: datetime, mode: str, gpu_name: str, boot_time: datetime) -> dict:
    is_game = mode == "game"
    is_dev  = mode == "dev"

    cpu = _jitter(82 if is_game else (55 if is_dev else 30), -12, 12)
    ram = _jitter(78 if is_game else (65 if is_dev else 52), -8, 8)
    gpu = _jitter(88 if is_game else 18, -10, 10)
    vram_total = 8192
    vram_used  = int(_jitter(87 if is_game else 28, -8, 8) / 100 * vram_total)

    c_percent = round(random.uniform(70.0, 74.0), 1)
    c_used    = round(500.0 * c_percent / 100, 1)
    c_free    = round(500.0 - c_used, 1)

    d_percent = round(random.uniform(46.0, 50.0), 1)
    d_used    = round(2000.0 * d_percent / 100, 1)
    d_free    = round(2000.0 - d_used, 1)

    procs = _GAME_PROCS if is_game else (_DEV_PROCS if is_dev else _IDLE_PROCS)

    return {
        "timestamp": ts.isoformat(),
        "cpu_percent": round(cpu, 1),
        "ram_percent": round(ram, 1),
        "gpu_name": gpu_name,
        "gpu_percent": round(gpu, 1),
        "vram_used_mb": vram_used,
        "vram_total_mb": vram_total,
        "boot_time": boot_time.isoformat(),
        "uptime_seconds": round((ts - boot_time).total_seconds(), 1),
        "disks": [
            {
                "mountpoint": "C:\\",
                "device": "PhysicalDrive0",
                "fstype": "NTFS",
                "total_gb": 500.0,
                "used_gb": c_used,
                "free_gb": c_free,
                "percent": c_percent,
            },
            {
                "mountpoint": "D:\\",
                "device": "PhysicalDrive1",
                "fstype": "NTFS",
                "total_gb": 2000.0,
                "used_gb": d_used,
                "free_gb": d_free,
                "percent": d_percent,
            },
        ],
        "processes": [
            {**p, "cpu_percent": round(max(0.0, p["cpu_percent"] + random.uniform(-2, 2)), 1)}
            for p in procs
        ],
    }


def _generate_logs(gpu_name: str | None = None) -> list[dict]:
    """7일(2026-05-21~05-27)간 '낮 개발(10~15시) + 저녁 게임(18~24시)' 패턴을
    1분 간격으로 생성한다. 매일 새벽 시간대는 로그가 없어(2시간 이상 공백)
    절전모드 인식(KAN-167) 세그먼트 분리를 그대로 재현한다."""
    gpu_name = gpu_name or "GPU"
    logs = []
    base_kst = datetime(2026, 5, 21, 0, 0, 0, tzinfo=KST)

    for day in range(7):
        day_start = base_kst + timedelta(days=day)

        dev_start_h  = random.uniform(10.0, 13.0)
        dev_dur_min  = random.randint(50, 100)

        idle_start_h = random.uniform(15.0, 17.0)
        idle_dur_min = random.randint(20, 65)

        game_start_h = random.uniform(18.0, 22.0)
        game_dur_min = random.randint(70, 120)

        # 그날의 첫 세션(개발) 시작 시각을 부팅 시각으로 사용
        boot_time = (day_start + timedelta(hours=dev_start_h)).astimezone(timezone.utc)

        for start_h, dur_min, mode in (
            (dev_start_h,  dev_dur_min,  "dev"),
            (idle_start_h, idle_dur_min, "idle"),
            (game_start_h, game_dur_min, "game"),
        ):
            session_start = day_start + timedelta(hours=start_h)
            for i in range(dur_min):
                ts = (session_start + timedelta(minutes=i)).astimezone(timezone.utc)
                logs.append(_make_snapshot(ts, mode, gpu_name, boot_time))

    return logs


# ── 보고서 생성 ──────────────────────────────────────────────────────────────

def main():
    print("더미 모니터링 데이터 생성 중...")
    logs = _generate_logs()
    print(f"  스냅샷 수: {len(logs)}개")

    print("데이터 분석 중...")
    data = collect_report_data(logs, PROFILE, user_preferences=USER_PREFERENCES)
    data["user_preferences"] = USER_PREFERENCES

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
