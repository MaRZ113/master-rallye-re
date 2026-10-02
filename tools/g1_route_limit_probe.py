#!/usr/bin/env python3
"""Prepare two fixed, source-hash-guarded France1 XML research probes.

This is not the Course SDK writer. The only writable paths are the two
predeclared RaceLine and LeftInnerLimit Marker Pos probe recipes below.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import xml.parsers.expat as expat
from collections import Counter
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]
RETAIL_EXE_SHA256 = "BF8AEF32407EB6552C05045B8ABEF149F32983CEDD9503B865069B444C5F96B4"
FRANCE1_RETAIL_XML_SHA256 = "BEAA2180912FFD54F313A149962E295F9894239014481D2C7BA2DB84FB1E08E1"
RUNTIME_EXE = "corpora/retail/MRallye.exe"

# Zero-based Marker ordinals within the exact, unique named MarkerList.
PROBES = {
    "raceline": {
        "marker_list": "RaceLine",
        "indices": (265, 266, 267, 268),
        "delta": (-36.239355, 0.0, 16.932487),
        "selection": "four consecutive points on a low-turn France1 section, away from StartArea, FinishArea and the three SplitTime centers",
        "question": "Does changing the ordered RaceLine sample path alter runtime LastMarker/Progress/Rank tracking while physical road geometry is unchanged?",
    },
    "limit": {
        "marker_list": "LeftInnerLimit",
        "indices": (98, 99, 100),
        "delta": (-5.855248, 0.0, 19.123705),
        "selection": "three consecutive points near RaceLine progress 0.60, translated horizontally toward the route by a shared 20-unit vector",
        "question": "Does this exact list's selected inner-limit position data change LimitState classification at the old/new boundary while the other three lists remain unchanged?",
    },
}


class ProbeError(ValueError):
    """A source, identity, or output-safety check refused the operation."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _markup_end(data: bytes, start: int) -> int:
    quote = 0
    for index in range(start, len(data)):
        byte = data[index]
        if quote:
            if byte == quote:
                quote = 0
        elif byte in (ord("'"), ord('"')):
            quote = byte
        elif byte == ord(">"):
            return index + 1
    raise ProbeError(f"unterminated XML start tag at byte 0x{start:X}")


def _attribute_value_span(data: bytes, tag_start: int, attribute: bytes) -> tuple[int, int, bytes]:
    tag_end = _markup_end(data, tag_start)
    token = data[tag_start:tag_end]
    pattern = re.compile(rb"(?<![A-Za-z0-9_:-])" + re.escape(attribute) + rb"\s*=\s*([\"'])(.*?)\1", re.DOTALL)
    matches = list(pattern.finditer(token))
    if len(matches) != 1:
        raise ProbeError(f"expected exactly one {attribute.decode('ascii')} attribute at byte 0x{tag_start:X}")
    match = matches[0]
    return tag_start + match.start(2), tag_start + match.end(2), match.group(2)


def _marker_pos_spans(data: bytes, marker_list_name: str, marker_index: int):
    """Find one Marker Pos Value attribute by literal list and source ordinal."""
    parser = expat.ParserCreate()
    stack: list[dict] = []
    list_occurrences: Counter[str] = Counter()
    found: list[dict] = []

    def start_element(tag: str, attrs: dict[str, str]) -> None:
        parent = stack[-1] if stack else None
        if tag == "List" and parent is not None and parent["tag"] == "MarkerLists":
            frame = {
                "tag": tag,
                "name": attrs.get("Name"),
                "occurrence": list_occurrences[attrs.get("Name", "")],
                "next_marker_index": 0,
            }
            list_occurrences[attrs.get("Name", "")] += 1
        elif tag == "Marker":
            list_frame = next((item for item in reversed(stack) if item["tag"] == "List"), None)
            if list_frame is None:
                frame = {"tag": tag}
            else:
                frame = {
                    "tag": tag,
                    "list_name": list_frame.get("name"),
                    "list_occurrence": list_frame["occurrence"],
                    "index": list_frame["next_marker_index"],
                }
                list_frame["next_marker_index"] += 1
        else:
            frame = {"tag": tag}

        if tag == "Value" and attrs.get("Name") == "Marker Pos":
            marker_frame = next((item for item in reversed(stack) if item["tag"] == "Marker"), None)
            if (marker_frame is not None
                    and marker_frame.get("list_name") == marker_list_name
                    and marker_frame.get("index") == marker_index):
                value_start = parser.CurrentByteIndex
                value_begin, value_end, raw_value = _attribute_value_span(data, value_start, b"Value")
                found.append({
                    "start": value_begin,
                    "end": value_end,
                    "raw": raw_value,
                    "list_occurrence": marker_frame["list_occurrence"],
                    "index": marker_index,
                })
        stack.append(frame)

    def end_element(_tag: str) -> None:
        if not stack:
            raise ProbeError("unexpected XML end tag while resolving Marker Pos")
        stack.pop()

    parser.StartElementHandler = start_element
    parser.EndElementHandler = end_element
    try:
        parser.Parse(data, True)
    except expat.ExpatError as error:
        raise ProbeError(f"malformed XML: {error}") from error

    if list_occurrences[marker_list_name] != 1:
        raise ProbeError(
            f"expected one MarkerLists List named {marker_list_name!r}; found {list_occurrences[marker_list_name]}"
        )
    if len(found) != 1 or found[0]["list_occurrence"] != 0:
        raise ProbeError(
            f"expected one Marker Pos for {marker_list_name}[{marker_index}], found {len(found)}"
        )
    return found[0]


