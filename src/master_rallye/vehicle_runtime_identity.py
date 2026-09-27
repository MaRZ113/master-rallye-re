"""Conservative evidence helpers for the R-PHYS2 vehicle identity audit.

Corpus observations, executable string references, and user-supplied design
context are represented as separate evidence sources. This module does not
resolve aliases or infer a named-family-to-runtime-slot mapping.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


BUILD_NAMES = ("8.4.1", "9.3.1", "9.10.0", "retail")
TEXT_EXTENSIONS = {".xml", ".xml#", ".txt", ".cfg", ".ini", ".csv", ".json", ".lua", ".js", ".dat"}
BINARY_METADATA_EXTENSIONS = {".dx", ".dxb", ".sfl", ".hnt"}

QUERY_PATTERNS: tuple[tuple[str, str], ...] = (
    ("numeric_vehicle_path", r"\bVehicles[/\\]Car(?:\d+|%d)(?:[/\\][\w%.-]+)*"),
    ("numeric_race_path", r"\bRace[/\\]Car(?:\d+|%d)(?:[/\\][\w%.-]+)*"),
    ("frontend_car_slot", r"\bFrontend[/\\](?:QuickRace|Network)[/\\]Car\d+\b"),
    ("car_model_data_file", r"\bCarModelDataFile\b"),
    ("vehicle_param_broker", r"\bVehicleParamBroker\b|\bVehicleParams?\b"),
    ("car_type_key", r"\bCarType\b"),
)
_TEXT_REGEXES = tuple((name, re.compile(pattern, re.IGNORECASE)) for name, pattern in QUERY_PATTERNS)
_BYTE_REGEXES = tuple(
    (name, re.compile(pattern.encode("ascii"), re.IGNORECASE)) for name, pattern in QUERY_PATTERNS
)
_VALUE_TAG = re.compile(r"<Value\b[^>]*>", re.IGNORECASE)
_XML_ATTRIBUTE = re.compile(r"([A-Za-z_:][\w:.-]*)\s*=\s*([\"'])(.*?)\2", re.DOTALL)
_SCENE_CAR_TYPE = re.compile(r"Race[/\\]Car(?P<index>\d+)[/\\]CarType\Z", re.IGNORECASE)


USER_SUPPLIED_CONTEXT: tuple[dict[str, str], ...] = (
    {
        "subject": "retail/Ufo/wheel.dx",
        "classification": "USER_SUPPLIED_DESIGN_CONTEXT",
        "claim": "The wheel.dx omission is intentional; Ufo is a wheel-less model.",
        "source": "user-supplied project context; not inferred by the corpus scanner",
    },
    {
        "subject": "retail/forklift",
        "classification": "USER_SUPPLIED_CUT_HIDDEN_CONTEXT",
        "claim": "The model is a cut/hidden bonus vehicle associated with a hidden 25th slot.",
        "source": "user-supplied project context; not inferred by the corpus scanner",
    },
)

def _build_roots(corpora_root: Path, build: str) -> list[tuple[str, Path]]:
    root = corpora_root / ("retail" if build == "retail" else f"demo-{build}")
    roots: list[tuple[str, Path]] = []
    for base in (root, root / "Data.sma_unpacked"):
        for area in ("DataGame", "DataGx", "DataScene"):
            candidate = base / area
            if candidate.is_dir():
                try:
                    resolved = candidate.resolve()
                except OSError:
                    resolved = candidate.absolute()
                if all(existing.resolve() != resolved for _, existing in roots):
                    roots.append((area, candidate))
    return roots


def _decode_text(payload: bytes) -> str:
    if payload.startswith((b"\xff\xfe", b"\xfe\xff")):
        return payload.decode("utf-16", errors="replace")
    if payload.count(b"\x00") > max(8, len(payload) // 12):
        # Most supported game metadata is ASCII/UTF-8; this branch catches BOM-less
        # UTF-16 text without treating ordinary non-ASCII UTF-8 as wide text.
        encoding = "utf-16le" if payload[1::2].count(0) > payload[0::2].count(0) else "utf-16be"
        return payload.decode(encoding, errors="replace")
    return payload.decode("utf-8-sig", errors="replace")


def _record_text_hits(path: Path, corpus_root: Path, build: str, area: str) -> list[dict[str, Any]]:
    payload = path.read_bytes()
    text = _decode_text(payload)
    digest = hashlib.sha256(payload).hexdigest()
    try:
        relative = path.relative_to(corpus_root).as_posix()
    except ValueError:
        relative = path.as_posix()
    rows: list[dict[str, Any]] = []
    for category, regex in _TEXT_REGEXES:
        for match in regex.finditer(text):
            start, end = match.span()
            rows.append({
                "build": build,
                "area": area,
                "path": relative,
                "category": category,
                "match": match.group(0),
                "character_offset": start,
                "snippet": text[max(0, start - 64):min(len(text), end + 64)].replace("\r", " ").replace("\n", " "),
                "source_size": len(payload),
                "source_sha256": digest,
                "encoding_detection": "BOM_OR_NULL_HEURISTIC",
            })
    for tag_match in _VALUE_TAG.finditer(text):
        attributes = {
            name.casefold(): html.unescape(value)
            for name, _quote, value in _XML_ATTRIBUTE.findall(tag_match.group(0))
        }
        name = attributes.get("name", "")
        key_match = _SCENE_CAR_TYPE.fullmatch(name)
        if key_match is None:
            continue
        start, end = tag_match.span()
        rows.append({
            "build": build,
            "area": area,
            "path": relative,
            "category": "scene_race_car_type_assignment",
            "match": name,
            "participant_index": int(key_match.group("index")),
            "value_type": attributes.get("type"),
            "value": attributes.get("value"),
            "character_offset": start,
            "snippet": text[max(0, start - 32):min(len(text), end + 32)].replace("\r", " ").replace("\n", " "),
            "source_size": len(payload),
            "source_sha256": digest,
            "encoding_detection": "BOM_OR_NULL_HEURISTIC",
        })
    return rows


def _record_binary_hits(path: Path, corpus_root: Path, build: str, area: str,
                        chunk_size: int = 1024 * 1024) -> list[dict[str, Any]]:
    """Search compiled metadata for ASCII and UTF-16LE strings without loading it all."""
    size = path.stat().st_size
    digest = hashlib.sha256()
    seen: set[tuple[str, int, str]] = set()
    rows: list[dict[str, Any]] = []
    carry = b""
    byte_count = 0
    text_carry = ""
    char_count = 0
    max_chars = 256
    with path.open("rb") as stream:
        while True:
            block = stream.read(chunk_size)
            if not block:
                break
            digest.update(block)
            combined = carry + block
            base_byte = byte_count - len(carry)
            for category, regex in _BYTE_REGEXES:
                for match in regex.finditer(combined):
                    offset = base_byte + match.start()
                    key = (category, offset, "ascii")
                    if key in seen:
                        continue
                    seen.add(key)
                    rows.append({
                        "build": build, "area": area,
                        "path": path.relative_to(corpus_root).as_posix(),
                        "category": category, "match": match.group(0).decode("ascii", errors="replace"),
                        "byte_offset": offset, "encoding_detection": "ASCII_BYTES",
                        "source_size": size,
                    })
            carry = combined[-512:]
            if len(carry) % 2:
                carry = carry[1:]

            # Search a decoded UTF-16LE view too. Offsets are byte offsets in the
            # original file; duplicate chunk-overlap hits are de-duplicated above.
            wide_combined = text_carry + combined.decode("utf-16le", errors="ignore")
            wide_base_char = char_count - len(text_carry)
            for category, regex in _TEXT_REGEXES:
                for match in regex.finditer(wide_combined):
                    offset = 2 * (wide_base_char + match.start())
                    key = (category, offset, "utf16le")
                    if key in seen:
                        continue
                    seen.add(key)
                    rows.append({
                        "build": build, "area": area,
                        "path": path.relative_to(corpus_root).as_posix(),
                        "category": category, "match": match.group(0),
                        "byte_offset": offset, "encoding_detection": "UTF16LE_CANDIDATE",
                        "source_size": size,
                    })
            text_carry = wide_combined[-max_chars:]
            # Track absolute decoded character positions on the actual block,
            # excluding the carry to prevent offsets drifting between chunks.
            char_count += len(block.decode("utf-16le", errors="ignore"))
            byte_count += len(block)
    final_hash = digest.hexdigest()
    for row in rows:
        row["source_sha256"] = final_hash
    return rows


def scan_corpus_metadata(corpora_root: Path) -> dict[str, Any]:
    """Scan textlike config and compiled metadata in DataGame/DataGx/DataScene trees."""
    text_hits: list[dict[str, Any]] = []
    binary_hits: list[dict[str, Any]] = []
    text_files = 0
    binary_files = 0
    for build in BUILD_NAMES:
        for area, root in _build_roots(corpora_root, build):
            for path in sorted(root.rglob("*"), key=lambda item: item.as_posix().casefold()):
                if not path.is_file():
                    continue
                suffix = path.suffix.casefold()
                if suffix in TEXT_EXTENSIONS:
                    text_files += 1
                    text_hits.extend(_record_text_hits(path, corpora_root, build, area))
                elif suffix in BINARY_METADATA_EXTENSIONS:
                    binary_files += 1
                    binary_hits.extend(_record_binary_hits(path, corpora_root, build, area))
    category_counts: dict[str, int] = {name: 0 for name, _pattern in QUERY_PATTERNS}
    category_counts["scene_race_car_type_assignment"] = 0
    file_counts: dict[str, int] = {}
    for row in text_hits + binary_hits:
        category_counts[row["category"]] = category_counts.get(row["category"], 0) + 1
        key = f'{row["build"]}:{row["path"]}'
        file_counts[key] = file_counts.get(key, 0) + 1
    return {
        "corpora_root": str(corpora_root),
        "text_file_count": text_files,
        "compiled_metadata_file_count": binary_files,
        "text_hits": text_hits,
        "compiled_metadata_hits": binary_hits,
        "hit_category_counts": dict(sorted(category_counts.items())),
        "hit_file_count": len(file_counts),
    }


def summarize_ghidra_xrefs(payload: dict[str, Any] | None) -> dict[str, Any]:
    if payload is None:
        return {"status": "GHIDRA_XREF_INPUT_MISSING", "string_count": 0, "relevant_strings": []}
    relevant = []
    for row in payload.get("strings", []):
        value = str(row.get("value", ""))
        lowered = value.casefold()
        if not any(term in lowered for term in (
            "vehicles/car", "race/car", "cartype", "carmodeldatafile",
            "vehicleparambroker", "vehicleparams",
        )):
            continue
        relevant.append({
            "address": row.get("address"),
            "value": value,
            "xref_count": row.get("xref_count", 0),
            "xrefs": [
                {key: ref.get(key) for key in ("from", "type", "function", "read", "write")}
                for ref in row.get("xrefs", [])
            ],
        })
    relevant.sort(key=lambda item: (str(item["value"]).casefold(), str(item["address"])))
    return {
        "status": "GHIDRA_STATIC_STRING_XREFS",
        "program": payload.get("program"),
        "image_base": payload.get("image_base"),
        "string_count": payload.get("string_count", len(payload.get("strings", []))),
        "relevant_strings": relevant,
    }


def _comparison(analysis: dict[str, Any], family: str, build_a: str, build_b: str) -> dict[str, Any] | None:
    for row in analysis.get("config_comparisons", []):
        if (row.get("family_a", "").casefold() == family.casefold()
                and row.get("build_a") == build_a and row.get("build_b") == build_b):
            return row
    return None


def trooper_survival_profile(analysis: dict[str, Any]) -> dict[str, Any]:
    trooper = _comparison(analysis, "Trooper", "9.10.0", "retail")
    if trooper is None:
        return {"status": "COMPARISON_MISSING"}
    controls = {
        name: _comparison(analysis, name, "9.10.0", "retail")
        for name in ("Jump", "Navara")
    }
    control_changed = {
        name: {field["path"] for field in row.get("fields", [])
               if field.get("status") == "VALUE_CHANGED"} if row else set()
        for name, row in controls.items()
    }
    rows = trooper.get("fields", [])
    value_changed = {field["path"] for field in rows if field.get("status") == "VALUE_CHANGED"}
    control_changed_any = set().union(*control_changed.values())
    changed_fields = [
        {
            "path": field["path"],
            "status": field["status"],
            "classification": (
                "CONTROL_SHARED_RETAIL_CHANGE" if field["path"] in control_changed_any
                else "TROOPER_ONLY_IN_JUMP_NAVARA_CONTROLS"
            ),
            "value_9_10_0": field.get("value_a"),
            "value_retail": field.get("value_b"),
        }
        for field in rows if field.get("status") == "VALUE_CHANGED"
    ]
    return {
        "status": "COMPARES_NAMED_XML_CONFIG_ONLY",
        "build_a": "9.10.0", "build_b": "retail", "family": "Trooper",
        "field_count": trooper.get("field_count"),
        "status_counts": trooper.get("status_counts", {}),
        "control_families": {
            name: {
                "comparison_found": row is not None,
                "field_count": row.get("field_count") if row else None,
                "status_counts": row.get("status_counts", {}) if row else {},
                "value_changed_paths": sorted(control_changed[name]),
            }
            for name, row in controls.items()
        },
        "trooper_value_changed_path_count": len(value_changed),
        "control_shared_path_count": len(value_changed & control_changed_any),
        "trooper_only_control_paths": sorted(value_changed - control_changed_any),
        "value_changed_fields": changed_fields,
        "runtime_consumption_status": "UNRESOLVED_FOR_NAMED_FAMILY_FIELDS",
    }


def build_identity_layers(rphys1: dict[str, Any], text_scan: dict[str, Any],
                          ghidra: dict[str, Any]) -> dict[str, Any]:
    targets = ["Trooper", "Navara", "NewRav", "Rav4", "RMonster", "Ufo", "forklift"]
    builds: dict[str, Any] = {}
    for build_name, build in rphys1.get("builds", {}).items():
        dirs = build.get("model_directory_inventory", [])
        per_target = {}
        for target in targets:
            config_matches = [name for name in build.get("family_names", [])
                              if name.casefold() == target.casefold()]
            exact = [entry for entry in dirs if entry.get("name") == target]
            folded = [entry for entry in dirs if entry.get("name", "").casefold() == target.casefold()]
            per_target[target] = {
                "config_family_exact_names": config_matches,
                "config_family_present_casefold": bool(config_matches),
                "model_directory_exact_names": [entry["name"] for entry in exact],
                "model_directory_casefold_names": [entry["name"] for entry in folded],
                "model_file_roles": {
                    role: any(entry.get(file_key, False) for entry in folded)
                    for role, file_key in (("car_dx", "car_dx"), ("complete_dx", "complete_dx"),
                                           ("wheel_dx", "wheel_dx"))
                },
                "evidence_source": "R-PHYS1 filesystem/XML scanner",
            }
        builds[build_name] = per_target
    hit_rows = text_scan.get("text_hits", [])
    frontend_hits = [row for row in hit_rows if row.get("category") == "frontend_car_slot"]
    race_strings = [row for row in ghidra.get("relevant_strings", [])
                    if str(row.get("value", "")).casefold().startswith("race/car")]
    scene_car_types = [row for row in hit_rows
                       if row.get("category") == "scene_race_car_type_assignment"]
    scene_type_summary: dict[str, Any] = {}
    for build_name in BUILD_NAMES:
        build_rows = [row for row in scene_car_types if row.get("build") == build_name]
        families = rphys1.get("builds", {}).get(build_name, {}).get("family_names", [])
        family_folded = {name.casefold(): name for name in families}
        matched_names = Counter(
            family_folded[str(row.get("value", "")).casefold()]
            for row in build_rows if str(row.get("value", "")).casefold() in family_folded
        )
        scene_type_summary[build_name] = {
            "assignment_count": len(build_rows),
            "source_file_count": len({row["path"] for row in build_rows}),
            "literal_value_counts": dict(sorted(Counter(row.get("value") for row in build_rows).items(),
                                                 key=lambda item: str(item[0]).casefold())),
            "values_matching_named_config_families_casefold": dict(sorted(matched_names.items())),
        }
    return {
        "status": "LAYERED_IDENTITIES_WITHOUT_SLOT_EQUIVALENCE",
        "builds": builds,
        "frontend_saved_or_default_selections": {
            "evidence": frontend_hits,
            "interpretation": "UI/save namespace only; no inferred mapping to Race/CarN or Vehicles/CarN",
        },
        "race_participant_namespace": {
            "static_string_evidence": race_strings,
            "scene_car_type_assignments": scene_car_types,
            "scene_car_type_summary": scene_type_summary,
            "interpretation": "Some demo DataScene files assign named strings to Race/CarN/CarType, but no link from those strings to the numeric Vehicles/CarN parameter store is established",
        },
        "runtime_physics_object": {
            "status": "NOT_BOUND_TO_NAMED_FAMILY",
            "interpretation": "No verified named-family-to-Vehicles/CarN population link or ordinary physics-constructor binding yet",
        },
        "user_supplied_context": [dict(row) for row in USER_SUPPLIED_CONTEXT],
    }


def analyze_vehicle_runtime_identity(corpora_root: Path, rphys1_path: Path,
                                     ghidra_xrefs_path: Path | None = None) -> dict[str, Any]:
    rphys1 = json.loads(rphys1_path.read_text(encoding="utf-8"))
    text_scan = scan_corpus_metadata(corpora_root)
    xrefs = json.loads(ghidra_xrefs_path.read_text(encoding="utf-8")) if ghidra_xrefs_path else None
    ghidra = summarize_ghidra_xrefs(xrefs)
    return {
        "schema_version": 1,
        "phase": "R-PHYS2",
        "rphys1_analysis": {"path": str(rphys1_path), "sha256": hashlib.sha256(rphys1_path.read_bytes()).hexdigest()},
        "text_and_metadata_scan": text_scan,
        "ghidra_string_xrefs": ghidra,
        "identity_layers": build_identity_layers(rphys1, text_scan, ghidra),
        "trooper_config_survival": trooper_survival_profile(rphys1),
    }


def render_report(analysis: dict[str, Any]) -> str:
    scan = analysis["text_and_metadata_scan"]
    profile = analysis["trooper_config_survival"]
    status = profile.get("status_counts", {})
    lines = [
        "# R-PHYS2 — Vehicle Param Broker population and physics constructor binding",
        "",
        "## Result and stop state",
        "",
        "The audit narrows the pipeline but does not establish which named `Vehicles/<family>` record is copied into the numeric `Vehicles/CarN` store consumed by the ordinary race physics constructor. The safe stop remains **STATE C**; no runtime mutation is proposed.",
        "",
        "## Corpus search",
        "",
        f"Scanned {scan['text_file_count']} text/config files and {scan['compiled_metadata_file_count']} compiled metadata files in extracted `DataGame` / `DataGx` / `DataScene` trees. Counts below are exact query hits, not inferred bindings.",
        "",
        "| Query category | Hits |",
        "|---|---:|",
    ]
    for category, count in scan["hit_category_counts"].items():
        lines.append(f"| `{category}` | {count} |")
    lines.extend([
        "",
        "The saved `Frontend/QuickRace/Car0/Car1` and `Frontend/Network/Car0` values are UI/save selection fields. They do not establish the source for `Race/CarN` or `Vehicles/CarN`. `CarModelDataFile=RMonster` occurs once per build in the default scene parameter registration; it is not evidence of race physics selection.",
        "",
        f"Demo `DataScene` files contain {sum(row['assignment_count'] for row in analysis['identity_layers']['race_participant_namespace']['scene_car_type_summary'].values())} typed `Race/CarN/CarType` string assignments in {sum(row['source_file_count'] for row in analysis['identity_layers']['race_participant_namespace']['scene_car_type_summary'].values())} files; they occur in 8.4.1 and 9.10.0, with none found in 9.3.1 or retail. Values include `Mercedes`, `Bruno`, `Citroen`, and `Null`, plus spelling/path variants such as `bruno` and `Vehicles/bruno`. Some values case-fold match a named config family in that build, establishing scene-level participant-to-string assignments for those files. They do not prove that retail populates numeric `Vehicles/CarN` from the same string or that the ordinary physics constructor consumes it.",
        "",
        "## Layered identity map",
        "",
        "| Layer | What is observed | Binding status |",
        "|---|---|---|",
        "| Resource folder | Exact/case-folded directory names and `car.dx` / `complete.dx` / `wheel.dx` are inventoried per build. | Scanner facts only; folder presence does not imply playability. |",
        "| Named config family | `vehicles.xml` contains named `Vehicles/<family>` roots; it contains no numeric `Vehicles/CarN` roots in the four audited builds. | Separate identity namespace. |",
        "| Frontend selection | `Frontend/QuickRace/Car0/Car1` and network selection fields occur in retail UI/save XML. | No mapping to runtime vehicle slots established. |",
        "| Race participant | Retail EXE has `Race/Car%d/...` keys including `CarType`, `CarID`, `PlayerType`, and `Transform`; demo scene fixtures put named strings in `CarType`. | Scene-level names are observed for those fixtures; no general retail mapping to the numeric parameter catalog is established. |",
        "| Runtime physics object | Static field readers exist for `Vehicles/Car%d/...`; ordinary contact/constructor path is not linked to a named family. | Unresolved. |",
        "",
        "### Cross-build controls",
        "",
        "`NewRav` (config) and `Rav4` (model directory) remain distinct literal names. Retail `Trooper` has a config family without a same-named retail model folder. Retail `forklift` has model assets without a same-named config family. These are identity-separation controls, not proof of runtime use.",
        "",
        "### User-supplied context (kept separate from scanner facts)",
        "",
        "- The user identifies retail Ufo's missing `wheel.dx` as intentional because it is wheel-less (`USER_SUPPLIED_DESIGN_CONTEXT`). The scanner only confirms the missing file.",
        "- The user identifies `forklift` as a cut/hidden bonus vehicle associated with hidden slot 25 (`USER_SUPPLIED_CUT_HIDDEN_CONTEXT`). The scanner independently confirms model files and no same-named config family.",
        "",
        "## Trooper config survival",
        "",
        f"The 9.10.0→retail Trooper comparison has {profile.get('field_count')} rows: {status.get('EXACT_EQUAL', 0)} exact, {status.get('NUMERIC_EQUAL_TEXT_DIFFERENT', 0)} numeric-equal text changes, and {status.get('VALUE_CHANGED', 0)} value changes.",
        f"Of the {profile.get('trooper_value_changed_path_count', 0)} changed paths, {profile.get('control_shared_path_count', 0)} also change in Jump and/or Navara controls; {len(profile.get('trooper_only_control_paths', []))} do not. This supports a systematic retail retune plus a small set of Trooper-specific deltas in the XML corpus. It does not prove runtime consumption.",
        "",
        "## Retail EXE static trace",
        "",
        "Ghidra review found that `FUN_00493600` builds a numeric `Vehicles/CarN` path; `FUN_004938C0` and `FUN_00493A40` read configuration fields from that path into parameter records. `FUN_0043E4C0` iterates numeric entries and creates records via `FUN_00442D40`. This establishes a numeric vehicle-parameter catalog/constructor path, but not the named-family population source or ordinary physical-contact binding.",
        "",
        "`FUN_004C0B20` (`gaVehicleSplineRecordAI`) reads `Race/Car%d/CarType` and calls the six-field wheel reader at `FUN_004BC590`; its only direct caller is the spline-record route. `FUN_004ABCE0` registers the `Race/CarType` broker key. The static xref/decompilation reviewed here did not identify a writer or named-family mapper for that field. `Frontend/QuickRace/Car0/Car1` accessors are separate UI code.",
        "",
        "`FUN_0048EB40` iterates race-car records by participant index. In the spline-record path, `FUN_004C0B20` passes that same integer to `FUN_004BC590`, which reads `Vehicles/CarN` wheel geometry. This confirms same-index reuse for those spline fields only; it does not prove the numeric entry is populated from `CarType` or used by the ordinary physics constructor.",
        "",
        "The selected functions show `FUN_0043F020` reads a participant `PlayerType`, prepares a numeric vehicle catalog, and attaches four per-wheel helper objects. The reviewed call chain still does not show the catalog index being derived from a named family or prove that these helper objects define physical contact points.",
        "",
        "## Runtime notes and R-PHYS1 cross-build evidence",
        "",
        "Trooper's 9.10.0→retail comparison changes 25 of 147 paths: 16 `DamageParams`, 7 `Engine`, 1 `Chassis`, and 1 `Suspension`; dimensions, steering, and the remaining fields are text/value-equal except one numeric-equal textual change. Jump and Navara controls share the broad damage/engine retune pattern. Earlier operator-supplied reports about Trooper transfer/model/damage and race-wheel placement remain unmeasured project context; they do not bind this EXE path.",
        "",
        "## Runtime test gate",
        "",
        "No runtime configuration mutation is prepared. Before that, establish (1) the writer/source of `Race/CarN/CarType` or the field actually selecting a numeric vehicle record, (2) named-family→numeric-slot mapping, and (3) an ordinary race constructor/read path that consumes the selected physics values. The wheel-spline reader alone is insufficient.",
        "",
        "## Reproducibility",
        "",
        "Run `python tools/scanner/r_phys2.py --corpora-root 'D:\\Game\\Master Rallye\\corpora' --rphys1-analysis .research-output/r-phys1/r-phys1-analysis.json --ghidra-xrefs .research-output/r-phys2/static/retail-vehicle-string-xrefs.json --output-dir .research-output/r-phys2`.",
        "",
        "Full hit offsets, snippets, hashes, indexed xrefs, identity layers, and field deltas are in ignored `r-phys2-analysis.json`. All corpora and EXEs remain read-only.",
        "",
    ])
    return "\n".join(lines)


def write_outputs(analysis: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "r-phys2-analysis.json").write_text(
        json.dumps(analysis, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (output_dir / "r-phys2-vehicle-param-broker.md").write_text(
        render_report(analysis), encoding="utf-8"
    )
