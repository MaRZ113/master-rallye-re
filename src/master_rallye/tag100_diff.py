"""Read-only byte and candidate-scalar analysis for course DX tag100 regions.

The module deliberately does not assign physical-collision semantics to tag100.
DX extraction relies on the course render parser's exact trailing-section
boundary; it never searches a file for the integer value 100.
"""
from __future__ import annotations

import hashlib
import math
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from .dx_course import parse_course_dx_bytes
from .errors import FormatError

TAG100 = 100


@dataclass(frozen=True)
class Tag100Slice:
    source: str
    tag_offset: int
    raw: bytes
    render_validated: bool

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.raw).hexdigest()


def extract_tag100_from_dx_bytes(data: bytes, source: str = "<bytes>") -> Tag100Slice:
    """Extract the exact tag100 suffix at the parsed course-render boundary."""
    model = parse_course_dx_bytes(data, source)
    if not model.course_render_validated:
        raise FormatError(f"course render prefix is not fully validated in {source}")
    section = model.collision.bsp
    if section is None:
        raise FormatError(f"no structurally detected tag100 section follows the render data in {source}")
    if section.status != "raw-length-unresolved":
        raise FormatError(f"unexpected tag100 boundary status {section.status!r} in {source}")
    if section.tag_offset != model.trailing.offset:
        raise FormatError(
            f"tag100 offset 0x{section.tag_offset:X} differs from parsed render boundary "
            f"0x{model.trailing.offset:X} in {source}"
        )
    raw = data[section.tag_offset:]
    if raw != section.raw:
        raise FormatError(f"tag100 parser slice is not the exact DX suffix in {source}")
    if len(raw) < 4 or struct.unpack_from("<I", raw)[0] != TAG100:
        raise FormatError(f"tag100 marker is absent at parsed offset 0x{section.tag_offset:X} in {source}")
    return Tag100Slice(source, section.tag_offset, raw, model.course_render_validated)


def extract_tag100_from_dx(path: Path) -> Tag100Slice:
    resolved = path.resolve()
    return extract_tag100_from_dx_bytes(resolved.read_bytes(), resolved.name)


def changed_ranges(before: bytes, after: bytes) -> list[dict[str, int]]:
    """Return contiguous differing byte spans as relative [start, end) ranges."""
    common = min(len(before), len(after))
    ranges: list[dict[str, int]] = []
    start: int | None = None
    for offset in range(common):
        differs = before[offset] != after[offset]
        if differs and start is None:
            start = offset
        elif not differs and start is not None:
            ranges.append({"start": start, "end_exclusive": offset, "length": offset - start})
            start = None
    if start is not None:
        ranges.append({"start": start, "end_exclusive": common, "length": common - start})
    if len(before) != len(after):
        tail_start = common
        tail_end = max(len(before), len(after))
        if ranges and ranges[-1]["end_exclusive"] == tail_start:
            ranges[-1]["end_exclusive"] = tail_end
            ranges[-1]["length"] = tail_end - ranges[-1]["start"]
        else:
            ranges.append({
                "start": tail_start,
                "end_exclusive": tail_end,
                "length": abs(len(before) - len(after)),
            })
    return ranges


def plane_residual(
    normal: Sequence[float],
    d: float,
    point: Sequence[float],
    *,
    convention: str,
) -> float:
    """Evaluate one of two common plane conventions without choosing one."""
    if len(normal) != 3 or len(point) != 3:
        raise ValueError("plane normal and point must each have three components")
    dot = sum(float(normal[i]) * float(point[i]) for i in range(3))
    if convention == "dot_plus_d_zero":
        return dot + float(d)
    if convention == "dot_equals_d":
        return dot - float(d)
    raise ValueError(f"unsupported plane convention {convention!r}")


def translated_plane_d(
    normal: Sequence[float],
    d: float,
    translation: Sequence[float],
    *,
    convention: str,
) -> float:
    """Return d' for a translated plane under an explicitly named convention.

    For ``n·x + d = 0``, translating geometry by t gives d' = d - n·t.
    For ``n·x = d``, it gives d' = d + n·t. The caller supplies the
    convention; this helper does not infer which one tag100 uses.
    """
    if len(normal) != 3 or len(translation) != 3:
        raise ValueError("normal and translation must each have three components")
    shift = sum(float(normal[i]) * float(translation[i]) for i in range(3))
    if convention == "dot_plus_d_zero":
        return float(d) - shift
    if convention == "dot_equals_d":
        return float(d) + shift
    raise ValueError(f"unsupported plane convention {convention!r}")


