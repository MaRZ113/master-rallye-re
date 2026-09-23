"""R4G synthetic bounds, collision-scale and vehicle-project checks."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]

from master_rallye.bounds import compute_bounds1339, parse_bounds1339
from master_rallye.collision_scale import scale_dx_collision
from master_rallye.collision_writer import _polygon_area
from master_rallye.dx import parse_dx_bytes
from master_rallye.topology_writer import DrawGeometry, rebuild_topology, source_geometry
from master_rallye.vehicle_project import VehicleProject, validate_vehicle, build_vehicle_mod
from tests.synthetic.test_r4f import fixture


class R4GBoundsTests(unittest.TestCase):
    def test_marker_parse_compute_center_radius_and_zero_edit(self):
        data = fixture()
        model = parse_dx_bytes(data)
        bounds = model.collision.spatial_bounds_1339
        self.assertEqual(bounds.offset, model.collision.unparsed_offset)
        self.assertEqual((bounds.minimum, bounds.maximum), ((0., 0., 0.), (1., 1., 1.)))
        self.assertEqual(bounds.center, (.5, .5, .5))
        self.assertIsNone(parse_bounds1339(b"not-a-footer"))
        self.assertEqual(rebuild_topology(data, bounds_mode="recompute").data, data)
        recomputed = compute_bounds1339(model.vertices.positions)
        self.assertEqual(recomputed.center, bounds.center)
        self.assertGreaterEqual(recomputed.radius, max(math.dist(v, recomputed.center) for v in model.vertices.positions))

    def test_outside_donor_bounds_recomputes_only_footer_and_render_core(self):
        data = fixture(collision=True)
        model = parse_dx_bytes(data)
        geometry = source_geometry(model)[0]
        first = geometry.vertices
        new = tuple(replace(first[i], position=(first[i].position[0] + 1.5,
                      first[i].position[1], first[i].position[2]), source_vertex_id=None)
                    for i in (0, 1, 2))
        edited = DrawGeometry(first + new, geometry.triangles + ((4, 5, 6),))
        with self.assertRaisesRegex(Exception, "outside original bounds"):
            rebuild_topology(data, {0: edited})
        result = rebuild_topology(data, {0: edited}, bounds_mode="recompute")
        out = result.output_model
        self.assertEqual((out.vertex_count, out.triangle_count), (10, 4))
        self.assertGreater(out.collision.spatial_bounds_1339.maximum[0],
                           model.collision.spatial_bounds_1339.maximum[0])
        self.assertEqual(out.collision.convex_hull.raw, model.collision.convex_hull.raw)
        self.assertEqual(result.external_diff_count, 0)


class R4GCollisionTests(unittest.TestCase):
    def test_uniform_nonuniform_and_zero_scale(self):
        data = fixture(collision=True)
        source = parse_dx_bytes(data).collision.convex_hull
        self.assertEqual(scale_dx_collision(data, (1, 1, 1))["data"], data)
        for factors in ((1.2, 1.2, 1.2), (1.2, 1.0, .8)):
            result = scale_dx_collision(data, factors)
            self.assertEqual(result["unexpected_diff_count"], 0)
            new = parse_dx_bytes(result["data"]).collision.convex_hull
            self.assertEqual(new.representation_b.edges, source.representation_b.edges)
            self.assertEqual(new.representation_b.face_loop_indices, source.representation_b.face_loop_indices)
            self.assertEqual(new.representation_b.geometry_a.triangles,
                             source.representation_b.geometry_a.triangles)
            self.assertNotEqual(new.base_scalar, source.base_scalar)
            self.assertGreaterEqual(new.base_scalar, max(
                math.dist(v, new.base_geometry.vertices[0])
                for v in new.representation_a.geometry_a.vertices) - 2e-6)
            self.assertEqual(len(new.representation_b.face_scalars),
                             len(source.representation_b.face_scalars))
            detailed = new.representation_b.geometry_a.vertices
            aabb_min = tuple(min(v[i] for v in detailed) for i in range(3))
            aabb_max = tuple(max(v[i] for v in detailed) for i in range(3))
            corners = new.representation_a.geometry_a.vertices
            self.assertEqual(tuple(min(v[i] for v in corners) for i in range(3)), aabb_min)
            self.assertEqual(tuple(max(v[i] for v in corners) for i in range(3)), aabb_max)
            for geometry, helper in ((corners, new.representation_a.geometry_b.vertices[0]),
                                     (detailed, new.representation_b.geometry_b.vertices[0])):
                for axis in range(3):
                    self.assertAlmostEqual(helper[axis], sum(v[axis] for v in geometry) / len(geometry), places=5)
            for rep in (new.representation_a, new.representation_b):
                for scalar, face in zip(rep.face_scalars, rep.face_descriptors):
                    self.assertAlmostEqual(scalar, _polygon_area(rep.geometry_a.vertices, face.primary_indices), places=5)
        with self.assertRaisesRegex(Exception, "scale"):
            scale_dx_collision(data, (0, 1, 1))


class R4GProjectTests(unittest.TestCase):
    def test_validate_and_stage_only_changed_resource(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            vehicle = root / "Astero"
            vehicle.mkdir()
            source = fixture(collision=True)
            (vehicle / "car.dx").write_bytes(source)
            (vehicle / "complete.dx").write_bytes(fixture())
            # Both donor draws reference only body and glass.
            tex = struct.pack("<5I", 0xFEED, 0, 0, 1, 1) + bytes((0, 0, 0, 255))
            (vehicle / "body-tga.dxt").write_bytes(tex)
            (vehicle / "glass-tga.dxt").write_bytes(tex)
            model = parse_dx_bytes(source)
            geometry = source_geometry(model)[0]
            new = tuple(replace(geometry.vertices[i], position=(geometry.vertices[i].position[0] + 1.5,
                        geometry.vertices[i].position[1], geometry.vertices[i].position[2]),
                        source_vertex_id=None) for i in (0, 1, 2))
            candidate = rebuild_topology(source, {0: DrawGeometry(
                geometry.vertices + new, geometry.triangles + ((4, 5, 6),))},
                bounds_mode="recompute").data
            candidate_path = root / "candidate.dx"
            candidate_path.write_bytes(candidate)
            project_path = root / "project.json"
            project_path.write_text(json.dumps({
                "vehicle_name": "Astero", "source_vehicle_dir": str(vehicle),
                "resources": {"car.dx": {"source_sha256": hashlib.sha256(source).hexdigest(),
                                         "candidate": str(candidate_path)}}}), encoding="utf-8")
            project = VehicleProject.load(project_path)
            report = validate_vehicle(project)
            self.assertEqual(report["status"], "WARN")  # optional wheel absent
            self.assertEqual(set(report["compiled"]), {"car.dx"})
            built = build_vehicle_mod(project, root / "output")
            self.assertEqual(len(built["files"]), 1)
            staged = root / "output/staging/DataGx/Vehicles/Astero/car.dx"
            self.assertEqual(staged.read_bytes(), candidate)
            self.assertEqual((vehicle / "car.dx").read_bytes(), source)
            bad = json.loads(project_path.read_text(encoding="utf-8"))
            bad["resources"]["car.dx"]["source_sha256"] = "0" * 64
            project_path.write_text(json.dumps(bad), encoding="utf-8")
            self.assertEqual(validate_vehicle(VehicleProject.load(project_path))["status"], "FAIL")
            bad["resources"]["car.dx"]["unsupported_edit"] = True
            project_path.write_text(json.dumps(bad), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unsupported edit"):
                VehicleProject.load(project_path)


if __name__ == "__main__":
    unittest.main()
