from __future__ import annotations

import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for item in (ROOT, ROOT / "src"):
    if str(item) not in sys.path:
        sys.path.insert(0, str(item))

from master_rallye.course_gxm import parse_course_gxm_model_v7_bytes
from master_rallye.course_sdk import load_course_project
from master_rallye.course_source import parse_course_txt_bytes
from master_rallye.errors import BoundsError, FormatError


BOX_TRIANGLES = (
    (0, 2, 3), (3, 1, 0), (4, 5, 7), (7, 6, 4),
    (0, 1, 5), (5, 4, 0), (1, 3, 7), (7, 5, 1),
    (3, 2, 6), (6, 7, 3), (2, 0, 4), (4, 6, 2),
)
BOX_POINTS = (
    (-5., -5., -5.), (5., -5., -5.), (-5., 5., -5.), (5., 5., -5.),
    (-5., -5., 5.), (5., -5., 5.), (-5., 5., 5.), (5., 5., 5.),
)
BOX_NORMALS = (
    (0., 0., -1.), (0., 0., 1.), (0., -1., 0.),
    (1., 0., 0.), (0., 1., 0.), (-1., 0., 0.),
)


def make_v7_gxm(*, position_index_override: tuple[int, int] | None = None,
                normal_index_override: tuple[int, int] | None = None,
                mesh_start: int = 0, mesh_size: int = 12, version: int = 7,
                zero_mesh: bool = False) -> tuple[bytes, bytes]:
    extra = "  moMesh(Name [empty] Index 0 Size 0)\n" if zero_mesh else ""
    txt = (f"moModel(Name [Model])\n  moMesh(Name [startpoint] Index {mesh_start} Size {mesh_size})\n"
           + extra).encode()
    name = b"Model"
    node_name = b"startpoint"
    table = bytearray(struct.pack("<H", len(name)) + name)
    table += struct.pack("<BBHIIH", 1, 1, 0, mesh_start, mesh_size, len(node_name)) + node_name
    if zero_mesh:
        empty_name = b"empty"
        table += struct.pack("<BBHIIH", 1, 1, 0, 0, 0, len(empty_name)) + empty_name
    triangles = bytearray()
    for triangle_id, position_indices in enumerate(BOX_TRIANGLES):
        normal_indices = (triangle_id * 3, triangle_id * 3 + 1, triangle_id * 3 + 2)
        if position_index_override and triangle_id == position_index_override[0]:
            mutable = list(position_indices)
            mutable[position_index_override[1]] = 8
            position_indices = tuple(mutable)
        if normal_index_override and triangle_id == normal_index_override[0]:
            mutable = list(normal_indices)
            mutable[normal_index_override[1]] = 36
            normal_indices = tuple(mutable)
        color_indices = (0, 1, 2)
        if triangle_id == 0:
            color_indices = (0, 0xFFFFFFFF, 2)
        material_index = 0xFFFFFFFF if triangle_id == 1 else 0
        texcoord_indices = (0, 1, 2)
        triangles += struct.pack(
            "<13I", *color_indices, material_index, *texcoord_indices,
            *position_indices, *normal_indices,
        )
    face_normals = []
    for normal in BOX_NORMALS:
        face_normals.extend((normal, normal, normal, normal, normal, normal))
    counts = (0, 4, 1, 36, 3, 12, 8)
    header = struct.pack("<8I", ((1 + int(zero_mesh)) << 16) | (version << 8) | 2, *counts)
    colors = struct.pack("<16f", *(1.0 for _ in range(16)))
    materials = b"\x11\x22\x33\x44"
    normals = b"".join(struct.pack("<3f", *item) for item in face_normals)
    texcoords = struct.pack("<9f", 0., 0., .5, 1., 0., .5, 0., 1., .5)
    positions = b"".join(struct.pack("<3f", *item) for item in BOX_POINTS)
    return header + colors + materials + normals + texcoords + triangles + positions + bytes(table), txt


def topology_proof(model, node_name: str):
    node = model.find_mesh(node_name)
    indices = model.mesh_position_indices(node)
    unique = tuple(sorted(set(indices)))
    points = tuple(model.position(index) for index in unique)
    edges = {}
    for triangle_index in model.mesh_triangle_indices(node):
        a, b, c = model.triangle(triangle_index).position_indices
        for edge in ((a, b), (b, c), (c, a)):
            key = tuple(sorted(edge))
            edges[key] = edges.get(key, 0) + 1
    edge_histogram = {}
    for count in edges.values():
        edge_histogram[count] = edge_histogram.get(count, 0) + 1
    return node, unique, points, edge_histogram


