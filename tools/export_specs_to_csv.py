import csv
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SPECS_DIR = PROJECT_ROOT / "data" / "specs"
EXPORTS_DIR = PROJECT_ROOT / "exports"

SPEC_FILES = [
    "cpu_specs.json",
    "gpu_specs.json",
    "ram_specs.json",
    "psu_specs.json",
    "ssd_specs.json",
    "hdd_specs.json",
]


def flatten_dict(data, parent_key="", sep="_"):
    result = {}

    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key

        if isinstance(value, dict):
            result.update(flatten_dict(value, new_key, sep=sep))
        elif isinstance(value, list):
            result[new_key] = ", ".join(map(str, value))
        else:
            result[new_key] = value

    return result


def export_json_to_csv(json_path):
    with json_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not data:
        print(f"skip empty file: {json_path.name}")
        return

    flattened_data = [flatten_dict(item) for item in data]

    fieldnames = sorted(
        {key for item in flattened_data for key in item.keys()}
    )

    csv_name = json_path.stem + ".csv"
    csv_path = EXPORTS_DIR / csv_name

    with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flattened_data)

    print(f"exported: {csv_path}")


def main():
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    for file_name in SPEC_FILES:
        json_path = SPECS_DIR / file_name

        if not json_path.exists():
            print(f"skip missing file: {json_path.name}")
            continue

        export_json_to_csv(json_path)


if __name__ == "__main__":
    main()