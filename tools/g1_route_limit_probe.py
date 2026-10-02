#!/usr/bin/env python3
"""Prepare fixed, source-hash-guarded France1 XML research probes.

This is not the Course SDK writer. Writable paths are limited to the
predeclared RaceLine and limit Marker Pos probe recipes below.
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
RUNTIME_EXE = REPOSITORY.parent / "MRallye.exe"
DEFAULT_OUTPUT_ROOT = REPOSITORY.parent / "research-output"

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
    "outerlimit": {
        "marker_list": "LeftOuterLimit",
        "indices": (58, 59, 60),
        "delta": (-33.453008, 0.0, -21.929346),
        "selection": "three consecutive France1 LeftOuterLimit points at RaceLine sample progress 0.559-0.562; a shared 40-unit X/Z translation moves them toward the nearby drivable RaceLine from 32.8-47.5 units away to approximately 4.2-12.3 units away",
        "question": "At the same physical road section, does moving only LeftOuterLimit inward cause gaLimitsAI to change LimitState or its outside-outer classification?",
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


def _verify_runtime_executable() -> str:
    if not RUNTIME_EXE.is_file():
        raise ProbeError(f"Retail runtime executable is missing: {RUNTIME_EXE}")
    digest = sha256(RUNTIME_EXE.read_bytes())
    if digest != RETAIL_EXE_SHA256:
        raise ProbeError(f"Retail runtime executable SHA256 mismatch: expected {RETAIL_EXE_SHA256}, got {digest}")
    return digest


def _manifest(
    probe_name: str,
    source_path: Path,
    output_path: Path,
    edits: list[dict],
    output_root: Path,
    runtime_exe_sha256: str,
) -> dict:
    spec = PROBES[probe_name]
    return {
        "schema": "master-rallye-g1-fixed-marker-probe-v2",
        "evidence": "PREPARED_FOR_HUMAN_RUNTIME_TEST; no runtime result asserted",
        "probe": probe_name,
        "course": "France1",
        "research_output_root": str(output_root.resolve()),
        "source_xml": str(source_path),
        "source_xml_sha256": FRANCE1_RETAIL_XML_SHA256,
        "edited_xml": str(output_path),
        "edited_xml_sha256": "computed-on-write",
        "expected_runtime_executable": str(RUNTIME_EXE.resolve()),
        "expected_runtime_executable_sha256": runtime_exe_sha256,
        "marker_list": spec["marker_list"],
        "field": "Marker Pos / Value Vector3",
        "edited_components": ["X", "Z"],
        "unchanged_components": ["Y"],
        "shared_delta_xyz": list(spec["delta"]),
        "marker_indices_zero_based": list(spec["indices"]),
        "edits": edits,
        "unrelated_semantic_changes": [],
        "unrelated_source_bytes_changed": False,
        "selection_basis": spec["selection"],
        "question": spec["question"],
        "write_scope": "Only predeclared Marker Pos Value attributes in the named list; every other source byte is preserved.",
    }


def _infer_output_root(path: Path) -> Path:
    path = path.resolve()
    if path.parent.name.casefold() != "probes" or path.parent.parent.name.casefold() != "g1":
        raise ProbeError("probe XML must be inside <output-root>/g1/probes")
    return path.parent.parent.parent.resolve()


def resolve_output_paths(
    probe_name: str,
    *,
    output: Path | None = None,
    output_root: Path | None = None,
) -> tuple[Path, Path, Path]:
    """Resolve explicit/default output root and candidate/manifest paths."""
    if probe_name not in PROBES:
        raise ProbeError(f"unsupported probe kind {probe_name!r}")
    if output is not None and output_root is not None:
        raise ProbeError("choose either --output or --output-root, not both")
    indices = PROBES[probe_name]["indices"]
    start, end = indices[0], indices[-1]
    filename = f"France1_{probe_name}_{start}-{end}.xml"
    if output_root is not None:
        root = output_root.expanduser().resolve()
        candidate = root / "g1" / "probes" / filename
    elif output is not None:
        candidate = output.expanduser().resolve()
        root = _infer_output_root(candidate)
    else:
        root = DEFAULT_OUTPUT_ROOT.expanduser().resolve()
        candidate = root / "g1" / "probes" / filename
    manifest = candidate.with_suffix(candidate.suffix + ".manifest.json")
    return root, candidate.resolve(), manifest.resolve()


def _assert_output_path(path: Path, source: Path, output_root: Path) -> None:
    if path.resolve() == source.resolve():
        raise ProbeError("probe output must be a new file, not the source XML")
    expected_parent = (output_root.resolve() / "g1" / "probes").resolve()
    if path.resolve().parent != expected_parent:
        raise ProbeError(f"probe output must be inside {expected_parent}")


def _baseline_manifest(source_path: Path, output_root: Path, runtime_exe_sha256: str) -> dict:
    return {
        "schema": "master-rallye-g1-baseline-reference-v1",
        "evidence": "CONFIRMED_BY_HASH; unedited France1 RaceTest baseline",
        "course": "France1",
        "build": "Retail",
        "source_xml": str(source_path.resolve()),
        "source_xml_sha256": FRANCE1_RETAIL_XML_SHA256,
        "runtime_executable": str(RUNTIME_EXE.resolve()),
        "runtime_executable_sha256": runtime_exe_sha256,
        "research_output_root": str(output_root.resolve()),
        "mutation": "none; baseline reference only",
    }


def _print_output_locations(output_root: Path, probe_xml: Path, manifest_path: Path) -> None:
    print(f"Research output root: {output_root.resolve()}")
    print(f"Probe XML: {probe_xml.resolve()}")
    print(f"Manifest: {manifest_path.resolve()}")


def _prepare(
    probe_name: str,
    source_path: Path,
    *,
    output_path: Path | None = None,
    output_root: Path | None = None,
) -> Path:
    source_path = source_path.resolve()
    runtime_hash = _verify_runtime_executable()
    resolved_root, output_path, manifest_path = resolve_output_paths(
        probe_name, output=output_path, output_root=output_root
    )
    _assert_output_path(output_path, source_path, resolved_root)
    source = source_path.read_bytes()
    output, edits = _make_expected(source, probe_name, expected_sha256=FRANCE1_RETAIL_XML_SHA256)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(output)
    manifest = _manifest(probe_name, source_path, output_path, edits, resolved_root, runtime_hash)
    manifest["edited_xml_sha256"] = sha256(output)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    baseline_path = output_path.parent / "France1_retail_baseline.manifest.json"
    baseline_path.write_text(
        json.dumps(_baseline_manifest(source_path, resolved_root, runtime_hash), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"prepared {probe_name}")
    _print_output_locations(resolved_root, output_path, manifest_path)
    print(f"Baseline reference manifest: {baseline_path.resolve()}")
    print(f"Source SHA256: {FRANCE1_RETAIL_XML_SHA256}")
    print(f"Candidate SHA256: {manifest['edited_xml_sha256']}")
    return output_path


def _verify(
    probe_name: str,
    source_path: Path,
    edited_path: Path,
    *,
    output_root: Path | None = None,
) -> dict:
    source_path = source_path.resolve()
    edited_path = edited_path.resolve()
    inferred_root = _infer_output_root(edited_path)
    resolved_root = output_root.expanduser().resolve() if output_root is not None else inferred_root
    _assert_output_path(edited_path, source_path, resolved_root)
    source = source_path.read_bytes()
    expected, edits = _make_expected(source, probe_name, expected_sha256=FRANCE1_RETAIL_XML_SHA256)
    actual = edited_path.read_bytes()
    if actual != expected:
        raise ProbeError("edited XML does not equal the exact predeclared probe transformation")
    manifest_path = edited_path.with_suffix(edited_path.suffix + ".manifest.json")
    if not manifest_path.is_file():
        raise ProbeError(f"probe manifest is required: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("probe") != probe_name or manifest.get("source_xml_sha256") != FRANCE1_RETAIL_XML_SHA256:
        raise ProbeError("probe manifest identity/hash does not match this verification")
    if manifest.get("edited_xml_sha256") != sha256(actual):
        raise ProbeError("probe manifest edited XML hash mismatch")
    if manifest.get("marker_list") != PROBES[probe_name]["marker_list"]:
        raise ProbeError("probe manifest MarkerList does not match this verification")
    if manifest.get("marker_indices_zero_based") != list(PROBES[probe_name]["indices"]):
        raise ProbeError("probe manifest marker indices do not match this verification")
    if Path(manifest.get("source_xml", "")).resolve() != source_path:
        raise ProbeError("probe manifest source path does not match this verification")
    if Path(manifest.get("edited_xml", "")).resolve() != edited_path:
        raise ProbeError("probe manifest candidate path does not match this verification")
    if manifest.get("edits") != edits:
        raise ProbeError("probe manifest field edits do not match the exact probe transformation")
    if manifest.get("unrelated_semantic_changes") not in (None, []):
        raise ProbeError("probe manifest reports unrelated semantic changes")
    if manifest.get("unrelated_source_bytes_changed") not in (None, False):
        raise ProbeError("probe manifest reports unrelated source bytes changed")
    if probe_name == "outerlimit":
        baseline_path = edited_path.parent / "France1_retail_baseline.manifest.json"
        if not baseline_path.is_file():
            raise ProbeError(f"baseline reference manifest is required: {baseline_path}")
        baseline_manifest = json.loads(baseline_path.read_text(encoding="utf-8"))
        if baseline_manifest.get("source_xml_sha256") != FRANCE1_RETAIL_XML_SHA256:
            raise ProbeError("baseline reference manifest source hash mismatch")
    if manifest.get("research_output_root") and Path(manifest["research_output_root"]).resolve() != resolved_root:
        raise ProbeError("probe manifest output root does not match this verification")
    runtime_hash = _verify_runtime_executable()
    _print_output_locations(resolved_root, edited_path, manifest_path)
    print(f"verified {probe_name}; baseline SHA256: {FRANCE1_RETAIL_XML_SHA256}; candidate SHA256: {sha256(actual)}")
    print(f"Runtime EXE SHA256: {runtime_hash}")
    print("Byte scope: only the predeclared Marker Pos attributes changed")
    return manifest


def _inspect(source_path: Path, output_root: Path | None = None) -> dict:
    source_path = source_path.resolve()
    resolved_root = (output_root or DEFAULT_OUTPUT_ROOT).expanduser().resolve()
    payload = source_path.read_bytes()
    actual_hash = sha256(payload)
    if actual_hash != FRANCE1_RETAIL_XML_SHA256:
        raise ProbeError(f"France1 source SHA256 mismatch: expected {FRANCE1_RETAIL_XML_SHA256}, got {actual_hash}")
    report = {
        "source_xml": str(source_path),
        "source_xml_sha256": actual_hash,
        "research_output_root": str(resolved_root),
        "probes": {},
    }
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
    print(f"Research output root: {resolved_root}")
    print("Probe XML: inspect is read-only; no candidate written")
    print("Manifest: inspect is read-only; no manifest written")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect", help="show the fixed France1 probe targets")
    inspect.add_argument("--source", required=True, type=Path)
    inspect.add_argument("--output-root", type=Path, help="research output root (default: Master Rallye runtime root research-output)")
    for name in PROBES:
        prepare = commands.add_parser(f"prepare-{name}", help=f"prepare the fixed {name} XML probe")
        prepare.add_argument("--source", required=True, type=Path)
        destination = prepare.add_mutually_exclusive_group()
        destination.add_argument("--output", type=Path, help="explicit candidate XML path inside <output-root>/g1/probes")
        destination.add_argument("--output-root", type=Path, help="research output root; writes candidate under g1/probes")
    verify = commands.add_parser("verify", help="verify a probe XML against the fixed source and recipe")
    verify.add_argument("--kind", required=True, choices=tuple(PROBES))
    verify.add_argument("--source", required=True, type=Path)
    verify.add_argument("--edited", required=True, type=Path)
    verify.add_argument("--output-root", type=Path, help="expected research output root (defaults to the edited XML location)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "inspect":
            _inspect(args.source, args.output_root)
        elif args.command.startswith("prepare-"):
            _prepare(
                args.command.removeprefix("prepare-"),
                args.source,
                output_path=args.output,
                output_root=args.output_root,
            )
        else:
            _verify(args.kind, args.source, args.edited, output_root=args.output_root)
    except (OSError, ProbeError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
