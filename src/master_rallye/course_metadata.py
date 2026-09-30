"""Read-only Blender metadata decoration for the observed course DX reader."""
from __future__ import annotations

import hashlib


def mark_course_metadata(metadata, model):
    """Record the course grammar boundary while keeping unknown data explicit."""
    metadata = dict(metadata)
    metadata["phase"] = "R5T-A"
    metadata["resource_kind"] = "course"
    metadata["format_status"] = "COURSE_RENDER_READ_ONLY"
    metadata["course"] = {
        "dx_revision": model.word_0x04,
        "root_wrapper": {
            "present": model.course_wrapper is not None,
            "offset": model.course_wrapper.offset if model.course_wrapper else None,
            "tag": model.course_wrapper.tag if model.course_wrapper else None,
            "control_words": list(model.course_wrapper.control_words) if model.course_wrapper else [],
            "child_count": model.course_wrapper.child_count if model.course_wrapper else None,
            "direct_root_record_count": len(model.course_root_records),
        },
        "draw_batches": [
            {
                "offset": batch.offset,
                "preamble": batch.preamble,
                "record_count": batch.record_count,
                "record_tags": [record.tag for record in batch.records],
                "byte_size": len(batch.raw),
                "sha256": hashlib.sha256(batch.raw).hexdigest(),
            }
            for batch in model.course_batches
        ],
        "course_containers": [
            {
                "record_path": record.record_path,
                "tag": record.tag,
                "offset": record.offset,
                "control_words": list(record.control_words),
                "child_count": record.declared_child_count,
                "raw_prefix_hex": record.opaque_prefix.hex(),
                "prefix_semantics": "course draw wrapper controls" if record.tag == 4 else "UNKNOWN",
            }
            for group in model.draw_groups for record in group.root.flattened()
            if record.tag in {1, 4, 5, 6} and record.opaque_prefix is not None
        ],
        "render_validation": {
            "passed": model.course_render_validated,
            "scope": "common DX arrays plus parsed revision-135 course draw/index ranges",
            "index_coverage": model.diagnostics.index_coverage,
            "vertex_coverage": model.diagnostics.vertex_coverage,
            "errors": list(model.diagnostics.errors),
            "warnings": list(model.diagnostics.warnings),
        },
        "opaque_course_data": {
            "trailing_tag_ids": list(model.collision.tag_ids),
            "tag100": None if model.collision.bsp is None else {
                "tag_offset": model.collision.bsp.tag_offset,
                "end_offset": model.collision.bsp.end_offset,
                "byte_size": len(model.collision.bsp.raw),
                "sha256": model.collision.bsp.sha256,
                "boundary_status": model.collision.bsp.status,
                "semantics": "UNKNOWN",
            },
            "route_data_decoded": False,
            "surface_data_decoded": False,
        },
        "source_directive_semantics": "UNKNOWN",
        "material_preview": {
            "method": "reuse existing DXT, sidecar, and structurally shared draw-record preview path",
            "D3D8_parity": "UNKNOWN",
            "new_course_semantics": "UNKNOWN",
        },
    }
    metadata["validation"] = {
        "validated": model.course_render_validated,
        "scope": "course render arrays, draw ranges, and local index references",
        "vehicle_global_index_comparison": "not applied; course sequential draw batches parsed with course grammar",
        "warnings": list(model.diagnostics.warnings),
        "errors": list(model.diagnostics.errors),
    }
    metadata["round_trip"] = {
        "writer_available": False,
        "read_only": True,
        "reason": "R5T-A does not implement course writing",
    }
    return metadata
