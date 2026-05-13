import csv
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SPECS_DIR = PROJECT_ROOT / "data" / "specs"
EXPORTS_DIR = PROJECT_ROOT / "exports"


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

    json_files = sorted(SPECS_DIR.glob("*.json"))

    for json_path in json_files:
        export_json_to_csv(json_path)


if __name__ == "__main__":
    main()