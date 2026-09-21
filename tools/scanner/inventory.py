#!/usr/bin/env python3
"""Build a read-only forensic inventory of an extracted Master Rallye Data.sma."""
from __future__ import annotations
import argparse, hashlib, json, math, re, statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

EXPECTED_ROOTS = {"DataGame", "DataGx", "DataScene"}

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def signature_label(head: bytes) -> str:
    known = ((b"<?xml", "xml-declaration"), (b"<", "text-angle-bracket"),
             (b"DDS ", "dds"), (b"BM", "bmp"), (b"\x89PNG\r\n\x1a\n", "png"),
             (b"RIFF", "riff"), (b"PK\x03\x04", "zip"))
    for magic, label in known:
        if head.startswith(magic): return label
    if not head: return "empty"
    printable = sum(byte in b"\t\n\r" or 32 <= byte < 127 for byte in head)
    return "mostly-ascii" if printable / len(head) >= 0.9 else "binary-unrecognized"

def resource_family(relative: Path) -> str:
    parts = relative.parts
    if not parts: return "unknown"
    if parts[0] == "DataGame": return "game-configuration"
    if parts[0] == "DataScene": return f"scene/{parts[1]}" if len(parts) > 1 else "scene-configuration"
    if parts[0] == "DataGx":
        if len(parts) >= 3 and parts[1] == "Vehicles": return f"vehicle/{parts[2]}"
        return f"graphics/{parts[1]}" if len(parts) >= 2 else "graphics"
    return parts[0]

def size_bucket(size: int) -> str:
    if size == 0: return "0"
    lower = 1 << int(math.log2(size))
    return f"{lower}-{(lower << 1) - 1}"

def filename_pattern(path: Path) -> str:
    stem, ext = path.stem.lower(), path.suffix.lower() or "[none]"
    if stem in {"car", "complete", "wheel"}: return f"semantic-{stem}{ext}"
    if re.search(r"(?:^|[-_])(tga|bmp)$", stem): return f"export-suffixed{ext}"
    if re.search(r"\d+$", stem): return f"numeric-suffix{ext}"
    return f"other{ext}"

def summarize_sizes(values: list[int]) -> dict:
    if not values: return {"count": 0, "bytes": 0, "min": 0, "max": 0, "median": 0}
    return {"count": len(values), "bytes": sum(values), "min": min(values),
            "max": max(values), "median": statistics.median(values)}

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--inventory", required=True, type=Path)
    parser.add_argument("--relationships", required=True, type=Path)
    args = parser.parse_args()
    source = args.source.resolve()
    present_roots = {p.name for p in source.iterdir() if p.is_dir()}
    missing = sorted(EXPECTED_ROOTS - present_roots)
    if missing: raise SystemExit(f"not an extracted Data.sma root; missing: {missing}")
    inventory_target, relationships_target = args.inventory.resolve(), args.relationships.resolve()
    for target in (inventory_target, relationships_target):
        if source == target or source in target.parents: raise SystemExit("refusing to write output below --source")
        target.parent.mkdir(parents=True, exist_ok=True)

    paths = sorted((p for p in source.rglob("*") if p.is_file()), key=lambda p: p.as_posix().lower())
    sibling_groups = defaultdict(list)
    for path in paths: sibling_groups[(path.parent, path.stem.lower())].append(path)
    records, extension_sizes, directory_sizes = [], defaultdict(list), defaultdict(list)
    magic_counts, pattern_counts, bucket_counts = Counter(), Counter(), Counter()
    hash_groups = defaultdict(list)
    for path in paths:
        rel, stat = path.relative_to(source), path.stat()
        with path.open("rb") as stream: head = stream.read(64)
        extension, magic, digest = path.suffix.lower() or "[none]", signature_label(head), sha256_file(path)
        records.append({"path": rel.as_posix(), "extension": extension, "size": stat.st_size,
                        "first_64_hex": head.hex(" "), "signature": magic, "stem": path.stem,
                        "matching_stem_neighbors": [p.relative_to(source).as_posix() for p in sibling_groups[(path.parent, path.stem.lower())] if p != path],
                        "resource_family": resource_family(rel), "sha256": digest})
        extension_sizes[extension].append(stat.st_size); directory_sizes[rel.parent.as_posix()].append(stat.st_size)
        magic_counts[magic] += 1; pattern_counts[filename_pattern(path)] += 1; bucket_counts[size_bucket(stat.st_size)] += 1
        hash_groups[digest].append(rel.as_posix())

    cross_extension_groups = []
    for (parent, stem), group in sorted(sibling_groups.items(), key=lambda item: str(item[0]).lower()):
        if len({path.suffix.lower() for path in group}) > 1:
            cross_extension_groups.append({"directory": parent.relative_to(source).as_posix(), "stem": stem,
                                           "files": [p.relative_to(source).as_posix() for p in sorted(group)]})
    vehicle_profiles = []
    vehicles_root = source / "DataGx" / "Vehicles"
    for directory in sorted((p for p in vehicles_root.iterdir() if p.is_dir()), key=lambda p: p.name.lower()):
        files = [p for p in directory.iterdir() if p.is_file()]; names = {p.name.lower() for p in files}
        extensions = Counter((p.suffix.lower() or "[none]") for p in files)
        semantic = {stem: {"dx": f"{stem}.dx" in names, "txt": f"{stem}.txt" in names} for stem in ("car", "complete", "wheel")}
        vehicle_profiles.append({"vehicle": directory.name, "file_count": len(files), "bytes": sum(p.stat().st_size for p in files),
                                 "extensions": dict(sorted(extensions.items())), "semantic_layout": semantic,
                                 "dxt_stems": sorted(p.stem for p in files if p.suffix.lower() == ".dxt")})
    duplicates = [{"sha256": digest, "files": group} for digest, group in sorted(hash_groups.items()) if len(group) > 1]
    created = datetime.now(timezone.utc).isoformat()
    inventory = {"schema_version": 1, "generated_utc": created,
                 "source_descriptor": "external extracted Data.sma root (path intentionally omitted)",
                 "file_count": len(records), "total_bytes": sum(r["size"] for r in records),
                 "aggregates": {"extensions": {k: summarize_sizes(v) for k, v in sorted(extension_sizes.items())},
                                "directories": {k: summarize_sizes(v) for k, v in sorted(directory_sizes.items())},
                                "filename_patterns": dict(sorted(pattern_counts.items())), "signatures": dict(sorted(magic_counts.items())),
                                "size_ranges": dict(sorted(bucket_counts.items(), key=lambda item: int(item[0].split("-")[0])))},
                 "files": records}
    relationships = {"schema_version": 1, "generated_utc": created, "cross_extension_same_stem": cross_extension_groups,
                     "vehicle_profiles": vehicle_profiles, "byte_identical_groups": duplicates}
    inventory_target.write_text(json.dumps(inventory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    relationships_target.write_text(json.dumps(relationships, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"indexed {len(records)} files / {inventory['total_bytes']} bytes")
    print(f"cross-extension stem groups: {len(cross_extension_groups)}")
    print(f"duplicate hash groups: {len(duplicates)}")
    return 0

if __name__ == "__main__": raise SystemExit(main())
