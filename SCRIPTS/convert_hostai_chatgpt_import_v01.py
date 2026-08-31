from __future__ import annotations

import argparse
import json
from pathlib import Path

from SERVICIOS.hostai_chatgpt_import_v01_converter import ChatGPTImportV01Converter
from SERVICIOS.hostai_import_package_adapter import PreparedImportPackageAdapter


def main() -> int:
    parser = argparse.ArgumentParser(description="Convierte el prototipo ChatGPT al HostAIImportPackage 0.1.")
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    prototype = json.loads(args.source.read_text(encoding="utf-8"))
    package = ChatGPTImportV01Converter().convert(prototype)
    PreparedImportPackageAdapter.validate(package)
    args.destination.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "valid": True, "destination": str(args.destination),
        "recipes": len(package["recipes"]), "variant_groups": len(package["variant_groups"]),
        "articles": len(package["articles"]), "menus": len(package["menus"]),
        "ambiguities": len(package["ambiguities"]),
        "unmigrated": package["metadata"]["migration_warnings"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
