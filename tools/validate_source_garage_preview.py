"""Private-input neutral-source GPU and real Tk integration qualification.

This runs the existing viewport and Workshop Source Garage UI. It does not
launch a donor game, author MR-native resources, or modify supplied projects.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tools")]


def positions_from_mrpv(path):
    """Read staged vertex positions for independent normalization comparison."""
    data = path.read_bytes(); cursor = 40
    if data[:8] != b"MRPV\x01\0\0\0": raise ValueError("Unexpected preview format")
    texture_count, draw_count = struct.unpack_from("<II", data, 8)
    def string():
        nonlocal cursor
        length, = struct.unpack_from("<I", data, cursor); cursor += 4
        text = data[cursor:cursor+length].decode(); cursor += length; return text
    for _ in range(texture_count):
        string(); width, height = struct.unpack_from("<II", data, cursor); cursor += 8 + width*height*4
    result = {}
    for _ in range(draw_count):
        name = string(); header = struct.unpack_from("<Iii4I3fII", data, cursor); cursor += 48
        count, index_count = header[-2:]
        result[name] = [struct.unpack_from("<3f", data, cursor + i*36) for i in range(count)]
        cursor += count*36 + index_count*4
    if cursor != len(data): raise ValueError("Unparsed preview tail")
    return result


def inverse_matrix(matrix):
    rows = [list(matrix[r*4:r*4+4]) + [float(r == c) for c in range(4)] for r in range(4)]
    for column in range(4):
        pivot = max(range(column, 4), key=lambda r: abs(rows[r][column]))
        rows[column], rows[pivot] = rows[pivot], rows[column]
        divisor = rows[column][column]
        if abs(divisor) < 1e-12: raise ValueError("Non-invertible normalization")
        rows[column] = [value/divisor for value in rows[column]]
        for r in range(4):
            if r != column:
                factor = rows[r][column]
                rows[r] = [a-factor*b for a, b in zip(rows[r], rows[column])]
    return [value for row in rows for value in row[4:]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", required=True, type=Path)
    parser.add_argument("--viewer", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    from master_rallye.universal_vehicle_scene import load_scene, output_directory, sha, read_bounded
    from master_rallye.source_scene_preview import stage_source_scene, capture_views
    from master_rallye.workshop.source_garage_ui import preview_configuration
    scene = load_scene(args.scene)
    output = output_directory(args.output, [args.scene.parent, scene["source"]["root"], *scene["source"].get("protected_roots", [])])
    output.mkdir(parents=True)
    original = {p.relative_to(args.scene.parent).as_posix(): sha(read_bounded(p, 128 * 1024 * 1024))
                for p in args.scene.parent.rglob("*") if p.is_file()}
    viewer = args.viewer.resolve()
    staged = stage_source_scene(scene, output / "source-original.mrpv", scene_root=args.scene.parent)
    captures = capture_views(viewer, output / "source-original.mrpv", output / "six-views", provenance=scene["metadata"]["display_name"])
    stage_source_scene(scene, output / "source-basis.mrpv", scene_root=args.scene.parent, basis="source")
    source_basis_captures = capture_views(viewer, output / "source-basis.mrpv", output / "source-basis-views",
                                        provenance="Original source units/basis; neutral D3D9 camera", basis="source")
    source_positions = positions_from_mrpv(output / "source-basis.mrpv")
    normalized_positions = positions_from_mrpv(output / "source-original.mrpv")
    from master_rallye.universal_vehicle_scene import transform_point
    matrix = scene["coordinate_system"]["source_to_normalized"]
    max_normalization_error = max(abs(transform_point(matrix, source)[axis] - normalized[axis])
                                  for name, points in source_positions.items()
                                  for source, normalized in zip(points, normalized_positions[name]) for axis in range(3))
    if max_normalization_error > 2e-6:
        raise AssertionError("Source->normalized preview geometry differs from declared transform")
    inverse = inverse_matrix(matrix)
    max_roundtrip_error = max(abs(transform_point(inverse, normalized)[axis] - source[axis])
                              for name, points in source_positions.items()
                              for source, normalized in zip(points, normalized_positions[name]) for axis in range(3))
    if max_roundtrip_error > 1e-5:
        raise AssertionError("Normalized preview cannot round-trip to retained source coordinates")
    glass = {m["material_id"]: .35 for m in scene["meshes"] if m["name"] in ("GlassI", "GlassE")}
    interpreted = preview_configuration(scene, {"opacity_overrides": glass})
    stage_source_scene(interpreted, output / "explicit-glass.mrpv", scene_root=args.scene.parent, material_mode="interpreted")
    if positions_from_mrpv(output / "explicit-glass.mrpv") != normalized_positions:
        raise AssertionError("Opacity interpretation changed source geometry")
    interpreted_captures = capture_views(viewer, output / "explicit-glass.mrpv", output / "explicit-glass-views",
                                        provenance="Explicit opacity 0.35; unspecified source channel remains UNKNOWN")
    # Work on a small derived-project copy so UI choices never touch the input.
    private = output / "ui-source-project"
    shutil.copytree(args.scene.parent, private)
    import tkinter as tk
    from master_rallye.workshop.gui import WorkshopApp
    from validate_rally_workshop import screenshot
    root = tk.Tk(); errors = []
    root.report_callback_exception = lambda *error: errors.append(str(error))
    app = WorkshopApp(root, output / "ui-workspace", ROOT, viewer)
    app.open_source_garage(); window = app.source_garage_window
    window._open(private / "scene.json"); root.update()
    nodes_before = len(window.rows)
    window.preview()

    def settle():
        deadline = time.monotonic() + 45
        while app.busy and time.monotonic() < deadline:
            root.update(); time.sleep(.02)
        root.update()
        if app.busy or errors:
            raise AssertionError("Source Garage callback failure/timeout: " + str(errors))

    try:
        settle()
        if not window.photos or window.preview_path is None:
            raise AssertionError("Source Garage preview did not populate the real image widget")
        high = json.loads(window.preview_path.with_suffix(".json").read_text(encoding="utf-8"))
        window.wheel_detail.set("08"); window._populate(); window.preview(); settle()
        low = json.loads(window.preview_path.with_suffix(".json").read_text(encoding="utf-8"))
        high_wheel = sum(d["vertices"] for d in high["draws"] if d["role"] == "wheel")
        low_wheel = sum(d["vertices"] for d in low["draws"] if d["role"] == "wheel")
        if not high_wheel > low_wheel > 0:
            raise AssertionError("Retained source wheel detail selection did not change preview geometry")
        window.basis.set("source"); window.view.set("front"); window.save_choices()
        window.basis.set("normalized"); window.wheel_detail.set("16")
        window._open(private / "scene.json")
        if window.basis.get() != "source" or window.wheel_detail.get() != "08":
            raise AssertionError("Neutral scene reopen did not restore preview choices")
        # The original normal scene and all channel sidecars remain byte exact.
        load_scene(private / "scene.json")
        # Real UI entry path, using the qualified original source root and the
        # window's own fresh private workspace output; no file-dialog automation.
        window.source.set(scene["source"]["root"])
        window.inspect(); settle()
        window.create(); settle()
        created_root = window.scene_root
        if created_root == private or created_root is None or not (created_root / "manifest.json").is_file():
            raise AssertionError("Source Garage Create did not produce a separate neutral project")
        if app.project is not None:
            raise AssertionError("Source Garage changed the MR Workshop project selection")
        window.capture(); settle()
        for name, digest in original.items():
            if sha(read_bounded(args.scene.parent / name, 128 * 1024 * 1024)) != digest:
                raise AssertionError("Input neutral source project changed")
        screenshot(window.window, output / "source-garage-ui.png")
        report = {"schema": "source-garage-preview-validation/1", "status": "PASS",
                  "viewer_sha256": hashlib.sha256(viewer.read_bytes()).hexdigest(),
                  "preview_draws": len(staged["draws"]), "source_node_mesh_rows": nodes_before,
                  "high_detail_wheel_vertices": high_wheel, "low_detail_wheel_vertices": low_wheel,
                  "real_tk_image_preview": "PASS", "reopen_choices": "PASS", "input_source_project_unchanged": True,
                  "inspect_create_capture_ui_flow": "PASS", "created_source_project": str(created_root),
                  "max_normalization_error_m": max_normalization_error,
                  "max_roundtrip_error_source_units": max_roundtrip_error, "opacity_interpretation_geometry_unchanged": True,
                  "captures": captures, "source_basis_captures": source_basis_captures, "explicit_opacity_captures": interpreted_captures,
                  "boundary": "Application GPU/Tk qualification; source-game render parity and MR gameplay NOT TESTED"}
        (output / "validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
    finally:
        if window.window.winfo_exists(): window.close()
        app.close()


if __name__ == "__main__":
    main()
