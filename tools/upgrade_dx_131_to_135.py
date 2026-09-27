#!/usr/bin/env python3
"""Create a research-only DX 131 to 135 candidate without index reordering."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
RESEARCH_OUTPUT_ROOT = (REPOSITORY_ROOT / ".research-output").resolve()
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from master_rallye.dx import parse_dx_bytes
from master_rallye.dx_revision_upgrade import upgrade_dx_131_to_135


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rev131_dx", type=Path)
    parser.add_argument("output_dx", type=Path)
    parser.add_argument("--overwrite", action="store_true",
                        help="replace an existing output file")
    args = parser.parse_args()

    source = args.rev131_dx.resolve(strict=True)
    output = args.output_dx.resolve()
    if output != RESEARCH_OUTPUT_ROOT and RESEARCH_OUTPUT_ROOT not in output.parents:
        parser.error(f"prototype DX output must be under ignored {RESEARCH_OUTPUT_ROOT}")
    if source == output:
        parser.error("output path must not be the rev131 input path")
    if output.exists() and not args.overwrite:
        parser.error(f"output already exists (use --overwrite to replace): {output}")

    source_bytes = source.read_bytes()
    candidate = upgrade_dx_131_to_135(source_bytes, str(source))
    parsed = parse_dx_bytes(candidate, str(output))
    draws = [draw for group in parsed.draw_groups for draw in group.root.flattened()]
    summary = {
        "source": str(source),
        "source_sha256": _sha256(source_bytes),
        "output": str(output),
        "output_sha256": _sha256(candidate),
        "output_size": len(candidate),
        "revision": parsed.word_0x04,
        "draw_record_count": len(draws),
        "material_count": None,
        "material_count_status": "not represented as a separate parsed structure",
        "texture_slot_reference_count": sum(len(draw.texture_slots) for draw in draws),
        "vertex_count": parsed.vertex_count,
        "triangle_count_from_draw_index_counts": sum(draw.index_count // 3 for draw in draws),
        "local_indices_preserved_by_rule": True,
        "global_index_table": {
            "present": parsed.global_index_table is not None,
            "reconstructed_match": parsed.diagnostics.reconstructed_global_match,
        },
        "collision_tag_ids": list(parsed.collision.tag_ids),
        "collision_errors": parsed.collision.errors,
        "collision_warnings": parsed.collision.warnings,
        "parser_errors": parsed.diagnostics.errors,
        "parser_warnings": parsed.diagnostics.warnings,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(candidate)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
