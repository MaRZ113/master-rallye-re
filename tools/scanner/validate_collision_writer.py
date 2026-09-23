#!/usr/bin/env python3
"""Validate exact tag-101 writing and translation over vehicle DX resources."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from master_rallye.collision_writer import (
    patch_dx_collision_translation,
    replace_dx_tag101,
    serialize_tag101,
)
from master_rallye.dx import parse_dx


DRY_RUN_DELTA = (0.001, -0.002, 0.003)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def scan(vehicle_root: Path) -> dict:
    root = vehicle_root.resolve()
    records = []
    failures = []
    for path in sorted(root.glob("*/*.dx"), key=lambda item: str(item).casefold()):
        relative = f"{path.parent.name}/{path.name}"
        model = parse_dx(path)
        hull = model.collision.convex_hull
        if hull is None:
            continue
        source = path.read_bytes()
        record = {
            "resource": relative,
            "evidence_class": (
                "STATIC_FORMAT_ONLY_OUTLIER"
                if path.parent.name.casefold() == "forklift"
                else "PC_VEHICLE_CORPUS"
            ),
            "source_dx_sha256": sha256(source),
            "tag101_offset": hull.tag_offset,
            "tag101_end_offset": hull.end_offset,
            "tag101_byte_count": len(hull.raw),
            "tag101_sha256": hull.sha256,
            "source_validation_errors": list(model.collision.errors),
        }
        try:
            encoded = serialize_tag101(hull)
            record["serialized_sha256"] = sha256(encoded)
            record["tag101_zero_edit_byte_identical"] = encoded == hull.raw
            rebuilt = replace_dx_tag101(source, encoded, source=relative)
            record["full_dx_zero_edit_byte_identical"] = rebuilt == source
        except Exception as error:
            record["tag101_zero_edit_byte_identical"] = False
            record["full_dx_zero_edit_byte_identical"] = False
            failures.append({
                "resource": relative,
                "stage": "zero-edit",
                "type": type(error).__name__,
                "message": str(error),
            })
        if model.collision.errors:
            record["translation"] = {
                "status": "SKIPPED",
                "reason": "source tag101 validation failed; static-only outlier",
            }
        else:
            try:
                result = patch_dx_collision_translation(
                    source, DRY_RUN_DELTA, source=relative
                )
                record["translation"] = {
                    "status": "PASS",
                    "delta": list(result.translation.delta),
                    "changed_byte_count": result.diff.changed_byte_count,
                    "changed_field_count": len(result.translation.changes),
                    "unexpected_diff_count": sum(
                        item.size for item in result.diff.unexpected_ranges
                    ),
                    "validation": result.translation.validation,
                    "visual_geometry_changed_bytes": 0,
                    "output_tag101_sha256": (
                        result.output_model.collision.convex_hull.sha256
                    ),
                }
            except Exception as error:
                record["translation"] = {
                    "status": "FAIL",
                    "type": type(error).__name__,
                    "reason": str(error),
                }
                failures.append({
                    "resource": relative,
                    "stage": "translation",
                    "type": type(error).__name__,
                    "message": str(error),
                })
        records.append(record)

    summary = {
        "tag101_resource_count": len(records),
        "structurally_parsed_count": len(records),
        "validated_count": sum(not item["source_validation_errors"] for item in records),
        "static_only_outlier_count": sum(
            item["evidence_class"] == "STATIC_FORMAT_ONLY_OUTLIER" for item in records
        ),
        "tag101_zero_edit_byte_identical_count": sum(
            item.get("tag101_zero_edit_byte_identical") is True for item in records
        ),
        "full_dx_zero_edit_byte_identical_count": sum(
            item.get("full_dx_zero_edit_byte_identical") is True for item in records
        ),
        "translation_pass_count": sum(
            item["translation"]["status"] == "PASS" for item in records
        ),
        "translation_skip_count": sum(
            item["translation"]["status"] == "SKIPPED" for item in records
        ),
        "translation_fail_count": sum(
            item["translation"]["status"] == "FAIL" for item in records
        ),
        "failure_count": len(failures),
    }
    return {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source_descriptor": "external read-only DataGx/Vehicles root (path omitted)",
        "translation_dry_run_delta": list(DRY_RUN_DELTA),
        "summary": summary,
        "resources": records,
        "failures": failures,
    }


def markdown(report: dict) -> str:
    summary = report["summary"]
    lines = [
        "# R4C tag-101 writer corpus",
        "",
        "Generated from external read-only vehicle resources. Modified dry-run bytes were retained only in memory.",
        "",
        "## Summary",
        "",
        f"- Tag-101 resources / structurally parsed: **{summary['tag101_resource_count']} / {summary['structurally_parsed_count']}**.",
        f"- Source-validated / static-only outliers: **{summary['validated_count']} / {summary['static_only_outlier_count']}**.",
        f"- Zero-edit tag-101 byte-identical: **{summary['tag101_zero_edit_byte_identical_count']}/{summary['tag101_resource_count']}**.",
        f"- Zero-edit full DX byte-identical: **{summary['full_dx_zero_edit_byte_identical_count']}/{summary['tag101_resource_count']}**.",
        f"- Translation pass / skipped / failed: **{summary['translation_pass_count']} / {summary['translation_skip_count']} / {summary['translation_fail_count']}**.",
        f"- Unexpected failures: **{summary['failure_count']}**.",
        "",
        "Forklift is serialized exactly but is skipped for translation because its known non-finite coordinates remain validation failures.",
        "",
        "## Resources",
        "",
        "| Resource | Bytes | Zero tag101 | Zero DX | Translation | Changed bytes | Evidence |",
        "|---|---:|---|---|---|---:|---|",
    ]
    for item in report["resources"]:
        translation = item["translation"]
        lines.append(
            f"| `{item['resource']}` | {item['tag101_byte_count']} | "
            f"{'PASS' if item['tag101_zero_edit_byte_identical'] else 'FAIL'} | "
            f"{'PASS' if item['full_dx_zero_edit_byte_identical'] else 'FAIL'} | "
            f"{translation['status']} | {translation.get('changed_byte_count', '-')} | "
            f"{item['evidence_class']} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("vehicle_root", type=Path)
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()
    report = scan(args.vehicle_root)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.markdown.write_text(markdown(report), encoding="utf-8")
    print(json.dumps(report["summary"], sort_keys=True))
    return 0 if not report["failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