def _f32_tuple(data: bytes, offset: int, count: int) -> tuple[float, ...] | None:
    values = struct.unpack_from("<" + "f" * count, data, offset)
    return values if all(math.isfinite(item) for item in values) else None


def _normal_length(values: Sequence[float]) -> float:
    return math.sqrt(sum(float(value) ** 2 for value in values))


def _unchanged_spans(
    length: int, ranges: Sequence[dict[str, int]], *, limit: int = 12
) -> dict[str, Any]:
    spans: list[dict[str, int]] = []
    cursor = 0
    for item in ranges:
        start = item["start"]
        if start > cursor:
            spans.append({"start": cursor, "end_exclusive": start, "length": start - cursor})
        cursor = max(cursor, item["end_exclusive"])
    if cursor < length:
        spans.append({"start": cursor, "end_exclusive": length, "length": length - cursor})
    return {
        "count": len(spans),
        "total_bytes": sum(item["length"] for item in spans),
        "longest": sorted(spans, key=lambda item: (-item["length"], item["start"]))[:limit],
    }


def _changed_clusters(
    ranges: Sequence[dict[str, int]], *, maximum_gap: int = 65_536
) -> list[dict[str, int]]:
    """Group nearby raw difference ranges; this is a navigation aid, not grammar."""
    if maximum_gap < 0:
        raise ValueError("maximum_gap must be non-negative")
    clusters: list[dict[str, int]] = []
    for item in ranges:
        if not clusters or item["start"] - clusters[-1]["end_exclusive"] > maximum_gap:
            clusters.append({
                "start": item["start"],
                "end_exclusive": item["end_exclusive"],
                "range_count": 1,
                "changed_byte_count": item["length"],
                "maximum_join_gap": maximum_gap,
            })
        else:
            cluster = clusters[-1]
            cluster["end_exclusive"] = item["end_exclusive"]
            cluster["range_count"] += 1
            cluster["changed_byte_count"] += item["length"]
    return clusters