class R5TE1CourseGxmTopologyTests(unittest.TestCase):
    def setUp(self):
        self.data, self.txt = make_v7_gxm()
        self.document = parse_course_txt_bytes(self.txt, "synthetic.txt")
        self.model = parse_course_gxm_model_v7_bytes(self.data, self.document, "cube.gxm")

    def test_packed_object_header_and_seven_model_count_words(self):
        self.assertEqual((self.model.object_class, self.model.version, self.model.child_count), (2, 7, 1))
        self.assertEqual(self.model.counts, (0, 4, 1, 36, 3, 12, 8))

    def test_fixed_bank_offsets_and_triangle_record_grammar(self):
        self.assertEqual([bank.offset for bank in (
            self.model.colors, self.model.materials, self.model.normals,
            self.model.texcoords, self.model.triangles, self.model.positions,
        )], [32, 96, 100, 532, 568, 1192])
        self.assertEqual((self.model.triangles.stride, self.model.triangles.count), (52, 12))
        first = self.model.triangle(0)
        self.assertEqual(first.color_indices, (0, 0xFFFFFFFF, 2))
        self.assertEqual(first.material_index, 0)
        self.assertEqual(first.texcoord_indices, (0, 1, 2))
        self.assertEqual(first.position_indices, (0, 2, 3))
        self.assertEqual(first.normal_indices, (0, 1, 2))
        self.assertEqual(self.model.triangle(1).material_index, 0xFFFFFFFF)

    def test_independent_reference_domains_and_sentinel_rules(self):
        self.assertTrue(self.model.validation.passed)
        self.assertEqual(self.model.validation.domain("color")["sentinel_count"], 1)
        self.assertEqual(self.model.validation.domain("material")["sentinel_count"], 1)
        for name in ("texcoord", "position", "normal"):
            self.assertEqual(self.model.validation.domain(name)["out_of_range_count"], 0)

    def test_mesh_span_slice_and_closed_box_proof(self):
        node, unique, points, edge_histogram = topology_proof(self.model, "startpoint")
        self.assertEqual((node.mesh_index, node.mesh_size), (0, 12))
        self.assertEqual(unique, tuple(range(8)))
        self.assertEqual(len(points), 8)
        self.assertEqual(edge_histogram, {2: 18})
        bounds = tuple((min(p[i] for p in points), max(p[i] for p in points)) for i in range(3))
        self.assertEqual(tuple(high - low for low, high in bounds), (10., 10., 10.))

    def test_normal_pool_resolves_to_six_axis_face_directions(self):
        observed = tuple(tuple(round(v, 5) for v in self.model.normal(i)) for i in range(36))
        groups = {}
        for item in observed:
            groups[item] = groups.get(item, 0) + 1
        self.assertEqual(set(groups.values()), {6})
        self.assertEqual(len(groups), 6)

    def test_unsupported_version_is_rejected_without_guessing(self):
        bad, _ = make_v7_gxm(version=8)
        with self.assertRaisesRegex(FormatError, "only version 7"):
            parse_course_gxm_model_v7_bytes(bad, self.document)

    def test_truncated_bank_and_invalid_attribute_indices_are_rejected(self):
        with self.assertRaises((BoundsError, FormatError)):
            parse_course_gxm_model_v7_bytes(self.data[:-100], self.document)
        bad_position, _ = make_v7_gxm(position_index_override=(0, 0))
        with self.assertRaisesRegex(FormatError, "position"):
            parse_course_gxm_model_v7_bytes(bad_position, self.document)
        bad_normal, _ = make_v7_gxm(normal_index_override=(0, 0))
        with self.assertRaisesRegex(FormatError, "normal"):
            parse_course_gxm_model_v7_bytes(bad_normal, self.document)

    def test_color_material_and_texcoord_domains_reject_non_sentinel_overflow(self):
        triangle_offset = self.model.triangles.offset
        for field, invalid_value, label in ((0, 4, "color"), (3, 1, "material"), (4, 3, "texcoord")):
            with self.subTest(domain=label):
                bad = bytearray(self.data)
                struct.pack_into("<I", bad, triangle_offset + field * 4, invalid_value)
                with self.assertRaisesRegex(FormatError, label):
                    parse_course_gxm_model_v7_bytes(bytes(bad), self.document)

    def test_out_of_range_mesh_span_is_rejected(self):
        txt = b"moModel(Name [Model])\n  moMesh(Name [startpoint] Index 12 Size 1)\n"
        document = parse_course_txt_bytes(txt)
        data, _ = make_v7_gxm(mesh_start=12, mesh_size=1)
        with self.assertRaisesRegex(BoundsError, "exceeds triangle count"):
            parse_course_gxm_model_v7_bytes(data, document)

    def test_no_writer_surface_is_exposed_by_topology_model(self):
        self.assertFalse(any("write" in name.casefold() for name in dir(self.model)))

    def test_zero_size_mesh_span_is_supported(self):
        data, txt = make_v7_gxm(zero_mesh=True)
        model = parse_course_gxm_model_v7_bytes(data, parse_course_txt_bytes(txt))
        empty = model.find_mesh("empty")
        self.assertEqual(empty.mesh_size, 0)
        self.assertEqual(len(model.mesh_triangle_indices(empty)), 0)

    def test_read_only_course_sdk_exposes_literal_source_meshes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data, txt = make_v7_gxm()
            (root / "model.gxm").write_bytes(data)
            (root / "model.txt").write_bytes(txt)
            project = load_course_project(root / "model.gxm")
        self.assertIsNotNone(project.source_geometry)
        self.assertEqual(len(project.source_meshes), 1)
        mesh = project.source_meshes[0]
        self.assertEqual(mesh.literal_name, "startpoint")
        self.assertEqual(mesh.hierarchy_path, ("Model", "startpoint"))
        self.assertEqual(mesh.triangle_count, 12)
        self.assertEqual(len(mesh.unique_position_indices), 8)
        self.assertEqual(mesh.triangle_position_triplets[0], (0, 2, 3))
        self.assertEqual(mesh.resolved_positions, tuple(self.model.position(index) for index in range(8)))
        self.assertEqual(mesh.unique_positions, mesh.resolved_positions)
        self.assertEqual(mesh.gameplay_role, "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
