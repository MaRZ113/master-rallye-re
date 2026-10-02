"""Read-only XML shape/metadata inventory, excluding values and object XML.

This uses ElementTree for inspection. It is not an emulator of the game's
ordered-attribute parser and does not validate native load compatibility.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


def inspect_xml(path: Path) -> dict:
    if path.stat().st_size > 16 * 1024 * 1024:
        raise ValueError("XML inspection size limit exceeded")
    raw = path.read_bytes()
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ValueError("DTD/entity declarations are not supported")
    root = ET.fromstring(raw)
    values = list(root.iter("Value"))
    names = [v.get("Name", "") for v in values]
    return {
        "filename": path.name, "size_bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
        "root": root.tag, "value_count": len(values),
        "type_counts": dict(sorted(Counter(v.get("Type", "UNKNOWN") for v in values).items())),
        "attribute_orders": [{"order": list(order), "count": count}
                             for order, count in sorted(Counter(tuple(v.attrib) for v in values).items())],
        "save_options": dict(sorted(Counter(v.get("SaveOptions", "MISSING") for v in values).items())),
        "save_player_state": dict(sorted(Counter(v.get("SavePlayerState", "MISSING") for v in values).items())),
        "path_roots": dict(sorted(Counter(name.partition("/")[0] for name in names).items())),
        "duplicate_path_count": sum(count - 1 for count in Counter(names).values() if count > 1),
        "representative_paths": sorted(set(names))[:12],
        "limitation": "No values or embedded XmlData copied; metadata inspection does not establish native parser acceptance.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    results = []
    for path in args.input:
        try:
            results.append(inspect_xml(path))
        except (OSError, ValueError, ET.ParseError) as exc:
            results.append({"filename": path.name, "error": str(exc)})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"schema_version": 1, "files": results}, indent=2) + "\n", encoding="utf-8")
    return int(any("error" in result for result in results))


if __name__ == "__main__":
    raise SystemExit(main())
