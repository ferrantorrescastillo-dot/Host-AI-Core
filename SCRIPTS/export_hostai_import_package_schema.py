from __future__ import annotations

import argparse
import json
from pathlib import Path

from MODELOS.hostai_import_package import hostai_import_package_json_schema


def main() -> int:
    parser = argparse.ArgumentParser(description="Exporta el JSON Schema oficial de HostAIImportPackage.")
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    args.destination.write_text(
        json.dumps(hostai_import_package_json_schema(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(args.destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
