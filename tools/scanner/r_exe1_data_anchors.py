#!/usr/bin/env python3
"""Inventory high-value retail Data.sma names and match them to EXE strings.

Reads the retail Data.sma local-file record table and checks matching members in
the pre-existing extracted view. Ghidra Bridge string exports are optional and
can be supplied later. No archive members are extracted or modified.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import struct
import zlib
from pathlib import Path
from typing import Any, BinaryIO
import xml.etree.ElementTree as ET


BUILD_NAMES = ("8.4.1", "9.3.1", "9.10.0", "retail")
TEXT_SUFFIXES = {".xml", ".txt", ".cfg", ".ini", ".htm", ".html"}
EXT_RE = re.compile(r"\.(?:dx|dxt|dxb|gxm|gxi|gxb|sfl|hnt|xml|txt|wav|mp3|avi|bik|tga|bmp|png|cfg|ini)\b", re.I)
PATH_RE = re.compile(r"(?:Data(?:Game|Gx|Scene)/|Vehicles/|Course/|Race/|Frontend/|Cameras/|Damage/|Modifications/|[A-Za-z0-9_.-]+\.(?:dx|dxt|dxb|gxm|gxi|gxb|sfl|hnt|xml|txt)\b)", re.I)
SEMANTIC_RE = re.compile(r"vehicle|car|course|race|marker|checkpoint|split|spline|wrong|pace|camera|frontend|surface|damage|wheel|physics|audio|music|save|unlock|shader|material|texture|resource|scene|route|input|profile|player|difficulty|weather|particle|replay|editor|cook|cache|selected|entry", re.I)


def local_tag(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def add_value(out: set[str], value: str | None) -> None:
    if not value:
        return
    value = value.strip()
    if len(value) < 3 or len(value) > 240:
        return
    if PATH_RE.search(value) or (SEMANTIC_RE.search(value) and re.fullmatch(r"[A-Za-z0-9_./\\:-]+", value)):
        out.add(value)


def parse_xml_stream(stream: BinaryIO, source: str, tags: collections.Counter, attrs: collections.Counter, values: set[str], parse_errors: list[str]) -> None:
    try:
        for event, element in ET.iterparse(stream, events=("end",)):
            tag = local_tag(str(element.tag))
            tags[tag] += 1
            for key, value in element.attrib.items():
                key = local_tag(str(key))
                attrs[key] += 1
                add_value(values, value)
            add_value(values, element.text)
            element.clear()
    except (ET.ParseError, OSError, ValueError) as exc:
        parse_errors.append(f"{source}: {type(exc).__name__}: {exc}")


def load_bridge_strings(directory: Path | None) -> dict[str, list[dict[str, Any]]]:
    if directory is None:
        return {}
    out: dict[str, list[dict[str, Any]]] = {}
    for build in BUILD_NAMES:
        candidates = [directory / build / "_strings.json", directory / build / "strings.json"]
        source = next((p for p in candidates if p.is_file()), None)
        if not source:
            continue
        payload = json.loads(source.read_text(encoding="utf-8"))
        entries = []
        iterable = payload.values() if isinstance(payload, dict) else payload
        for item in iterable:
            if not isinstance(item, dict):
                continue
            value = str(item.get("value", ""))
            if value:
                entries.append({
                    "address": item.get("address"), "value": value,
                    "references": item.get("references", []),
                })
        out[build] = entries
    return out


def iter_local_records(archive: Path) -> list[dict[str, Any]]:
    """Read sequential ZIP local records, including archives without an EOCD."""
    file_size = archive.stat().st_size
    records = []
    offset = 0
    with archive.open("rb") as stream:
        while offset + 30 <= file_size:
            stream.seek(offset)
            if stream.read(4) != b"PK\x03\x04":
                break
            header = stream.read(26)
            if len(header) != 26:
                raise ValueError(f"Truncated local header at 0x{offset:X}")
            version, flags, compression, mod_time, mod_date, crc, csize, usize, name_len, extra_len = struct.unpack("<HHHHHIIIHH", header)
            name_raw, extra = stream.read(name_len), stream.read(extra_len)
            if len(name_raw) != name_len or len(extra) != extra_len:
                raise ValueError(f"Truncated local name/extra at 0x{offset:X}")
            name = name_raw.decode("utf-8" if flags & 0x800 else "cp437", "replace")
            data_offset = offset + 30 + name_len + extra_len
            if flags & 0x8 or csize == 0xFFFFFFFF or usize == 0xFFFFFFFF:
                raise ValueError(f"Data descriptor or ZIP64 record is not supported: {name} at 0x{offset:X}")
            next_offset = data_offset + csize
            if next_offset > file_size:
                raise ValueError(f"Compressed payload exceeds archive: {name} at 0x{offset:X}")
            records.append({
                "name": name, "header_offset": offset, "data_offset": data_offset,
                "compressed_size": csize, "file_size": usize, "crc32": crc,
                "compression": compression, "flags": flags, "version_needed": version,
            })
            offset = next_offset
    if not records:
        raise ValueError(f"No sequential ZIP local records found: {archive}")
    return records


def crc_and_size(path: Path) -> tuple[int, int]:
    crc, size = 0, 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            crc = zlib.crc32(chunk, crc)
            size += len(chunk)
    return crc & 0xFFFFFFFF, size


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", type=Path, help="Retail Data.sma; defaults to ../corpora/retail/Data.sma")
    ap.add_argument("--unpacked-root", type=Path, help="Existing extracted view; defaults to ../corpora/retail/Data.sma_unpacked")
    ap.add_argument("--string-export-dir", type=Path, help="Bridge output root with <build>/_strings.json")
    ap.add_argument("--output-dir", type=Path, help="Defaults to research/r-exe1")
    ap.add_argument("--max-hits", type=int, default=600)
    args = ap.parse_args()
    repo = Path(__file__).resolve().parents[2]
    archive = (args.archive or (repo.parent / "corpora" / "retail" / "Data.sma")).resolve()
    unpacked_root = (args.unpacked_root or (repo.parent / "corpora" / "retail" / "Data.sma_unpacked")).resolve()
    out_dir = (args.output_dir or (repo / "research" / "r-exe1")).resolve()
    if not archive.is_file():
        raise SystemExit(f"Retail Data.sma not found: {archive}")

    members: list[str] = []
    directory_records: list[str] = []
    dirs = collections.Counter()
    suffixes = collections.Counter()
    tags, attrs = collections.Counter(), collections.Counter()
    values: set[str] = set()
    vehicles: set[str] = set()
    courses: set[str] = set()
    config_files: list[str] = []
    parse_errors: list[str] = []
    extracted_mismatches = []
    validated_text_count = 0
    archive_records = iter_local_records(archive)

    for record in archive_records:
        raw_name = record["name"].replace("\\", "/")
        is_directory = raw_name.endswith("/")
        name = raw_name.strip("/")
        if not name:
            continue
        if is_directory:
            directory_records.append(name)
            continue
        members.append(name)
        parts = name.split("/")
        suffixes[Path(parts[-1]).suffix.lower() or "[none]"] += 1
        for depth, component in enumerate(parts[:-1], 1):
            dirs["/".join(parts[:depth])] += 1
        low = name.lower()
        if low.startswith("datagx/vehicles/") and len(parts) >= 3:
            vehicles.add(parts[2])
        if low.startswith("datagx/course/") and len(parts) >= 3:
            courses.add(parts[2])
        if low.startswith("datascene/racetest/") and len(parts) >= 3 and parts[-1].lower().endswith(".xml"):
            courses.add(Path(parts[-1]).stem)
        if parts[0].lower() in {"datagame", "datascene"} and Path(parts[-1]).suffix.lower() in TEXT_SUFFIXES:
            config_files.append(name)
        if parts[0].lower() not in {"datagame", "datascene"} or Path(parts[-1]).suffix.lower() not in TEXT_SUFFIXES:
            continue
        extracted = unpacked_root.joinpath(*parts)
        if not extracted.is_file():
            extracted_mismatches.append({"member": name, "reason": "missing extracted counterpart"})
            continue
        actual_crc, actual_size = crc_and_size(extracted)
        if actual_crc != record["crc32"] or actual_size != record["file_size"]:
            extracted_mismatches.append({
                "member": name, "reason": "CRC/size mismatch",
                "expected_crc32": f"0x{record['crc32']:08X}", "actual_crc32": f"0x{actual_crc:08X}",
                "expected_size": record["file_size"], "actual_size": actual_size,
            })
            continue
        validated_text_count += 1
        if Path(parts[-1]).suffix.lower() == ".xml":
            with extracted.open("rb") as stream:
                parse_xml_stream(stream, name, tags, attrs, values, parse_errors)
        elif record["file_size"] <= 2_000_000:
            try:
                text = extracted.read_text(encoding="utf-8", errors="replace")
                for match in re.finditer(r"[^\r\n\0]{3,240}", text):
                    add_value(values, match.group())
            except OSError as exc:
                parse_errors.append(f"{name}: {type(exc).__name__}: {exc}")

    last = archive_records[-1]
    local_end = last["data_offset"] + last["compressed_size"]
    with archive.open("rb") as stream:
        stream.seek(local_end)
        trailer = stream.read(4)
    if trailer == b"PK\x01\x02":
        archive_format = "ZIP local-file records followed by central directory; standard EOCD record is absent"
    elif trailer == b"PK\x05\x06":
        archive_format = "ZIP local-file records followed by standard EOCD"
    else:
        archive_format = f"ZIP local-file records; post-record marker at 0x{local_end:X} is {trailer.hex()}"

    bridge_strings = load_bridge_strings(args.string_export_dir)
    anchor_sources: dict[str, set[str]] = collections.defaultdict(set)
    distinct_identifier = re.compile(r"^(?:ga|en|ai|ui)[A-Za-z0-9_]+$|^[A-Z][A-Za-z0-9_]*$")
    def is_distinctive_identifier(token: str) -> bool:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{4,80}", token):
            return False
        if token.casefold() in {"input", "output", "physics", "normal", "value", "type", "name", "true", "false", "null", "default", "enabled", "disabled", "unknown", "none", "front", "back", "left", "right", "start", "finish"}:
            return False
        return bool(distinct_identifier.fullmatch(token) and (token.startswith(("ga", "en", "ai", "ui")) or re.search(r"[A-Z0-9_]", token[1:])))

    for item in sorted(values):
        if PATH_RE.search(item) or EXT_RE.search(item) or is_distinctive_identifier(item):
            anchor_sources[item].add("DataGame/DataScene XML/TXT value")
    for item, _count in tags.items():
        if item.startswith(("ga", "en", "ai", "ui")):
            anchor_sources[item].add("XML component element name")
    for item, _count in attrs.items():
        if is_distinctive_identifier(item):
            anchor_sources[item].add("XML attribute name")
    for item in sorted(config_files):
        anchor_sources[item].add("config filename")
    for item in sorted(vehicles):
        anchor_sources[item].add("vehicle family directory")
        anchor_sources[f"Vehicles/{item}"].add("vehicle family path")
    for item in sorted(courses):
        anchor_sources[item].add("course/RaceTest name")
        anchor_sources[f"Course/{item}"].add("course path")
    for name in members:
        low = name.lower()
        if low.startswith("datagx/") and EXT_RE.search(name):
            rel = name[len("DataGx/"):]
            anchor_sources[rel].add("DataGx resource path")
            if Path(rel).suffix.lower() in {".dx", ".dxt", ".gxm", ".gxi", ".gxb", ".sfl", ".hnt"}:
                anchor_sources[str(Path(rel).with_suffix("")).replace("\\", "/")].add("DataGx resource path without extension")

    candidate_list = []
    seen = set()
    for token, sources in anchor_sources.items():
        normalized = token.strip().strip("/")
        if len(normalized) < 3 or normalized in seen:
            continue
        seen.add(normalized)
        if "/" in normalized or "\\" in normalized or EXT_RE.search(normalized) or is_distinctive_identifier(normalized):
            candidate_list.append((normalized, sorted(sources)))
    candidate_list.sort(key=lambda pair: (-len(pair[0]), pair[0].casefold()))

    hits = []
    for build, entries in bridge_strings.items():
        for entry in entries:
            value = entry["value"]
            low_value = value.casefold()
            matching = []
            for token, sources in candidate_list:
                if "/" in token or "\\" in token or EXT_RE.search(token):
                    matches = token.casefold() in low_value
                else:
                    matches = re.search(rf"(?<![A-Za-z0-9_]){re.escape(token.casefold())}(?![A-Za-z0-9_])", low_value) is not None
                if matches:
                    matching.append({"anchor": token, "sources": sources})
                    if len(matching) >= 12:
                        break
            if matching:
                refs = entry.get("references", [])
                hits.append({
                    "build": build, "address": entry.get("address"), "exe_string": value,
                    "anchors": matching,
                    "functions": sorted({ref.get("func_name", "") for ref in refs if ref.get("func_name")}),
                    "references": refs[:20],
                    "evidence_grade": "CONFIRMED_BY_EXE_XREF" if refs else "CONFIRMED_BY_EXE_STRING_ONLY",
                })
    hits.sort(key=lambda h: (h["build"], h["address"] or ""))
    hits = hits[:args.max_hits]

    payload = {
        "schema_version": 1,
        "archive": {"name": "corpora/retail/Data.sma", "size_bytes": archive.stat().st_size, "local_record_count": len(archive_records), "file_count": len(members), "directory_record_count": len(directory_records), "roots": sorted({n.split("/", 1)[0] for n in members}), "format_observation": archive_format, "unpacked_text_members_crc_validated": validated_text_count, "unpacked_text_mismatches": extracted_mismatches},
        "inventory": {"extensions": dict(sorted(suffixes.items())), "top_directories": dirs.most_common(120), "config_file_count": len(config_files), "xml_element_counts": tags.most_common(), "xml_attribute_counts": attrs.most_common(), "vehicle_families": sorted(vehicles), "course_names": sorted(courses), "semantic_values": sorted(values)[:6000], "parse_errors": parse_errors},
        "bridge_string_builds": {build: len(entries) for build, entries in bridge_strings.items()},
        "exe_anchor_hits": hits,
        "anchor_candidate_count": len(candidate_list),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "data-to-exe-anchors.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = ["# Retail Data.sma semantic anchors into the executables", "", "## Corpus inventory", "", f"Retail `Data.sma` has {len(archive_records):,} sequential local records ({len(members):,} file records and {len(directory_records):,} directory records), roots `{', '.join(payload['archive']['roots'])}`, and {len(config_files):,} human-readable config/text files selected. Format observation: **{archive_format}**. The pre-existing extracted view is used only after CRC and size checks against archive headers ({validated_text_count:,} text/config files verified; mismatches: {len(extracted_mismatches)}). No archive member was extracted or changed by this script.", "", "Vehicle families: " + (", ".join(sorted(vehicles)) or "none found") + ".", "", "Course and RaceTest names: " + (", ".join(sorted(courses)) or "none found") + ".", "", "High-frequency XML element names: " + ", ".join(f"`{name}` ({count})" for name, count in tags.most_common(35)) + ".", "", "High-frequency XML attribute names: " + ", ".join(f"`{name}` ({count})" for name, count in attrs.most_common(35)) + ".", "", "## Executable string matches", "", "Matches use whole data-path fragments or distinctive identifiers, avoiding generic words such as `Input` and `Physics`. `CONFIRMED_BY_EXE_XREF` means a Ghidra xref reaches the string; string-only matches are kept separate. A missing literal does not rule out a dynamically formatted or hashed lookup.", "", "| Grade | Build | String address | Data anchor | Executable string | Referencing functions |", "|---|---|---:|---|---|---|"]
    if hits:
        for hit in hits:
            anchor = "; ".join(a["anchor"] for a in hit["anchors"][:5])
            funcs = ", ".join(hit["functions"][:6]) or "no containing function resolved"
            value = hit["exe_string"].replace("|", "\\|").replace("\n", " ")
            lines.append(f"| {hit['evidence_grade']} | {hit['build']} | `{hit['address']}` | `{anchor}` | `{value}` | {funcs} |")
    else:
        lines.append("| — | — | — | No bridge string exports were supplied or no direct name match was found. | — |")
    lines += ["", "## Interpretation boundaries", "", "- Directory presence proves corpus membership, not runtime loading or gameplay use.", "- A direct xref supports executable reachability from that literal; it does not establish the full consumer semantics without caller/callee and decompilation review.", "- Config element and attribute names are semantic search anchors, not typed runtime field names until code paths corroborate them.", "- Archive, extracted assets, and executable imports remain external and read-only.", ""]
    (out_dir / "data-to-exe-anchors.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Indexed {len(members)} files and {len(directory_records)} directory records, {len(tags)} XML element kinds, {len(candidate_list)} candidate anchors, and {len(hits)} direct EXE string hits.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
