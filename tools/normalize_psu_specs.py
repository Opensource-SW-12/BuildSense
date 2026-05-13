import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_DIR = PROJECT_ROOT / "open-db" / "PSU"
OUTPUT_FILE = PROJECT_ROOT / "data" / "specs" / "psu_specs.json"


def to_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def normalize_psu(raw_data, opendb_id, index):
    metadata = raw_data.get("metadata", {})
    specs = raw_data.get("specifications", {})
    connectors = specs.get("connectors", {})
    appearance = raw_data.get("appearance", {})

    release_year = to_int(metadata.get("releaseYear"))

    return {
        "part_id": f"psu_{index:04d}",
        "opendb_id": opendb_id,
        "category": "psu",

        "name": metadata.get("name", ""),
        "manufacturer": metadata.get("manufacturer", ""),
        "series": metadata.get("series", ""),
        "variant": metadata.get("variant", ""),
        "release_year": release_year,

        "wattage": specs.get("wattage", None),
        "efficiency_rating": specs.get("efficiencyRating", None),
        "modular": specs.get("modular", None),
        "form_factor": specs.get("formFactor", None),
        "fanless": specs.get("fanless", None),

        "connector_atx_24pin": connectors.get("atx24pin", None),
        "connector_eps_8pin": connectors.get("eps8pin", None),
        "connector_pcie_6plus2pin": connectors.get("pcie6plus2pin", None),
        "connector_pcie_12vhpwr": connectors.get("pcie12vhpwr", None),
        "connector_sata": connectors.get("sata", None),
        "connector_molex": connectors.get("molex", None),

        "color": appearance.get("color", []),
        "lighting": appearance.get("lighting", None),
        "manufacturer_color": appearance.get("manufacturerColor", None)
    }


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    normalized_psus = []

    psu_files = sorted(INPUT_DIR.glob("*.json"))

    for index, psu_file in enumerate(psu_files, start=1):
        try:
            with psu_file.open("r", encoding="utf-8") as file:
                raw_data = json.load(file)
        except json.JSONDecodeError:
            print(f"skip: {psu_file.name}")
            continue

        opendb_id = psu_file.stem
        normalized_psus.append(normalize_psu(raw_data, opendb_id, index))

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(normalized_psus, file, indent=2, ensure_ascii=False)

    print(f"PSU specs normalized: {len(normalized_psus)}")


if __name__ == "__main__":
    main()