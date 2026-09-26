#!/usr/bin/env python3
"""Read-only R-PHYS1 vehicle-config and model-directory inventory scanner."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from master_rallye.vehicle_config_analysis import (
    build_vehicle_schema,
    classify_config_families_against_directories,
    compare_vehicle_configs,
    config_schema_summary,
    family_value_rows,
    inventory_vehicle_directories,
    parse_vehicle_config,
)


BUILD_NAMES = ("8.4.1", "9.3.1", "9.10.0", "retail")
CONFIG_ONLY_ALIAS_CANDIDATES: dict[str, tuple[str, ...]] = {
    # Lexical candidates only. None of these pairings is treated as an alias.
    "Megane2": ("megane",),
    "Navarabig": ("Navara",),
    "Pajerostripe": ("Pajero",),
}
CONTROL_FAMILIES = ("Jump", "Navara", "Trooper", "NewRav", "Rav4")


def corpus_paths(corpora_root: Path) -> dict[str, dict[str, Path]]:
    result: dict[str, dict[str, Path]] = {}
    for build in BUILD_NAMES:
        root = corpora_root / ("retail" if build == "retail" else f"demo-{build}")
        if build == "retail":
            data_root = root / "Data.sma_unpacked"
        else:
            data_root = root
        result[build] = {
            "root": root,
            "xml": data_root / "DataGame" / "vehicles.xml",
            "vehicle_dirs": data_root / "DataGx" / "Vehicles",
            "exe": root / "MRallye.exe",
        }
    return result


def _family_name(document: Any, requested: str) -> str | None:
    matches = [name for name in document.families if name.casefold() == requested.casefold()]
    if len(matches) > 1:
        raise ValueError(f"ambiguous family spelling for {requested!r}: {matches}")
    return matches[0] if matches else None


def _demo_match_inventory(
    retail_orphans: list[dict[str, Any]],
    documents: dict[str, Any],
    model_dirs: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    result = []
    for orphan in retail_orphans:
        family = orphan["config_family"]
        folded = family.casefold()
        per_build = {}
        for build in BUILD_NAMES[:-1]:
            document = documents[build]
            config_names = [name for name in document.families if name.casefold() == folded]
            exact_dirs = [entry for entry in model_dirs[build] if entry["name"].casefold() == folded]
            alpha_dirs = [entry for entry in model_dirs[build]
                          if entry["name"].casefold() == f"{folded}alpha"]
            per_build[build] = {
                "matching_config_families_case_insensitive": config_names,
                "matching_model_directories_case_insensitive": [entry["name"] for entry in exact_dirs],
                "matching_alpha_directories_case_insensitive": [entry["name"] for entry in alpha_dirs],
                "model_assets_present": bool(exact_dirs or alpha_dirs),
                "car_dx_present": any(entry["car_dx"] for entry in exact_dirs),
                "complete_dx_present": any(entry["complete_dx"] for entry in exact_dirs),
                # Filesystem evidence does not establish that the vehicle is playable.
                "known_playable_demo_status": "UNKNOWN_FROM_CORPUS_INVENTORY",
            }
        result.append({**orphan, "demo_corpus_matches": per_build})
    return result


def collect_analysis(corpora_root: Path) -> dict[str, Any]:
    paths = corpus_paths(corpora_root)
    documents = {
        build: parse_vehicle_config(paths[build]["xml"], build=build)
        for build in BUILD_NAMES
    }
    directories = {
        build: inventory_vehicle_directories(paths[build]["vehicle_dirs"])
        for build in BUILD_NAMES
    }
    retail_dirs = directories["retail"]
    retail_families = list(documents["retail"].families)
    root_classification = classify_config_families_against_directories(
        retail_families,
        retail_dirs,
        possible_aliases=CONFIG_ONLY_ALIAS_CANDIDATES,
    )
    orphans = [entry for entry in root_classification
               if entry["status"] != "MATCHED_EXACT"
               and entry["status"] != "DIRECTORY_NAME_MISMATCH"]
    demo_matches = _demo_match_inventory(orphans, documents, directories)

    configs_by_build = {
        build: {
            "metadata": config_schema_summary(documents[build]),
            "family_names": sorted(documents[build].families,
                                    key=lambda item: (item.casefold(), item)),
            "excluded_families": {
                name: {"value_count": len(values),
                       "field_paths": sorted(values, key=str.casefold)}
                for name, values in documents[build].excluded_families.items()
            },
            "model_directory_names": [entry["name"] for entry in directories[build]],
            "model_directory_inventory": directories[build],
        }
        for build in BUILD_NAMES
    }

    comparisons = []
    # Compare every same-literal family identity (case-insensitive only) found
    # in at least two builds. This does not map lexical aliases such as Rav4
    # to NewRav or Navarabig to Navara.
    family_identities = sorted({name.casefold() for document in documents.values()
                                for name in document.families})
    for family in family_identities:
        for i, build_a in enumerate(BUILD_NAMES):
            name_a = _family_name(documents[build_a], family)
            if name_a is None:
                continue
            for build_b in BUILD_NAMES[i + 1:]:
                name_b = _family_name(documents[build_b], family)
                if name_b is None:
                    continue
                comparisons.append(compare_vehicle_configs(
                    documents[build_a], name_a, documents[build_b], name_b
                ))

    trooper_fields = {
        build: {
            "family": _family_name(documents[build], "Trooper"),
            "values": family_value_rows(documents[build], _family_name(documents[build], "Trooper") or "Trooper"),
        }
        for build in BUILD_NAMES
    }
    vehicle_schema = build_vehicle_schema(list(documents.values()))

    source_files = {}
    for build in BUILD_NAMES:
        record = {}
        for role in ("xml", "exe"):
            path = paths[build][role]
            if path.is_file():
                payload = path.read_bytes()
                record[role] = {
                    "path": str(path),
                    "file_size": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            else:
                record[role] = {"path": str(path), "status": "MISSING"}
        source_files[build] = record

    # Global tire definitions are preserved as an independent data family.
    global_schema = []
    for document in documents.values():
        for family, fields in document.excluded_families.items():
            for path, record in fields.items():
                global_schema.append({
                    "full_path": f"Vehicles/{family}/{path}",
                    "family": family,
                    "relative_path": path,
                    "type": record["type"],
                    "value": record["value"],
                    "build": document.build,
                    "config_sha256": document.sha256,
                })

    return {
        "schema_version": 1,
        "corpora_root": str(corpora_root),
        "source_files": source_files,
        "builds": configs_by_build,
        "retail": {
            "vehicle_family_names": sorted(retail_families,
                                            key=lambda item: (item.casefold(), item)),
            "vehicle_family_count": len(retail_families),
            "excluded_config_families": list(documents["retail"].excluded_families),
            "model_directory_names": [entry["name"] for entry in retail_dirs],
            "model_directory_count": len(retail_dirs),
            "family_directory_classification": root_classification,
            "config_only_or_possible_aliases": demo_matches,
        },
        "config_comparisons": comparisons,
        "trooper_full_config": trooper_fields,
        "control_family_names": list(CONTROL_FAMILIES),
        "vehicle_schema": vehicle_schema,
        "global_non_vehicle_schema": global_schema,
    }


def _markdown_summary(analysis: dict[str, Any]) -> str:
    retail = analysis["retail"]
    lines = [
        "# R-PHYS1 generated inventory summary",
        "",
        "This file is generated from read-only corpus inputs. Exact source hashes, full file lists, typed schema observations, and field-by-field comparisons are in `r-phys1-analysis.json`.",
        "",
        f"Retail vehicle config families: {retail['vehicle_family_count']}",
        f"Retail vehicle model directories: {retail['model_directory_count']}",
        "",
        "## Retail model folders",
        "",
        "| Exact folder name | car.dx | complete.dx | wheel.dx | DXT count | file count |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for entry in analysis["builds"]["retail"]["model_directory_inventory"]:
        lines.append(
            f"| `{entry['name']}` | {'yes' if entry['car_dx'] else 'no'} | "
            f"{'yes' if entry['complete_dx'] else 'no'} | {'yes' if entry['wheel_dx'] else 'no'} | "
            f"{entry['texture_count_dxt']} | {entry['file_count']} |"
        )
    lines.extend([
        "",
        "## Config families without exact retail model directory",
        "",
        "| Config family | Classification | Case-only directory match | Possible alias candidates | Demo config/assets evidence |",
        "|---|---|---|---|---|",
    ])
    for entry in retail["config_only_or_possible_aliases"]:
        demo = []
        for build, match in entry["demo_corpus_matches"].items():
            if match["matching_config_families_case_insensitive"] or match["model_assets_present"]:
                demo.append(
                    f"{build}: cfg={','.join(match['matching_config_families_case_insensitive']) or '—'}; "
                    f"dirs={','.join(match['matching_model_directories_case_insensitive'] + match['matching_alpha_directories_case_insensitive']) or '—'}"
                )
        lines.append(
            f"| `{entry['config_family']}` | `{entry['status']}` | "
            f"{', '.join(entry['case_insensitive_directory_matches']) or '—'} | "
            f"{', '.join(entry['possible_aliases']) or '—'} | {'<br>'.join(demo) or '—'} |"
        )
    lines.extend([
        "",
        "Names are preserved exactly. A possible alias candidate is a search lead, not a resolved identity. Directory presence is not proof of demo playability.",
        "",
    ])
    return "\n".join(lines)


def write_outputs(analysis: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "r-phys1-analysis.json").write_text(
        json.dumps(analysis, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (output_dir / "r-phys1-generated-inventory.md").write_text(
        _markdown_summary(analysis), encoding="utf-8"
    )
    (output_dir / "r-phys1-config-schema.json").write_text(
        json.dumps({
            "vehicle_schema": analysis["vehicle_schema"],
            "global_non_vehicle_schema": analysis["global_non_vehicle_schema"],
        }, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpora-root", type=Path, required=True,
                        help="read-only directory containing demo-8.4.1, demo-9.3.1, demo-9.10.0, retail")
    parser.add_argument("--output-dir", type=Path, default=Path(".research-output/r-phys1"),
                        help="ignored research-output directory")
    args = parser.parse_args()
    analysis = collect_analysis(args.corpora_root)
    write_outputs(analysis, args.output_dir)
    print(json.dumps({
        "output_dir": str(args.output_dir),
        "retail_vehicle_families": analysis["retail"]["vehicle_family_count"],
        "retail_model_directories": analysis["retail"]["model_directory_count"],
        "config_only": len(analysis["retail"]["config_only_or_possible_aliases"]),
        "config_comparison_count": len(analysis["config_comparisons"]),
        "vehicle_schema_fields": len(analysis["vehicle_schema"]),
    }, indent=2))


if __name__ == "__main__":
    main()
