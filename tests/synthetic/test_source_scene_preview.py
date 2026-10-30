"""UVS preview transform/texture integrity and UI interpretation boundaries."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from master_rallye.source_scene_preview import IDENTITY, stage_source_scene, viewer_command
from master_rallye.workshop.source_garage_ui import preview_configuration


def scene_fixture(root):
    project = root / "source-project"; project.mkdir()
    (root / "original-donor").mkdir()
    raw = bytes([3, 7, 11, 127]); (project / "texture.rgba").write_bytes(raw)
    parent = IDENTITY.copy(); parent[3] = 2
    child = IDENTITY.copy(); child[7] = 3
    basis = IDENTITY.copy(); basis[10] = -1
    scene = {"schema": "universal-vehicle-scene/1", "source": {"root": str(root / "original-donor")},
             "metadata": {"display_name": "Synthetic source vehicle"}, "unknown_semantics": [{"type": "reflection", "status": "UNKNOWN"}],
             "coordinate_system": {"source_to_normalized": basis, "interpretation_status": "synthetic", "evidence": ["test fixture"]},
             "textures": [{"id": "texture", "width": 1, "height": 1, "rgba_path": "texture.rgba", "rgba_sha256": hashlib.sha256(raw).hexdigest(), "source_channels": {"mode": "RGBA"}}],
             "materials": [{"id": "material", "diffuse_texture_id": "texture", "raw_fields": ["1", "1", "64", "1", "1", "test.TIF"],
                            "flags": {"transparent_raw": "1", "reflective_raw": "1"}, "unsupported": ["runtime reflection"]}],
             "meshes": [{"id": "body", "name": "Body", "positions": [[0, 0, 1], [1, 0, 1], [0, 1, 1]],
                         "normals": [[0, 0, 1]] * 3, "uvs": [[0, 0], [1, 0], [0, 1]], "triangles": [[0, 1, 2]],
                         "material_id": "material", "source": {"member_sha256": "0" * 64}, "animation_frames": []}],
             "nodes": [{"id": "parent", "name": "Assembly", "mesh_ids": [], "parent_id": None, "local_transform": parent,
                        "source_local_transform": None, "visible": True, "source_visible": True, "role": "body", "transform_evidence": "fixture"},
                       {"id": "child", "name": "Body", "mesh_ids": ["body"], "parent_id": "parent", "local_transform": child,
                        "source_local_transform": None, "visible": True, "source_visible": True, "role": "body", "transform_evidence": "fixture"}]}
    return project, scene


def read_first_draw(path):
    data = path.read_bytes(); offset = 40
    def string():
        nonlocal offset
        n, = struct.unpack_from("<I", data, offset); offset += 4
        raw = data[offset:offset+n]; offset += n; return raw.decode()
    textures = []
    _, _, nt, nd = struct.unpack_from("<4sIII", data)
    for _ in range(nt):
        name = string(); w, h = struct.unpack_from("<II", data, offset); offset += 8
        pixels = data[offset:offset + w*h*4]; offset += w*h*4; textures.append((name, pixels))
    name = string(); header = struct.unpack_from("<Iii4I3fII", data, offset); offset += 48
    nv, ni = header[-2:]
    vertices = [struct.unpack_from("<6f4B2f", data, offset + i*36) for i in range(nv)]
    offset += nv*36; indices = struct.unpack_from(f"<{ni}I", data, offset)
    return textures, name, header, vertices, indices


class SourceScenePreviewTests(unittest.TestCase):
    def test_native_capture_explicitly_selects_race_instead_of_default_frontend(self):
        from unittest.mock import patch
        from PIL import Image
        from master_rallye.source_scene_preview import capture_views
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);scene=root/'x.mrpv';scene.write_bytes(b'synthetic')
            commands=[]
            def fake_run(command,**kwargs):
                commands.append(command)
                Image.new('RGB',(8,8)).save(command[command.index('--capture')+1])
            with patch('master_rallye.source_scene_preview.subprocess.run',side_effect=fake_run):
                report=capture_views(Path('viewer.exe'),scene,root/'captures',model='race')
            self.assertEqual(report['model'],'race')
            self.assertEqual(len(commands),6)
            self.assertTrue(all(c[c.index('--model')+1]=='race'for c in commands))

    def test_normalized_parent_transform_winding_normals_and_raw_rgba(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); project, scene = scene_fixture(root); before = copy.deepcopy(scene)
            output = root / "preview.mrpv"
            report = stage_source_scene(scene, output, scene_root=project)
            textures, name, header, vertices, indices = read_first_draw(output)
            self.assertEqual(textures[0][1], bytes([11, 7, 3, 127]))
            self.assertEqual(vertices[0][:3], (2, 3, -1))
            self.assertEqual(vertices[0][3:6], (0, 0, -1))
            self.assertEqual(indices, (0, 2, 1))
            self.assertEqual(header[:4], (0, 0, -1, 1))
            self.assertTrue(report["draws"][0]["winding_reversed"])
            self.assertEqual(scene, before)
            self.assertEqual((project / "texture.rgba").read_bytes(), bytes([3, 7, 11, 127]))

    def test_source_basis_preserves_raw_units_and_triangle_order(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); project, scene = scene_fixture(root)
            output = root / "preview.mrpv"; stage_source_scene(scene, output, scene_root=project, basis="source")
            _, _, _, vertices, indices = read_first_draw(output)
            self.assertEqual(vertices[0][:3], (2, 3, 1)); self.assertEqual(indices, (0, 1, 2))

    def test_interpreted_opacity_is_explicit_copy_original_stays_untouched(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); project, scene = scene_fixture(root)
            interpreted = preview_configuration(scene, {"opacity_overrides": {"material": .25}})
            self.assertNotIn("preview", scene["materials"][0])
            original = root / "original.mrpv"; altered = root / "altered.mrpv"
            stage_source_scene(interpreted, original, scene_root=project, material_mode="original")
            stage_source_scene(interpreted, altered, scene_root=project, material_mode="interpreted")
            self.assertEqual(read_first_draw(original)[3][0][9], 255)
            self.assertEqual(read_first_draw(altered)[3][0][9], 64)

    def test_selected_visibility_does_not_destroy_retained_source_objects(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); project, scene = scene_fixture(root); scene["nodes"][1]["visible"] = False
            with self.assertRaises(ValueError):
                stage_source_scene(scene, root / "selected.mrpv", scene_root=project)
            report = stage_source_scene(scene, root / "source.mrpv", scene_root=project, visibility="source")
            self.assertEqual(len(report["draws"]), 1)
            self.assertFalse(scene["nodes"][1]["visible"])

    def test_sidecar_hash_and_traversal_fail_without_output(self):
        for mutation in ("hash", "path"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); project, scene = scene_fixture(root)
                if mutation == "hash": scene["textures"][0]["rgba_sha256"] = "0" * 64
                else: scene["textures"][0]["rgba_path"] = "../escape.rgba"
                with self.assertRaises(ValueError):
                    stage_source_scene(scene, root / "preview.mrpv", scene_root=project)
                self.assertFalse((root / "preview.mrpv").exists())

    def test_invalid_mesh_index_and_cycle_rejected_before_writes(self):
        for mutation in ("index", "cycle"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); project, scene = scene_fixture(root)
                if mutation == "index": scene["meshes"][0]["triangles"] = [[0, 1, 9]]
                else: scene["nodes"][0]["parent_id"] = "child"
                with self.assertRaises(ValueError):
                    stage_source_scene(scene, root / "preview.mrpv", scene_root=project)
                self.assertFalse((root / "preview.mrpv").exists())

    def test_output_cannot_replace_source_project_original_donor_or_prior_preview(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); project, scene = scene_fixture(root)
            (project / "scene.json").write_text("immutable", encoding="utf-8")
            other = root / "another-donor"; other.mkdir()
            scene["source"]["protected_roots"] = [str(other)]
            for output in (project / "scene.mrpv", root / "original-donor/preview.mrpv", other / "preview.mrpv"):
                with self.assertRaises(ValueError):
                    stage_source_scene(scene, output, scene_root=project)
            self.assertEqual((project / "scene.json").read_text(), "immutable")
            output = root / "preview.mrpv"; stage_source_scene(scene, output, scene_root=project); before = output.read_bytes()
            with self.assertRaises(ValueError):
                stage_source_scene(scene, output, scene_root=project)
            self.assertEqual(output.read_bytes(), before)

    def test_viewer_commands_cannot_trigger_mr_resource_exporter_and_preserve_axis_labels(self):
        for basis, sign in (("normalized", "negative-z"), ("source", "positive-z")):
            command = viewer_command(Path("viewer.exe"), Path("scene.mrpv"), view="front", basis=basis)
            self.assertIn("--neutral-source", command); self.assertIn("--orthographic", command)
            self.assertEqual(command[command.index("--source-front") + 1], sign)
            self.assertNotIn("--source", command); self.assertNotIn("--exporter", command)
        with self.assertRaises(ValueError):
            viewer_command(Path("viewer.exe"), Path("scene.mrpv"), view="arbitrary")

    def test_unknown_or_nonfinite_opacity_does_not_mutate_source(self):
        scene = {"materials": [{"id": "one"}]}
        for overrides in ({"unknown": .5}, {"one": float("nan")}, {"one": -1}):
            with self.assertRaises(ValueError):
                preview_configuration(scene, {"opacity_overrides": overrides})
        self.assertEqual(scene, {"materials": [{"id": "one"}]})

    def test_wheel_detail_selects_retained_meshes_without_changing_transforms_or_original(self):
        with tempfile.TemporaryDirectory() as temp:
            _, scene = scene_fixture(Path(temp))
            low = copy.deepcopy(scene["meshes"][0]); low["id"] = "wheel-low"
            scene["meshes"].append(low)
            scene["nodes"][1].update(role="wheel", wheel_slot="faxle.ltire")
            scene["wheel_variants"] = {"08L": {"mesh_ids": ["wheel-low"]}, "08R": {"mesh_ids": ["wheel-low"]},
                                       "16L": {"mesh_ids": ["body"]}, "16R": {"mesh_ids": ["body"]}}
            result = preview_configuration(scene, {"wheel_detail": "08"})
            self.assertEqual(result["nodes"][1]["mesh_ids"], ["wheel-low"])
            self.assertEqual(result["selection"]["wheel_lod_index"], 0)
            self.assertEqual(scene["nodes"][1]["mesh_ids"], ["body"])
            self.assertEqual(result["nodes"][1]["local_transform"], scene["nodes"][1]["local_transform"])
            with self.assertRaises(ValueError):
                preview_configuration(scene, {"wheel_detail": "12"})


if __name__ == "__main__":
    unittest.main()
