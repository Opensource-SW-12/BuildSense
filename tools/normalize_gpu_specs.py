import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_DIR = PROJECT_ROOT / "open-db" / "GPU"
OUTPUT_FILE = PROJECT_ROOT / "data" / "specs" / "gpu_specs.json"


def to_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def normalize_gpu(raw_data, opendb_id, index):
    metadata = raw_data.get("metadata", {})
    specs = raw_data.get("specifications", {})
    memory = specs.get("memory", {})
    clocks = raw_data.get("clocks", {})
    power = specs.get("power", {})
    connectors = power.get("connectors", {})
    physical = specs.get("physical", {})
    appearance = raw_data.get("appearance", {})

    release_year = to_int(metadata.get("releaseYear"))

    return {
        "part_id": f"gpu_{index:04d}",
        "opendb_id": opendb_id,
        "category": "gpu",

        "name": metadata.get("name", ""),
        "manufacturer": metadata.get("manufacturer", ""),
        "series": metadata.get("series", ""),
        "variant": metadata.get("variant", ""),
        "release_year": release_year,

        "chipset": raw_data.get("chipset", None),
        "chipset_manufacturer": raw_data.get("chipsetManufacturer", None),

        "core_count": to_int(raw_data.get("coreCount")),
        "clock_base": raw_data.get("baseClock", None),
        "clock_boost": raw_data.get("boostClock", None),

        "memory_gb": memory.get("capacityGb", None),
        "memory_type": memory.get("type", None),
        "memory_bus": memory.get("busWidth", None),

        "tdp": power.get("tdp", None),
        "interface": specs.get("interface", None),
        "length_mm": physical.get("lengthMm", None),

        "power_connector_pcie_8pin": connectors.get("pcie8pin", None),
        "power_connector_pcie_6pin": connectors.get("pcie6pin", None),
        "power_connector_pcie_12vhpwr": connectors.get("pcie12vhpwr", None),
        "power_connector_pcie_12v2x6": connectors.get("pcie12v2x6", None),

        "color": appearance.get("color", []),
        "lighting": appearance.get("lighting", None),
        "manufacturer_color": appearance.get("manufacturerColor", None)
    }


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    normalized_gpus = []

    gpu_files = sorted(INPUT_DIR.glob("*.json"))

    for index, gpu_file in enumerate(gpu_files, start=1):
        try:
            with gpu_file.open("r", encoding="utf-8") as file:
                raw_data = json.load(file)
        except json.JSONDecodeError:
            print(f"skip: {gpu_file.name}")
            continue

        opendb_id = gpu_file.stem

        normalized_gpus.append(
            normalize_gpu(raw_data, opendb_id, index)
        )

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(normalized_gpus, file, indent=2, ensure_ascii=False)

    print(f"GPU specs normalized: {len(normalized_gpus)}")


if __name__ == "__main__":
    main()