def _parse_vector(raw: bytes) -> tuple[float, float, float]:
    try:
        fields = raw.decode("ascii").replace(",", " ").split()
        if len(fields) != 3:
            raise ValueError("expected 3 components")
        result = tuple(float(item) for item in fields)
    except (UnicodeDecodeError, ValueError) as error:
        raise ProbeError(f"invalid Marker Pos Vector3 {raw!r}") from error
    if not all(math.isfinite(item) for item in result):
        raise ProbeError(f"non-finite Marker Pos Vector3 {raw!r}")
    return result  # type: ignore[return-value]


def _make_expected(source: bytes, probe_name: str, *, expected_sha256: str):
    if probe_name not in PROBES:
        raise ProbeError(f"unsupported probe kind {probe_name!r}")
    actual_hash = sha256(source)
    if actual_hash != expected_sha256.upper():
        raise ProbeError(f"France1 source SHA256 mismatch: expected {expected_sha256}, got {actual_hash}")
    spec = PROBES[probe_name]
    patches = []
    edits = []
    dx, dy, dz = spec["delta"]
    for marker_index in spec["indices"]:
        span = _marker_pos_spans(source, spec["marker_list"], marker_index)
        old = _parse_vector(span["raw"])
        new = (old[0] + dx, old[1] + dy, old[2] + dz)
        new_raw = (f"{new[0]:.6f} {new[1]:.6f} {new[2]:.6f}").encode("ascii")
        patches.append((span["start"], span["end"], new_raw))
        edits.append({
            "marker_index": marker_index,
            "old_raw": span["raw"].decode("ascii"),
            "old_xyz": list(old),
            "new_raw": new_raw.decode("ascii"),
            "new_xyz": [float(item) for item in new_raw.decode("ascii").split()],
            "byte_range": [span["start"], span["end"]],
        })
    output = source
    for start, end, replacement in sorted(patches, reverse=True):
        output = output[:start] + replacement + output[end:]
    return output, edits


def _manifest(probe_name: str, source_path: Path, output_path: Path, edits: list[dict]) -> dict:
    spec = PROBES[probe_name]
    return {
        "schema": "master-rallye-g1-fixed-marker-probe-v1",
        "evidence": "PREPARED_FOR_HUMAN_RUNTIME_TEST; no runtime result asserted",
        "probe": probe_name,
        "course": "France1",
        "source_xml": str(source_path),
        "source_xml_sha256": FRANCE1_RETAIL_XML_SHA256,
        "edited_xml": str(output_path),
        "edited_xml_sha256": "computed-on-write",
        "expected_runtime_executable": RUNTIME_EXE,
        "expected_runtime_executable_sha256": RETAIL_EXE_SHA256,
        "marker_list": spec["marker_list"],
        "field": "Marker Pos / Value Vector3",
        "edited_components": ["X", "Z"],
        "unchanged_components": ["Y"],
        "shared_delta_xyz": list(spec["delta"]),
        "marker_indices_zero_based": list(spec["indices"]),
        "edits": edits,
        "selection_basis": spec["selection"],
        "question": spec["question"],
        "write_scope": "Only predeclared Marker Pos Value attributes in the named list; every other source byte is preserved.",
    }


