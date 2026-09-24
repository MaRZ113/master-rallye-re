"""Compare a demo GXI, original DXT and optional scratch-regenerated DXT.

Source paths are build-qualified and read-only. Reports contain metadata only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import zlib
from pathlib import Path

from master_rallye.dxt import parse_dxt_bytes
from master_rallye.gxi import encode_gxi_as_observed_dxt, parse_gxi_bytes

FIELDS = ("magic", "version", "crc32", "width", "height")


def file_within(root: Path, relative: Path) -> Path:
    if relative.is_absolute():
        raise ValueError("corpus file must be specified by relative path")
    path = (root / relative).resolve(strict=True)
    if root not in path.parents:
        raise ValueError("corpus file escaped its declared root")
    return path


def dxt_metadata(data: bytes, source: str) -> dict:
    texture = parse_dxt_bytes(data, source)
    return {"size": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "header_hex": texture.header.hex(), "version": texture.word_0x04,
            "crc32": f"0x{texture.word_0x08:08x}",
            "crc_valid": texture.word_0x08 == zlib.crc32(texture.bgra) & 0xFFFFFFFF,
            "dimensions": [texture.width, texture.height],
            "payload_sha256": hashlib.sha256(texture.bgra).hexdigest()}


def pair_comparison(a: bytes, b: bytes) -> dict:
    first = parse_dxt_bytes(a)
    second = parse_dxt_bytes(b)
    a_words = struct.unpack_from("<5I", a)
    b_words = struct.unpack_from("<5I", b)
    return {"full_byte_identical": a == b,
            "pixel_payload_identical": first.bgra == second.bgra,
            "header_identical": first.header == second.header,
            "header_field_differences": [
                {"field": name, "offset": index * 4,
                 "first": f"0x{a_words[index]:08x}",
                 "second": f"0x{b_words[index]:08x}"}
                for index, name in enumerate(FIELDS) if a_words[index] != b_words[index]],
            "different_byte_count": sum(x != y for x, y in zip(a, b)) + abs(len(a) - len(b))}


def compare_pipeline(corpus_id: str, gxi_relative: str, gxi: bytes,
                     original_relative: str, original: bytes,
                     regenerated: bytes | None = None,
                     regenerated_relative: str | None = None) -> dict:
    image = parse_gxi_bytes(gxi, f"{corpus_id}:{gxi_relative}")
    offline = encode_gxi_as_observed_dxt(image)
    original_meta = dxt_metadata(original, f"{corpus_id}:{original_relative}")
    offline_meta = dxt_metadata(offline, "offline GXI reconstruction")
    result = {"corpus_id": corpus_id,
              "gxi": {"corpus_id": corpus_id, "relative_path": gxi_relative,
                      "size": len(gxi), "sha256": hashlib.sha256(gxi).hexdigest(),
                      "dimensions": [image.width, image.height]},
              "original_dxt": {"corpus_id": corpus_id, "relative_path": original_relative,
                               **original_meta},
              "offline_dxt": {"derived_from_corpus_id": corpus_id,
                              "derived_from_relative_path": gxi_relative, **offline_meta},
              "expected_dxt_size": len(offline),
              "comparisons": {"original_vs_offline": pair_comparison(original, offline)},
              "runtime_dxt": None,
              "verdict": "RUNTIME_PENDING"}
    if regenerated is not None:
        runtime_meta = dxt_metadata(regenerated, regenerated_relative or "scratch runtime DXT")
        result["runtime_dxt"] = {"scratch_relative_path": regenerated_relative,
                                 **runtime_meta}
        result["comparisons"]["original_vs_runtime"] = pair_comparison(original, regenerated)
        result["comparisons"]["offline_vs_runtime"] = pair_comparison(offline, regenerated)
        comparisons = result["comparisons"]
        if all(item["full_byte_identical"] for item in comparisons.values()):
            result["verdict"] = "THREE_WAY_BYTE_IDENTICAL"
        elif all(item["pixel_payload_identical"] for item in comparisons.values()):
            result["verdict"] = "PAYLOAD_IDENTICAL_HEADERS_DIFFER"
        else:
            result["verdict"] = "PAYLOAD_DIFFERS"
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus-id", choices=("demo-8.4.1", "demo-9.3.1"), required=True)
    ap.add_argument("--corpus-root", type=Path, required=True)
    ap.add_argument("--gxi", type=Path, required=True, help="path relative to corpus root")
    ap.add_argument("--original-dxt", type=Path, required=True, help="path relative to corpus root")
    ap.add_argument("--scratch-root", type=Path, required=True)
    ap.add_argument("--regenerated-dxt", type=Path, help="existing file under scratch root")
    ap.add_argument("--output", type=Path, required=True, help="JSON file under scratch root")
    args = ap.parse_args()
    corpus = args.corpus_root.resolve(strict=True)
    scratch = args.scratch_root.resolve()
    if corpus == scratch or corpus in scratch.parents or scratch in corpus.parents:
        raise SystemExit("corpus and scratch roots must be disjoint")
    gxi_path = file_within(corpus, args.gxi)
    original_path = file_within(corpus, args.original_dxt)
    output = args.output.resolve()
    if scratch not in output.parents or output.suffix.lower() != ".json":
        raise SystemExit("output must be a JSON file under scratch root")
    regenerated = None
    regenerated_relative = None
    if args.regenerated_dxt:
        runtime_path = args.regenerated_dxt.resolve(strict=True)
        if scratch not in runtime_path.parents or runtime_path == output:
            raise SystemExit("regenerated DXT must be a distinct file under scratch root")
        regenerated = runtime_path.read_bytes()
        regenerated_relative = runtime_path.relative_to(scratch).as_posix()
    report = compare_pipeline(args.corpus_id, args.gxi.as_posix(), gxi_path.read_bytes(),
                              args.original_dxt.as_posix(), original_path.read_bytes(),
                              regenerated, regenerated_relative)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": report["verdict"],
                      "original_sha256": report["original_dxt"]["sha256"],
                      "offline_sha256": report["offline_dxt"]["sha256"],
                      "runtime_sha256": report["runtime_dxt"]["sha256"] if report["runtime_dxt"] else None}))


if __name__ == "__main__":
    main()
