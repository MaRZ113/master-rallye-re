"""Create ignored Astero positions-only candidates for the human runtime gate."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def args_after_separator() -> list[str]:
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def select_visible_vertex(model):
    minimum = tuple(
        min(value[axis] for value in model.vertices.positions)
        for axis in range(3)
    )
    maximum = tuple(
        max(value[axis] for value in model.vertices.positions)
        for axis in range(3)
    )
    candidates = [
        (index, value)
        for index, value in enumerate(model.vertices.positions)
        if 0.0 < value[0] < maximum[0] - 0.1
    ]
    vertex_index, old = max(candidates, key=lambda item: item[1][1])
    delta_x = min(0.08, (maximum[0] - old[0]) * 0.25)
    if delta_x <= 0.01:
        raise RuntimeError("no visible AABB-safe candidate displacement")
    return vertex_index, delta_x, minimum, maximum


def main() -> None:
    values = args_after_separator()
    if len(values) != 2:
        raise SystemExit("usage after --: <Astero-folder> <output-directory>")
    source_folder, output_folder = map(Path, values)
    output_folder.mkdir(parents=True, exist_ok=True)
    root = repository_root()
    sys.path.insert(0, str(root / "src"))
    sys.path.insert(0, str(root / "blender"))

    import master_rallye_io
    from master_rallye.coords import position_to_blender
    from master_rallye_io.blender_export import export_dx_positions
    from master_rallye_io.blender_mesh import create_collection, import_dx_resource

    bpy.ops.wm.read_factory_settings(use_empty=True)
    master_rallye_io.register()
    reports = []
    for filename in ("complete.dx", "car.dx"):
        source = source_folder / filename
        result = import_dx_resource(
            source,
            create_collection(f"R3 runtime {source.stem}"),
            object_name=f"Astero_{source.stem}_runtime_candidate",
            import_sidecar=True,
            load_textures=False,
            strict=True,
        )
        obj = result.object
        model = result.model
        vertex_index, requested_delta, minimum, maximum = select_visible_vertex(model)
        source_ids = obj.data.attributes["mr_source_vertex"].data
        blender_vertex = next(
            index
            for index, item in enumerate(source_ids)
            if int(item.value) == vertex_index
        )
        old_source = model.vertices.positions[vertex_index]
        old_blender = tuple(float(value) for value in obj.data.vertices[blender_vertex].co)
        obj.data.vertices[blender_vertex].co.x += requested_delta
        new_blender = tuple(float(value) for value in obj.data.vertices[blender_vertex].co)
        output = output_folder / f"Astero-{source.stem}-one-vertex.dx"
        exported = export_dx_positions(obj, output)
        if len(exported.patch.changes) != 1:
            raise AssertionError(f"{filename}: expected one changed vertex")
        change = exported.patch.changes[0]
        if change.vertex_index != vertex_index:
            raise AssertionError(f"{filename}: wrong source vertex changed")
        if exported.patch.diff.unexpected_ranges:
            raise AssertionError(f"{filename}: unexpected binary differences")
        inside = all(
            minimum[axis] <= change.new_position[axis] <= maximum[axis]
            for axis in range(3)
        )
        if not inside:
            raise AssertionError(f"{filename}: candidate escaped original AABB")
        report = exported.patch.to_dict()
        report.update(
            {
                "resource_name": filename,
                "source_path": str(source.resolve()),
                "output_path": str(output.resolve()),
                "vertex_index": vertex_index,
                "old_source_position": list(old_source),
                "new_source_position": list(change.new_position),
                "old_blender_position": list(old_blender),
                "new_blender_position": list(new_blender),
                "requested_blender_delta": [requested_delta, 0.0, 0.0],
                "original_aabb_minimum": list(minimum),
                "original_aabb_maximum": list(maximum),
                "aabb_containment": inside,
                "runtime_role_confidence": "LOW",
            }
        )
        reports.append(report)

    validation_path = output_folder / "validation.json"
    validation_path.write_text(
        json.dumps(
            {
                "phase": "R3",
                "status": "READY_FOR_HUMAN_RUNTIME_TEST",
                "candidates": reports,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (output_folder / "TEST_INSTRUCTIONS.txt").write_text(
        "MASTER RALLYE R3 HUMAN RUNTIME TEST\n"
        "===================================\n\n"
        "These files are experimental positions-only candidates. The available XML/TXT\n"
        "does not directly prove whether complete.dx or car.dx is selected in each game\n"
        "context, so both are supplied and must be tested ONE AT A TIME.\n\n"
        "1. Back up the matching original Astero DX file.\n"
        "2. Copy ONE candidate manually to the matching resource location/name.\n"
        "3. Launch Master Rallye and inspect Astero in the relevant menu/race context.\n"
        "4. Restore the original before trying the other candidate.\n"
        "5. Report: GAME LOADS / CRASHES; MODEL LOADS / FAILS;\n"
        "   EDIT VISIBLE / NOT VISIBLE; OTHER ARTIFACTS.\n\n"
        "The edit moves one upper-body source vertex +0.08 along source X and remains\n"
        "inside the original AABB. No original file was overwritten automatically.\n",
        encoding="utf-8",
    )
    print("R3_RUNTIME_CANDIDATES_READY", json.dumps(reports, sort_keys=True))


if __name__ == "__main__":
    main()
