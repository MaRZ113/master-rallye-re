"""Inventory development/editor broker configs in supplied Master Rallye corpora.

The scanner only reads source corpus files. It emits paths and selected XML
metadata; it never extracts or copies game data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


BUILD_LAYOUTS = {
    "8.4.1": ("demo-8.4.1", ""),
    "9.3.1": ("demo-9.3.1", ""),
    "9.10.0": ("demo-9.10.0", ""),
    "retail": ("retail", "Data.sma_unpacked"),
}
CONFIG_NAMES = ("Game", "dev", "Editors")
DEVELOPMENT_KEYS = (
    "DebugWindow/Enabled",
    "Menues/Enabled",
    "Editing/EditorsOpen",
    "ModelCaching/CachingDisabled",
    "Camera0/SwitchTarget",
    "Camera0/SwitchType",
    "Scene/HatchEggsOnLoad",
    "Scene/ResetSceneOnLoad",
    "Scene/StartScene",
)
DEVELOPMENT_LOAD_KEYS = {"Load/Dev", "Load/Editors"}


def _parse_values(path: Path) -> dict[str, Any]:
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as error:
        return {"status": "error", "error": str(error), "values": []}

    values: list[dict[str, Any]] = []
    for element in root.iter():
        if element.tag.casefold() != "value":
            continue
        name = element.attrib.get("Name")
        if name is None:
            continue
        values.append(
            {
                "name": name,
                "type": element.attrib.get("Type"),
                "value": element.attrib.get("Value"),
                "save_options": element.attrib.get("SaveOptions"),
                "save_player_state": element.attrib.get("SavePlayerState"),
            }
        )
    return {"status": "parsed", "root_tag": root.tag, "values": values}


def _data_root(corpus_root: Path, build: str) -> tuple[Path, str]:
    folder, prefix = BUILD_LAYOUTS[build]
    return corpus_root / folder / prefix, prefix


def _source_metadata(path: Path, corpus_root: Path, build: str) -> dict[str, Any]:
    corpus_directory, prefix = BUILD_LAYOUTS[build]
    corpus_identity = (Path(corpus_directory) / prefix).as_posix().rstrip("/")
    relative_path = path.relative_to(corpus_root).as_posix()
    metadata: dict[str, Any] = {
        "build": build,
        "corpus_identity": corpus_identity,
        "source_relative_path": relative_path,
        "source_size_bytes": None,
        "source_sha256": None,
    }
    if path.is_file():
        payload = path.read_bytes()
        metadata["source_size_bytes"] = len(payload)
        metadata["source_sha256"] = hashlib.sha256(payload).hexdigest()
    return metadata


def _resolve_case_insensitive_file(directory: Path, requested_name: str) -> Path | None:
    """Model Windows filename lookup when inventory runs on a case-sensitive host."""
    if not directory.is_dir():
        return None
    matches = [
        path
        for path in directory.iterdir()
        if path.is_file() and path.name.casefold() == requested_name.casefold()
    ]
    if not matches:
        return None
    return min(matches, key=lambda path: (path.name != requested_name, path.name.casefold(), path.name))


def _loaded_config_names(game_values: list[dict[str, Any]]) -> list[dict[str, str]]:
    loaded = []
    for item in game_values:
        if not item["name"].startswith("Load/") or item["type"] != "XmlFilename":
            continue
        loaded.append(
            {
                "key": item["name"],
                "value": item["value"] or "",
                "file": f"DataGame/{item['value']}.xml" if item["value"] else "",
            }
        )
    return loaded


def inventory_corpora(corpus_root: Path) -> dict[str, Any]:
    """Return selected development/config anchors for the four build layouts."""
    result: dict[str, Any] = {"schema_version": 3, "builds": {}}
    for build in BUILD_LAYOUTS:
        root, prefix = _data_root(corpus_root, build)
        datagame = root / "DataGame"
        corpus_directory, _ = BUILD_LAYOUTS[build]
        corpus_identity = (Path(corpus_directory) / prefix).as_posix().rstrip("/")
        config_records: dict[str, Any] = {}
        for config_name in CONFIG_NAMES:
            relpath = f"DataGame/{config_name}.xml"
            path = datagame / f"{config_name}.xml"
            record = _parse_values(path) if path.is_file() else {"status": "missing", "values": []}
            record["path"] = (Path(prefix) / relpath).as_posix() if prefix else relpath
            record.update(_source_metadata(path, corpus_root, build))
            # Keep the report architectural: retain the load graph from Game.xml
            # and only the development/editor keys from Dev/Editors, not every
            # unrelated value in those files.
            if record.get("status") == "parsed":
                if config_name == "Game":
                    record["values"] = [
                        value
                        for value in record["values"]
                        if value["type"] == "XmlFilename"
                        and value["name"] in DEVELOPMENT_LOAD_KEYS
                    ]
                else:
                    record["values"] = [
                        value
                        for value in record["values"]
                        if value["name"] in DEVELOPMENT_KEYS
                    ]
            config_records[config_name] = record

        game_values = config_records["Game"].get("values", [])
        loaded = _loaded_config_names(game_values)
        for item in loaded:
            requested_name = f"{item['value']}.xml" if item["value"] else ""
            resolved = _resolve_case_insensitive_file(datagame, requested_name) if requested_name else None
            item["requested_file"] = item["file"]
            item["file"] = f"DataGame/{requested_name}" if requested_name else ""
            item["resolved_path"] = (
                (Path(prefix) / "DataGame" / resolved.name).as_posix()
                if resolved is not None and prefix
                else (Path("DataGame") / resolved.name).as_posix()
                if resolved is not None
                else None
            )
            item["lookup_model"] = "case-insensitive Windows filename semantics"
            item["exists"] = resolved is not None

        relevant_values = []
        for config_name, record in config_records.items():
            for item in record.get("values", []):
                if item["name"] in DEVELOPMENT_KEYS:
                    relevant_values.append({"file": record["path"], **item})

        dataeditors = root / "DataEditors"
        editor_files = []
        if dataeditors.is_dir():
            for path in sorted(dataeditors.rglob("*")):
                if not path.is_file():
                    continue
                payload = path.read_bytes()
                editor_files.append(
                    {
                        "path": path.relative_to(root).as_posix(),
                        "size": len(payload),
                        "sha256": hashlib.sha256(payload).hexdigest(),
                        "extension": path.suffix.lower(),
                        "referenced_editor": next(
                            (
                                editor
                                for editor in ("Particle", "Egg", "Marker", "Broker")
                                if editor.casefold() in path.name.casefold()
                            ),
                            None,
                        ),
                        "content_classification": (
                            "human-readable text candidate"
                            if path.suffix.lower() in {".txt", ".xml", ".ini", ".md"}
                            else "binary or unclassified file"
                        ),
                    }
                )
        result["builds"][build] = {
            "build": build,
            "corpus_directory": BUILD_LAYOUTS[build][0],
            "corpus_identity": corpus_identity,
            "data_root_prefix": prefix,
            "configs": config_records,
            "game_xml_load_order": loaded,
            "development_values": relevant_values,
            "dataeditors_directory_present": dataeditors.is_dir(),
            "dataeditors_files": editor_files,
        }
    return result


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Development/editor configuration inventory",
        "",
        "Selected-anchor report: Load/Dev, Load/Editors, development/editor keys and DataEditors files only; this is not a full XML dump.",
        "Generated by `tools/scanner/r_dev1_config_inventory.py`. Values below are corpus observations, not compiled fallbacks or effective runtime values.",
        "",
    ]
    for build, record in report["builds"].items():
        lines += [f"## {build}", "", f"Corpus identity: `{record['corpus_identity']}`.", "", "Game.xml `Load/*` sequence:", ""]
        if record["game_xml_load_order"]:
            lines += [
                f"- `{item['key']}` = `{item['value']}` → requested `{item['file']}`; resolved `{item['resolved_path'] or 'missing'}` ({'present' if item['exists'] else 'missing'})"
                for item in record["game_xml_load_order"]
            ]
        else:
            lines.append("- No parsed `Load/*` values.")
        lines += ["", "Development/editor values:", ""]
        if record["development_values"]:
            lines += [
                f"- `{item['name']}` ({item.get('type')}) = `{item.get('value')}` in `{item['file']}`"
                for item in record["development_values"]
            ]
        else:
            lines.append("- None of the selected keys were present in the inventoried files.")
        lines += ["", "Source XML provenance:", ""]
        for config_name, source in record["configs"].items():
            if source["status"] == "parsed":
                lines.append(
                    f"- `{source['source_relative_path']}` — {source['source_size_bytes']} bytes; SHA256 `{source['source_sha256']}`."
                )
            else:
                lines.append(f"- `{source['source_relative_path']}` — {source['status']}; no size/hash available.")
        lines += [
            "",
            f"DataEditors directory: {'present' if record['dataeditors_directory_present'] else 'not present in this supplied corpus view'}.",
        ]
        if record["dataeditors_files"]:
            lines.extend(
                f"- `{item['path']}` — {item['size']} bytes, SHA256 `{item['sha256']}`, {item['content_classification']}"
                for item in record["dataeditors_files"]
            )
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpora-root", type=Path, required=True)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args(argv)
    report = inventory_corpora(args.corpora_root)
    json_text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    markdown_text = render_markdown(report)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json_text, encoding="utf-8")
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(markdown_text, encoding="utf-8")
    if not args.json_output and not args.markdown_output:
        sys.stdout.write(json_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
