"""Read-only R-DEMO corpus inventory and exact image correspondence audit.

All inputs are explicit external roots. Outputs contain metadata only. This tool
never writes under an input root and rejects overlapping input/output paths.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import struct
import zlib
from pathlib import Path

from master_rallye.errors import MasterRallyeError
from master_rallye.dxt import parse_dxt_bytes
from master_rallye.gxb import parse_gxb_bytes
from master_rallye.gxi import encode_gxi_as_observed_dxt, parse_gxi_bytes
from master_rallye.gx_image import image_to_bgra_bottom_up
from master_rallye.gxp import parse_gxp_bytes

IDS = ("demo-8.4.1", "demo-9.3.1", "retail")
IMAGE_EXTS = {".gxi", ".gxb", ".gxp"}
PAIR_EXTS = {".gxi": ".dxt", ".gxb": ".tga", ".gxp": ".tga", ".gxm": ".dx"}


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def save_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def extension(path: Path) -> str:
    return path.suffix.casefold() or "<none>"


def inventory(corpus_id: str, root: Path) -> dict:
    files = []
    for path in sorted(root.rglob("*"), key=lambda p: p.as_posix().casefold()):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        stat = path.stat()
        with path.open("rb") as stream:
            header = stream.read(16)
        files.append({"corpus_id": corpus_id, "relative_path": relative,
                      "size": stat.st_size, "sha256": digest(path),
                      "extension": extension(path), "header16": header.hex()})
    return {"corpus_id": corpus_id, "file_count": len(files),
            "total_bytes": sum(item["size"] for item in files), "files": files}


def parse_tga_pixels(data: bytes) -> tuple[int, int, bytes, dict]:
    if len(data) < 18:
        raise ValueError("TGA header is truncated")
    id_length, color_map, image_type = struct.unpack_from("<BBB", data)
    width, height, bpp, descriptor = struct.unpack_from("<HHBB", data, 12)
    if color_map != 0 or image_type != 2 or bpp != 32 or not width or not height:
        raise ValueError("not an uncompressed 32-bit truecolor TGA")
    start = 18 + id_length
    end = start + width * height * 4
    if end > len(data):
        raise ValueError("TGA pixel payload is truncated")
    return width, height, data[start:end], {"descriptor": descriptor,
                                              "id_length": id_length,
                                              "trailing_bytes": len(data) - end}


def image_audit(corpus_id: str, root: Path, manifest: dict) -> tuple[dict, list[dict]]:
    by_key = {item["relative_path"].casefold(): item for item in manifest["files"]}
    pairs = []
    parse_status = collections.Counter()
    for item in manifest["files"]:
        ext = item["extension"]
        if ext not in IMAGE_EXTS and ext != ".gxm":
            continue
        src_rel = item["relative_path"]
        target_rel = str(Path(src_rel).with_suffix(PAIR_EXTS[ext])).replace("\\", "/")
        target = by_key.get(target_rel.casefold())
        row = {"corpus_id": corpus_id, "source_relative_path": src_rel,
               "source_extension": ext,
               "target_relative_path": target["relative_path"] if target else None,
               "target_extension": PAIR_EXTS[ext],
               "evidence": "same-folder, same-stem candidate" if target else "missing in same build"}
        if ext in IMAGE_EXTS:
            try:
                raw = (root / src_rel).read_bytes()
                image = {".gxi": parse_gxi_bytes, ".gxb": parse_gxb_bytes, ".gxp": parse_gxp_bytes}[ext](raw, src_rel)
                row.update({"width": image.width, "height": image.height,
                            "exact_container_size": True})
                parse_status[f"{ext}:valid"] += 1
                if target and ext == ".gxi":
                    dxt = parse_dxt_bytes((root / target["relative_path"]).read_bytes(), target_rel)
                    payload = image_to_bgra_bottom_up(image)
                    generated = encode_gxi_as_observed_dxt(image)
                    actual = (root / target["relative_path"]).read_bytes()
                    row.update({"dimensions_match": (image.width, image.height) == (dxt.width, dxt.height),
                                "payload_identical": payload == dxt.bgra,
                                "complete_identical": generated == actual,
                                "crc32_matches_payload": dxt.word_0x08 == zlib.crc32(dxt.bgra) & 0xFFFFFFFF,
                                "dxt_word_0x04": dxt.word_0x04})
                elif target and ext in {".gxb", ".gxp"}:
                    width, height, pixels, tga_info = parse_tga_pixels((root / target["relative_path"]).read_bytes())
                    row.update({"dimensions_match": (image.width, image.height) == (width, height),
                                "payload_identical": image_to_bgra_bottom_up(image) == pixels,
                                "tga": tga_info})
            except (ValueError, OSError, MasterRallyeError) as exc:
                row["error"] = str(exc)
                parse_status[f"{ext}:error"] += 1
        pairs.append(row)
    return dict(sorted(parse_status.items())), pairs


def file_type_report(manifests: dict[str, dict]) -> str:
    retail_counts = collections.Counter(item["extension"] for item in manifests["retail"]["files"])
    lines = ["# R-DEMO file type inventory", "", "Read-only corpus scan. Header signatures are the first eight bytes of each file; they are not format claims.", ""]
    for corpus_id, manifest in manifests.items():
        groups = collections.defaultdict(list)
        by_parent = collections.defaultdict(set)
        for item in manifest["files"]:
            groups[item["extension"]].append(item)
            by_parent[str(Path(item["relative_path"]).parent).casefold()].add(item["extension"])
        lines += [f"## {corpus_id}", "", "| Extension | Count | Retail count | Bytes | Mean/min/max bytes | Main path prefixes | Common sibling extensions | Header 8-byte modes |", "|---|---:|---:|---:|---:|---|---|---|"]
        for ext, files in sorted(groups.items(), key=lambda pair: (-len(pair[1]), pair[0])):
            sizes = [f["size"] for f in files]
            dirs = collections.Counter("/".join(f["relative_path"].split("/")[:2]) for f in files)
            siblings = collections.Counter(s for f in files for s in by_parent[str(Path(f["relative_path"]).parent).casefold()] if s != ext)
            signatures = collections.Counter(f["header16"][:16] for f in files)
            brief = lambda counter: ", ".join(f"{key} ({count})" for key, count in counter.most_common(3)) or "—"
            lines.append(f"| `{ext}` | {len(files)} | {retail_counts[ext]} | {sum(sizes)} | {sum(sizes)//len(sizes)}/{min(sizes)}/{max(sizes)} | {brief(dirs)} | {brief(siblings)} | `{brief(signatures)}` |")
        lines += ["", f"Total: {manifest['file_count']} files, {manifest['total_bytes']} bytes, {len(groups)} unique extensions.", ""]
    return "\n".join(lines)


def summary_md(manifest: dict, parse_status: dict) -> str:
    counts = collections.Counter(f["extension"] for f in manifest["files"])
    return "\n".join([f"# {manifest['corpus_id']} manifest", "",
        f"- Files: {manifest['file_count']}", f"- Bytes: {manifest['total_bytes']}",
        f"- Unique extensions: {len(counts)}", "- Extension counts: " + ", ".join(f"`{ext}` {count}" for ext, count in counts.most_common()),
        "- Image structure scan: " + (", ".join(f"{key} {count}" for key, count in parse_status.items()) or "no GXI/GXB files"),
        "", "Every manifest entry retains corpus_id and relative_path. No game file is copied into Git.", ""])


def evolution(left: dict, right: dict) -> dict:
    a = {f["relative_path"].casefold(): f for f in left["files"]}
    b = {f["relative_path"].casefold(): f for f in right["files"]}
    shared = a.keys() & b.keys()
    identical = sorted(k for k in shared if a[k]["sha256"] == b[k]["sha256"])
    changed = sorted(k for k in shared if a[k]["sha256"] != b[k]["sha256"])
    removed = sorted(a.keys() - b.keys())
    added = sorted(b.keys() - a.keys())
    old_by_hash = collections.defaultdict(list)
    for key in removed:
        old_by_hash[a[key]["sha256"]].append(key)
    new_by_hash = collections.defaultdict(list)
    for key in added:
        new_by_hash[b[key]["sha256"]].append(key)
    rename_candidates = [{"from_corpus_id": left["corpus_id"], "from_relative_path": a[key]["relative_path"],
                          "to_corpus_id": right["corpus_id"], "to_relative_path": b[candidates[0]]["relative_path"],
                          "sha256": a[key]["sha256"]}
                         for key in removed if len(old_by_hash[a[key]["sha256"]]) == 1 and len(candidates := new_by_hash[a[key]["sha256"]]) == 1]
    return {"from_corpus_id": left["corpus_id"], "to_corpus_id": right["corpus_id"],
            "identical": [{"from_relative_path": a[k]["relative_path"], "to_relative_path": b[k]["relative_path"]} for k in identical],
            "changed": [{"from_relative_path": a[k]["relative_path"], "to_relative_path": b[k]["relative_path"]} for k in changed],
            "removed": [a[k]["relative_path"] for k in removed],
            "added": [b[k]["relative_path"] for k in added],
            "rename_candidates": rename_candidates}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    for name in IDS:
        ap.add_argument("--" + name, type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    roots = {name: getattr(args, name.replace("-", "_" )).resolve() for name in IDS}
    output = args.output.resolve()
    if any(not root.is_dir() for root in roots.values()):
        raise SystemExit("all three corpus roots must be existing directories")
    for root in roots.values():
        if root == output or root in output.parents or output in root.parents:
            raise SystemExit("output must not overlap any corpus root")
    manifests = {}
    pairs = []
    for corpus_id, root in roots.items():
        manifest = inventory(corpus_id, root)
        manifests[corpus_id] = manifest
        status, found_pairs = image_audit(corpus_id, root, manifest)
        pairs.extend(found_pairs)
        stem = corpus_id.replace("demo-", "corpus-").replace(".", "_") if corpus_id != "retail" else "corpus-retail"
        save_json(output / f"{stem}.json", manifest)
        (output / f"{stem}.md").write_text(summary_md(manifest, status), encoding="utf-8")
        print(corpus_id, manifest["file_count"], manifest["total_bytes"], status, flush=True)
    (output / "file-types.md").write_text(file_type_report(manifests), encoding="utf-8")
    save_json(output / "resource-pairs.json", {"pairs": pairs})
    evo = evolution(manifests["demo-8.4.1"], manifests["demo-9.3.1"])
    save_json(output / "demo-evolution.json", evo)
    print("pairs", len(pairs), "evolution", {key: len(value) for key, value in evo.items() if isinstance(value, list)}, flush=True)


if __name__ == "__main__":
    main()