def _assert_output_path(path: Path, source: Path) -> None:
    if path.resolve() == source.resolve():
        raise ProbeError("probe output must be a new file, not the source XML")
    lowered = str(path.resolve()).replace("/", "\\").casefold()
    if "\\research-output\\g1\\probes\\" not in lowered:
        raise ProbeError("probe output must be inside research-output\\g1\\probes")


def _prepare(probe_name: str, source_path: Path, output_path: Path) -> Path:
    source_path = source_path.resolve()
    output_path = output_path.resolve()
    _assert_output_path(output_path, source_path)
    source = source_path.read_bytes()
    output, edits = _make_expected(source, probe_name, expected_sha256=FRANCE1_RETAIL_XML_SHA256)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(output)
    manifest = _manifest(probe_name, source_path, output_path, edits)
    manifest["edited_xml_sha256"] = sha256(output)
    manifest_path = output_path.with_suffix(output_path.suffix + ".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"prepared {probe_name}: {output_path}")
    print(f"source_sha256={FRANCE1_RETAIL_XML_SHA256}")
    print(f"edited_sha256={manifest['edited_xml_sha256']}")
    print(f"manifest={manifest_path}")
    return output_path


def _verify(probe_name: str, source_path: Path, edited_path: Path) -> dict:
    source_path = source_path.resolve()
    edited_path = edited_path.resolve()
    source = source_path.read_bytes()
    expected, edits = _make_expected(source, probe_name, expected_sha256=FRANCE1_RETAIL_XML_SHA256)
    actual = edited_path.read_bytes()
    if actual != expected:
        raise ProbeError("edited XML does not equal the exact predeclared probe transformation")
    manifest_path = edited_path.with_suffix(edited_path.suffix + ".manifest.json")
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("probe") != probe_name or manifest.get("source_xml_sha256") != FRANCE1_RETAIL_XML_SHA256:
            raise ProbeError("probe manifest identity/hash does not match this verification")
        if manifest.get("edited_xml_sha256") != sha256(actual):
            raise ProbeError("probe manifest edited XML hash mismatch")
    else:
        manifest = _manifest(probe_name, source_path, edited_path, edits)
    print(f"verified {probe_name}: {edited_path}")
    print(f"source_sha256={FRANCE1_RETAIL_XML_SHA256}")
    print(f"edited_sha256={sha256(actual)}")
    print("byte_scope=exactly the predeclared Marker Pos fields")
    return manifest


def _inspect(source_path: Path) -> dict:
    source_path = source_path.resolve()
    payload = source_path.read_bytes()
    actual_hash = sha256(payload)
    if actual_hash != FRANCE1_RETAIL_XML_SHA256:
        raise ProbeError(f"France1 source SHA256 mismatch: expected {FRANCE1_RETAIL_XML_SHA256}, got {actual_hash}")
    report = {"source_xml": str(source_path), "source_xml_sha256": actual_hash, "probes": {}}
    for name, spec in PROBES.items():
        rows = []
        for marker_index in spec["indices"]:
            span = _marker_pos_spans(payload, spec["marker_list"], marker_index)
            rows.append({"marker_index": marker_index, "raw": span["raw"].decode("ascii"), "xyz": list(_parse_vector(span["raw"]))})
        report["probes"][name] = {
            "marker_list": spec["marker_list"],
            "indices_zero_based": list(spec["indices"]),
            "delta_xyz": list(spec["delta"]),
            "markers": rows,
            "selection_basis": spec["selection"],
            "question": spec["question"],
        }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect", help="show the fixed France1 probe targets")
    inspect.add_argument("--source", required=True, type=Path)
    for name in PROBES:
        prepare = commands.add_parser(f"prepare-{name}", help=f"prepare the fixed {name} XML probe")
        prepare.add_argument("--source", required=True, type=Path)
        prepare.add_argument("--output", required=True, type=Path)
    verify = commands.add_parser("verify", help="verify a probe XML against the fixed source and recipe")
    verify.add_argument("--kind", required=True, choices=tuple(PROBES))
    verify.add_argument("--source", required=True, type=Path)
    verify.add_argument("--edited", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "inspect":
            _inspect(args.source)
        elif args.command.startswith("prepare-"):
            _prepare(args.command.removeprefix("prepare-"), args.source, args.output)
        else:
            _verify(args.kind, args.source, args.edited)
    except (OSError, ProbeError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
