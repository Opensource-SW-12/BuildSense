import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_DIR = PROJECT_ROOT / "open-db" / "Storage"

SSD_OUTPUT_FILE = PROJECT_ROOT / "data" / "specs" / "ssd_specs.json"
HDD_OUTPUT_FILE = PROJECT_ROOT / "data" / "specs" / "hdd_specs.json"


def to_int(value):
    if value is None:
        return None

    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def normalize_storage(raw_data, opendb_id, index, storage_type):
    metadata = raw_data.get("metadata", {})
    appearance = raw_data.get("appearance", {})

    release_year = to_int(metadata.get("releaseYear"))

    data = {
        "part_id": f"{storage_type.lower()}_{index:04d}",
        "opendb_id": opendb_id,
        "category": storage_type.lower(),

        "name": metadata.get("name", ""),
        "manufacturer": metadata.get("manufacturer", ""),
        "series": metadata.get("series", ""),
        "variant": metadata.get("variant", ""),
        "release_year": release_year,

        "storage_type": storage_type,
        "capacity_gb": raw_data.get("capacity", None),
        "form_factor": raw_data.get("form_factor", None),
        "interface": raw_data.get("interface", None),
        "cache_mb": raw_data.get("cache", None),
        "lighting": raw_data.get("lighting", appearance.get("lighting", None))
    }

    if storage_type == "SSD":
        data["nvme"] = raw_data.get("nvme", None)

    return data


def main():
    SSD_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    ssd_list = []
    hdd_list = []

    storage_files = sorted(INPUT_DIR.glob("*.json"))

    for storage_file in storage_files:
        try:
            with storage_file.open("r", encoding="utf-8") as file:
                raw_data = json.load(file)

        except json.JSONDecodeError:
            print(f"skip: {storage_file.name}")
            continue

        opendb_id = storage_file.stem
        raw_type = raw_data.get("type", "")

        if raw_type == "SSD":
            ssd_list.append(
                normalize_storage(
                    raw_data,
                    opendb_id,
                    len(ssd_list) + 1,
                    "SSD"
                )
            )

        elif raw_type == "HDD":
            hdd_list.append(
                normalize_storage(
                    raw_data,
                    opendb_id,
                    len(hdd_list) + 1,
                    "HDD"
                )
            )

    with SSD_OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(ssd_list, file, indent=2, ensure_ascii=False)

    with HDD_OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(hdd_list, file, indent=2, ensure_ascii=False)

    print(f"SSD specs normalized: {len(ssd_list)}")
    print(f"HDD specs normalized: {len(hdd_list)}")


if __name__ == "__main__":
    main()