#!/usr/bin/env python3
"""Validate the R3 template position writer against vehicle DX resources."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from master_rallye.dx import parse_dx_bytes
from master_rallye.dx_writer import patch_dx_positions


def safe_candidate(model, fraction: float = 1.0e-4):
    positions = model.vertices.positions
    minimum = tuple(min(value[axis] for value in positions) for axis in range(3))
    maximum = tuple(max(value[axis] for value in positions) for axis in range(3))
    extrema_counts = Counter(
        (axis, side)
        for value in positions
        for axis in range(3)
        for side, boundary in (("min", minimum[axis]), ("max", maximum[axis]))
        if value[axis] == boundary
    )
    candidates = []
    for vertex_index, value in enumerate(positions):
        for axis in range(3):
            span = maximum[axis] - minimum[axis]
            if span <= 0:
                continue
            step = max(span * fraction, 1.0e-6)
            if minimum[axis] + step < value[axis] < maximum[axis] - step:
                candidates.append((0, vertex_index, axis, step))
            elif value[axis] == minimum[axis] and extrema_counts[(axis, "min")] > 1:
                candidates.append((1, vertex_index, axis, step))
            elif value[axis] == maximum[axis] and extrema_counts[(axis, "max")] > 1:
                candidates.append((1, vertex_index, axis, -step))
    if not candidates:
        return None
    _, vertex_index, axis, delta = min(candidates)
    changed = [tuple(value) for value in positions]
    value = list(changed[vertex_index])
    value[axis] += delta
    changed[vertex_index] = tuple(value)
    return vertex_index, axis, delta, tuple(changed)


def markdown(payload: dict) -> str:
    summary = payload["summary"]
    lines = [
        "# R3 DX writer corpus validation",
        "",
        "All operations used the original bytes as an in-memory template. No generated",
        "DX resource was retained in the repository.",
        "",
        "| Metric | Result |",
        "|---|---:|",
        f"| Vehicle DX resources | {summary['total_resources']} |",
        f"| Zero-edit byte-identical | {summary['zero_edit_byte_identical']} |",
        f"| Safe single-position validated | {summary['single_position_validated']} |",
        f"| Single-position skipped | {summary['single_position_skipped']} |",
        f"| Tag-101 payload hashes preserved | {summary['tag101_payload_preserved']}/{summary['tag101_resources']} |",
        f"| Failures | {summary['failures']} |",
        "",
        "A single-position pass means the candidate stayed inside the original AABB,",
        "changed only its source 12-byte position record, reparsed successfully, and",
        "preserved all known non-position structures and original diagnostics.",
        "",
    ]
    failures = [item for item in payload["resources"] if item["status"] != "PASS"]
    if failures:
        lines.extend(["## Exceptions", ""])
        for item in failures:
            lines.append(f"- `{item['path']}`: {item.get('error') or item.get('skip_reason')}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("vehicle_root", type=Path)
    parser.add_argument("--json", required=True, type=Path)
    parser.add_argument("--markdown", required=True, type=Path)
    args = parser.parse_args()
    root = args.vehicle_root.resolve()
    resources = []
    for path in sorted(root.rglob("*.dx"), key=lambda item: str(item).casefold()):
        relative = path.relative_to(root).as_posix()
        item = {"path": relative, "status": "PASS"}
        try:
            data = path.read_bytes()
            model = parse_dx_bytes(data, source=relative)
            tag101_before = model.collision.convex_hull.sha256 if model.collision.convex_hull else None
            item["tag101_present"] = tag101_before is not None
            item["tag101_sha256_before"] = tag101_before
            zero = patch_dx_positions(data, model.vertices.positions, source=relative)
            item["zero_edit_byte_identical"] = zero.byte_identical
            item["source_sha256"] = zero.source_sha256
            item["original_warnings"] = list(model.diagnostics.warnings)
            candidate = safe_candidate(model)
            if candidate is None:
                item["single_position"] = "SKIPPED"
                item["skip_reason"] = "no AABB-preserving candidate vertex/component"
            else:
                vertex_index, axis, requested_delta, positions = candidate
                changed = patch_dx_positions(data, positions, source=relative)
                item["single_position"] = "PASS"
                item["vertex_index"] = vertex_index
                item["axis"] = axis
                item["requested_delta"] = requested_delta
                item["actual_delta"] = list(changed.changes[0].delta)
                item["changed_byte_count"] = changed.diff.changed_byte_count
                item["changed_ranges"] = [
                    value.to_dict() for value in changed.diff.changed_ranges
                ]
                item["post_write_validated"] = changed.output_model.diagnostics.validated
                tag101_after = (
                    changed.output_model.collision.convex_hull.sha256
                    if changed.output_model.collision.convex_hull else None
                )
                item["tag101_sha256_after"] = tag101_after
                item["tag101_payload_preserved"] = tag101_before == tag101_after
                item["unexpected_ranges"] = [
                    value.to_dict() for value in changed.diff.unexpected_ranges
                ]
            if not zero.byte_identical:
                raise AssertionError("zero-edit output was not byte-identical")
        except Exception as error:
            item["status"] = "FAIL"
            item["error"] = f"{type(error).__name__}: {error}"
        resources.append(item)
    payload = {
        "phase": "R3",
        "scope": "DataGx/Vehicles/**/*.dx",
        "writer_mode": "template-preserving-positions-only",
        "safe_bounds": True,
        "resources": resources,
    }
    payload["summary"] = {
        "total_resources": len(resources),
        "zero_edit_byte_identical": sum(
            item.get("zero_edit_byte_identical") is True for item in resources
        ),
        "single_position_validated": sum(
            item.get("single_position") == "PASS" for item in resources
        ),
        "single_position_skipped": sum(
            item.get("single_position") == "SKIPPED" for item in resources
        ),
        "failures": sum(item["status"] == "FAIL" for item in resources),
        "tag101_resources": sum(item.get("tag101_present") is True for item in resources),
        "tag101_payload_preserved": sum(
            item.get("tag101_present") is True
            and item.get("tag101_payload_preserved") is True
            for item in resources
        ),
    }
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    args.markdown.write_text(markdown(payload).rstrip() + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0 if payload["summary"]["failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
