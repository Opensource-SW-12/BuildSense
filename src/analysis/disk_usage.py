import subprocess
from collections import Counter

from src.normalization.core import calculate_basic_stats

_CREATE_NO_WINDOW = 0x08000000


def _mode(values):
    if not values:
        return None
    return Counter(round(v, 1) for v in values).most_common(1)[0][0]


def _free_stats(values):
    valid = [v for v in values if v is not None]
    if not valid:
        return {"min": None, "average": None, "median": None}
    sorted_v = sorted(valid)
    return {
        "min": sorted_v[0],
        "average": sum(valid) / len(valid),
        "median": sorted_v[len(sorted_v) // 2],
    }


def _run_ps(cmd: str) -> str:
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            capture_output=True, text=True, timeout=10,
            creationflags=_CREATE_NO_WINDOW,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _get_drive_type_map() -> dict[str, str]:
    """드라이브 문자 (예: 'C') -> 미디어 타입 ('NVMe'/'SSD'/'HDD'/'Unknown') 매핑"""
    try:
        # 논리 디스크 -> 디스크 인덱스 매핑
        ld_out = _run_ps(
            "Get-WmiObject Win32_LogicalDiskToPartition | "
            "ForEach-Object { "
            "  ($_.Antecedent -replace '.*Disk #(\\d+).*','$1') + ',' + "
            "  ($_.Dependent  -replace '.*DeviceID=\"\"(.+)\"\".*','$1') "
            "}"
        )

        disk_to_drives: dict[str, list[str]] = {}
        for line in ld_out.splitlines():
            line = line.strip()
            if "," not in line:
                continue
            disk_idx, drive_raw = line.split(",", 1)
            drive_letter = drive_raw.strip().strip('"').rstrip(":").upper()
            if drive_letter:
                disk_to_drives.setdefault(disk_idx.strip(), []).append(drive_letter)

        # 물리 디스크 인덱스 -> 미디어 타입
        pd_out = _run_ps(
            "Get-PhysicalDisk | "
            "Select-Object DeviceId,MediaType,BusType | "
            "ConvertTo-Csv -NoTypeInformation"
        )

        idx_to_type: dict[str, str] = {}
        for line in pd_out.splitlines()[1:]:
            cols = [c.strip('"') for c in line.split('","')]
            if len(cols) < 3:
                continue
            dev_id, media_type, bus_type = cols[0].strip(), cols[1].strip(), cols[2].strip()
            if bus_type == "NVMe":
                disk_type = "NVMe"
            elif media_type == "SSD":
                disk_type = "SSD"
            elif media_type == "HDD":
                disk_type = "HDD"
            else:
                disk_type = "Unknown"
            idx_to_type[dev_id] = disk_type

        result: dict[str, str] = {}
        for disk_idx, drives in disk_to_drives.items():
            disk_type = idx_to_type.get(disk_idx, "Unknown")
            for drive in drives:
                result[drive] = disk_type
        return result
    except Exception:
        return {}


def analyze_disk_usage(logs):
    drive_type_map = _get_drive_type_map()
    drive_snapshots: dict[str, list[dict]] = {}

    for log in logs:
        for disk in log.get("disks", []):
            mp = disk.get("mountpoint")
            if not mp:
                continue
            drive_snapshots.setdefault(mp, []).append(disk)

    result = {}
    for mountpoint, snapshots in drive_snapshots.items():
        total_values   = [s["total_gb"]  for s in snapshots if s.get("total_gb")  is not None]
        used_values    = [s["used_gb"]   for s in snapshots if s.get("used_gb")   is not None]
        free_values    = [s["free_gb"]   for s in snapshots if s.get("free_gb")   is not None]
        percent_values = [s["percent"]   for s in snapshots if s.get("percent")   is not None]

        total_snaps = len(snapshots)
        danger_count = sum(1 for p in percent_values if p >= 90)

        # 마운트포인트에서 드라이브 문자 추출 (예: "C:\\" -> "C")
        drive_letter = mountpoint.replace("\\", "").replace("/", "").replace(":", "")[:1].upper()
        drive_type = drive_type_map.get(drive_letter, "Unknown")

        result[mountpoint] = {
            "drive_type":    drive_type,
            "total_gb":      _mode(total_values),
            "used_gb_stats": calculate_basic_stats(used_values),
            "free_gb_stats": _free_stats(free_values),
            "percent_stats": calculate_basic_stats(percent_values),
            "danger_ratio":  danger_count / total_snaps if total_snaps > 0 else 0,
        }

    return result