def analyze_tag100_diff(
    baseline: Tag100Slice,
    modified: Tag100Slice,
    *,
    normal_tolerance: float = 0.01,
    max_samples_per_layout: int = 8,
) -> dict[str, Any]:
    """Compare tag100 byte slices and summarize aligned finite float candidates.

    Float2/3/4 windows are hypotheses over the already bounded tag100 region.
    Their counts and samples are evidence only; no record grammar is asserted.
    """
    if normal_tolerance < 0 or not math.isfinite(normal_tolerance):
        raise ValueError("normal_tolerance must be finite and non-negative")
    if not baseline.render_validated or not modified.render_validated:
        raise FormatError("both tag100 slices must come from fully validated course render prefixes")
    if len(baseline.raw) < 4 or len(modified.raw) < 4:
        raise FormatError("tag100 slices are shorter than the four-byte marker")
    if struct.unpack_from("<I", baseline.raw)[0] != TAG100:
        raise FormatError("baseline slice does not begin with the tag100 marker")
    if struct.unpack_from("<I", modified.raw)[0] != TAG100:
        raise FormatError("modified slice does not begin with the tag100 marker")
    if len(baseline.raw) != len(modified.raw):
        raise FormatError(
            f"tag100 sizes differ ({len(baseline.raw)} vs {len(modified.raw)}); "
            "refusing aligned record-candidate analysis"
        )

    before, after = baseline.raw, modified.raw
    ranges = changed_ranges(before, after)
    changed_offsets: list[int] = []
    for item in ranges:
        changed_offsets.extend(range(item["start"], item["end_exclusive"]))
    changed_count = len(changed_offsets)
    common_size = len(before)
    alignment_histogram = {
        str(modulus): {
            str(remainder): sum(offset % modulus == remainder for offset in changed_offsets)
            for remainder in range(modulus)
        }
        for modulus in (4, 16)
    }
    range_alignment_histogram = {
        str(modulus): {
            str(remainder): sum(item["start"] % modulus == remainder for item in ranges)
            for remainder in range(modulus)
        }
        for modulus in (4, 16)
    }

    scalar_fields: list[dict[str, Any]] = []
    non_finite_scalar_count = 0
    scalar_offsets = sorted({offset - offset % 4 for offset in changed_offsets})
    for offset in scalar_offsets:
        if offset + 4 > common_size:
            continue
        old_raw = before[offset:offset + 4]
        new_raw = after[offset:offset + 4]
        if old_raw == new_raw:
            continue
        old = struct.unpack("<f", old_raw)[0]
        new = struct.unpack("<f", new_raw)[0]
        if not math.isfinite(old) or not math.isfinite(new):
            non_finite_scalar_count += 1
            continue
        scalar_fields.append({
            "offset": offset,
            "baseline": old,
            "modified": new,
            "delta": new - old,
        })

    window_summaries: list[dict[str, Any]] = []
    plane_candidates: list[dict[str, Any]] = []
    for component_count in (2, 3, 4):
        stride = component_count * 4
        for alignment in range(0, stride, 4):
            candidate_count = 0
            finite_count = 0
            normal_like_count = 0
            samples: list[dict[str, Any]] = []
            possible_offsets = sorted({
                alignment + ((changed_offset - alignment) // stride) * stride
                for changed_offset in changed_offsets
            })
            for offset in possible_offsets:
                if offset < 0 or offset + stride > common_size:
                    continue
                old_raw = before[offset:offset + stride]
                new_raw = after[offset:offset + stride]
                if old_raw == new_raw:
                    continue
                candidate_count += 1
                old_values = _f32_tuple(before, offset, component_count)
                new_values = _f32_tuple(after, offset, component_count)
                if old_values is None or new_values is None:
                    continue
                finite_count += 1
                record: dict[str, Any] = {
                    "offset": offset,
                    "baseline": list(old_values),
                    "modified": list(new_values),
                    "delta": [new_values[i] - old_values[i] for i in range(component_count)],
                    "changed_components": [
                        i for i in range(component_count)
                        if old_raw[i * 4:(i + 1) * 4] != new_raw[i * 4:(i + 1) * 4]
                    ],
                }
                if component_count == 4:
                    old_length = _normal_length(old_values[:3])
                    new_length = _normal_length(new_values[:3])
                    record["normal_length_baseline"] = old_length
                    record["normal_length_modified"] = new_length
                    record["normal_delta_length"] = _normal_length(
                        [new_values[i] - old_values[i] for i in range(3)]
                    )
                    record["d_delta"] = new_values[3] - old_values[3]
                    record["normal_like"] = (
                        abs(old_length - 1.0) <= normal_tolerance
                        and abs(new_length - 1.0) <= normal_tolerance
                    )
                    if record["normal_like"]:
                        normal_like_count += 1
                        previous_offset = offset - stride
                        next_offset = offset + stride
                        neighbors: dict[str, Any] = {}
                        for label, neighbor_offset in (
                            ("previous", previous_offset), ("next", next_offset)
                        ):
                            if 0 <= neighbor_offset <= common_size - stride:
                                old_neighbor = _f32_tuple(before, neighbor_offset, 4)
                                new_neighbor = _f32_tuple(after, neighbor_offset, 4)
                                if old_neighbor is not None and new_neighbor is not None:
                                    neighbors[label] = {
                                        "offset": neighbor_offset,
                                        "baseline": list(old_neighbor),
                                        "modified": list(new_neighbor),
                                        "changed": old_neighbor != new_neighbor,
                                    }
                        record["neighboring_float4_windows"] = neighbors
                        record["candidate_status"] = "unit-normal-like float4 window; record semantics unknown"
                        plane_candidates.append({
                            "alignment_mod_16": alignment,
                            **record,
                        })
                if len(samples) < max_samples_per_layout:
                    samples.append(record)
            window_summaries.append({
                "components": component_count,
                "stride_bytes": stride,
                "alignment_mod_stride": alignment,
                "changed_windows": candidate_count,
                "finite_changed_windows": finite_count,
                "unit_normal_like_float4_windows": normal_like_count if component_count == 4 else None,
                "samples": samples,
            })

    return {
        "schema": "master-rallye-tag100-diff-v1",
        "interpretation": {
            "tag100_semantics": "UNKNOWN",
            "float_windows": "candidate views only; offsets are relative to the detected tag100 marker",
            "unit_normal_like_float4": "HIGH_CONFIDENCE_INFERENCE of plane-like coefficients only; not proof of physical collision or record grammar",
            "byte_region_boundary": "CONFIRMED_BY_BINARY from the parsed course-render boundary; internal tag100 end is unresolved",
        },
        "baseline": {
            "source": baseline.source,
            "tag_offset_in_dx": baseline.tag_offset,
            "size": len(before),
            "sha256": baseline.sha256,
            "render_validated": baseline.render_validated,
        },
        "modified": {
            "source": modified.source,
            "tag_offset_in_dx": modified.tag_offset,
            "size": len(after),
            "sha256": modified.sha256,
            "render_validated": modified.render_validated,
        },
        "summary": {
            "same_size": True,
            "changed_byte_count": changed_count,
            "unchanged_byte_count": common_size - changed_count,
            "changed_range_count": len(ranges),
            "changed_percent": changed_count * 100.0 / common_size if common_size else 0.0,
            "changed_aligned_finite_float32_count": len(scalar_fields),
            "changed_aligned_non_finite_float32_count": non_finite_scalar_count,
            "unit_normal_like_changed_float4_window_count": len(plane_candidates),
            "normal_tolerance": normal_tolerance,
        },
        "changed_byte_offset_alignment_histogram": alignment_histogram,
        "changed_range_start_alignment_histogram": range_alignment_histogram,
        "changed_ranges": ranges,
        "changed_range_clusters": _changed_clusters(ranges),
        "unchanged_spans": _unchanged_spans(common_size, ranges),
        "aligned_finite_float32_candidates": scalar_fields,
        "float_window_layouts": window_summaries,
        "unit_normal_like_float4_candidates": plane_candidates,
    }


def render_tag100_diff_markdown(report: dict[str, Any]) -> str:
    baseline = report["baseline"]
    modified = report["modified"]
    summary = report["summary"]
    lines = [
        "# Course tag100 differential",
        "",
        f"- Baseline: `{baseline['source']}` at DX offset `0x{baseline['tag_offset_in_dx']:X}`, "
        f"  {baseline['size']:,} bytes, SHA-256 `{baseline['sha256']}`",
        f"- Modified: `{modified['source']}` at DX offset `0x{modified['tag_offset_in_dx']:X}`, "
        f"  {modified['size']:,} bytes, SHA-256 `{modified['sha256']}`",
        f"- Changed bytes: {summary['changed_byte_count']:,} "
        f"({summary['changed_percent']:.6f}%) across {summary['changed_range_count']:,} ranges",
        f"- Unchanged bytes: {summary['unchanged_byte_count']:,}",
        f"- Aligned finite float32 candidates: {summary['changed_aligned_finite_float32_count']:,}",
        f"- Unit-normal-like changed float4 windows: {summary['unit_normal_like_changed_float4_window_count']:,} "
        f"(tolerance ±{summary['normal_tolerance']})",
        "",
        "## Changed ranges",
        "",
        "Offsets are relative to the tag100 marker; end offsets are exclusive.",
        "",
        "| Start | End | Bytes | Start mod 16 |",
        "|---:|---:|---:|---:|",
    ]
    for item in report["changed_ranges"]:
        lines.append(
            f"| `0x{item['start']:X}` | `0x{item['end_exclusive']:X}` | "
            f"{item['length']} | {item['start'] % 16} |"
        )
    lines.extend([
        "",
        "## Candidate float4 windows with unit-length first three values",
        "",
        "These are overlapping alignment hypotheses, not decoded records.",
        "The plane equation, record boundary, and runtime role are unknown.",
        "",
        "| Alignment mod 16 | Relative offset | Normal length before → after | Delta normal length | Delta fourth value | Changed components |",
        "|---:|---:|---:|---:|---:|---|",
    ])
    for item in report["unit_normal_like_float4_candidates"]:
        changed = ", ".join(str(index) for index in item["changed_components"])
        lines.append(
            f"| {item['alignment_mod_16']} | `0x{item['offset']:X}` | "
            f"{item['normal_length_baseline']:.9f} → {item['normal_length_modified']:.9f} | "
            f"{item['normal_delta_length']:.9g} | {item['d_delta']:.9g} | {changed} |"
        )
    lines.extend([
        "",
        "## Difference neighborhoods",
        "",
        "Ranges separated by at most 64 KiB are grouped for navigation only;",
        "these groups do not imply tag100 record boundaries.",
        "",
        "| Start | End | Ranges | Changed bytes |",
        "|---:|---:|---:|---:|",
    ])
    for item in report["changed_range_clusters"]:
        lines.append(
            f"| `0x{item['start']:X}` | `0x{item['end_exclusive']:X}` | "
            f"{item['range_count']} | {item['changed_byte_count']} |"
        )
    lines.extend([
        "",
        "## Unchanged spans",
        "",
        f"There are {report['unchanged_spans']['count']:,} unchanged spans totaling "
        f"{report['unchanged_spans']['total_bytes']:,} bytes. The twelve longest are:",
        "",
        "| Start | End | Bytes |",
        "|---:|---:|---:|",
    ])
    for item in report["unchanged_spans"]["longest"]:
        lines.append(
            f"| `0x{item['start']:X}` | `0x{item['end_exclusive']:X}` | {item['length']:,} |"
        )
    lines.extend([
        "",
        "The detected tag100 region begins exactly at the validated course-render",
        "boundary. Its internal payload end remains unresolved. Plane-like float4",
        "windows are a `HIGH_CONFIDENCE_INFERENCE` about coefficient shape only;",
        "they do not establish collision, spatial-tree, or trigger semantics.",
        "",
    ])
    return "\n".join(lines)
