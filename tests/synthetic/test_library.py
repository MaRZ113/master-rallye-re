from __future__ import annotations

import json
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from master_rallye.assets import AssetResolver
from master_rallye.dx import MAGIC as DX_MAGIC, MAX_VERTICES, parse_dx, parse_dx_bytes
from master_rallye.dxt import (
    MAGIC as DXT_MAGIC,
    PNG_ROWS_FLIP_VERTICAL,
    PNG_ROWS_PRESERVE_STORED,
    encode_png,
    parse_dxt_bytes,
)
from master_rallye.errors import BoundsError, FormatError, UnknownRecordTagError
from master_rallye.export.gltf import export_gltf, transform_uv_values
from master_rallye.materials import select_preview_binding
from master_rallye.sidecar import apply_material_candidates, parse_sidecar

sys.path.insert(0, str(ROOT / "tools" / "scanner"))
import inventory as inventory_scanner


def simple_record(base, local_max, index_start, index_count, textures=("synthetic-tga", "Null")):
    record = bytearray(struct.pack(
        "<7If4BI", 2, base, local_max, index_start, index_count,
        1, 0, 1.0, 0, 0, 0, 1, 5,
    ))
    record += struct.pack("<I", len(textures))
    for value in textures:
        encoded = value.encode("ascii")
        record += struct.pack("<I", len(encoded)) + encoded
    record += struct.pack("<I", 0)
    return bytes(record)


def tag8_record(core_record, controls=(2, 1)):
    return struct.pack("<3I", 8, *controls) + core_record


def tag7_record(label, core_record, child_count, controls=(2, 2, 8, 1)):
    encoded = label.encode("ascii")
    return (
        struct.pack("<2I", 7, len(encoded))
        + encoded
        + struct.pack("<5I", *controls, child_count)
        + core_record
    )


def footer56(positions):
    minimum = tuple(min(value[axis] for value in positions) for axis in range(3))
    maximum = tuple(max(value[axis] for value in positions) for axis in range(3))
    midpoint = tuple((a + b) / 2 for a, b in zip(minimum, maximum))
    return struct.pack("<IffI3ff6f", 102, 0.4, 0.2, 1339, *midpoint, 1.0, *minimum, *maximum)


def synthetic_dx(
    positions,
    local_indices,
    flat_records,
    draw_metas,
    uv_sets=None,
    declared_count=None,
    stored_override=None,
    trailing=b"",
    include_global=True,
):
    if uv_sets is None:
        uv_sets = [[(index / max(1, len(positions) - 1), 0.25) for index in range(len(positions))]]
    blob = bytearray(struct.pack("<4I", DX_MAGIC, 135, 1337, len(positions)))
    for value in positions:
        blob += struct.pack("<3f", *value)
    for _ in positions:
        blob += struct.pack("<3f", 0.0, 1.0, 0.0)
    blob += bytes((10, 20, 30, 255)) * len(positions)
    blob += struct.pack("<I", len(uv_sets))
    for uv_set in uv_sets:
        for value in uv_set:
            blob += struct.pack("<2f", *value)
    blob += struct.pack("<I", len(local_indices))
    if local_indices:
        blob += struct.pack(f"<{len(local_indices)}H", *local_indices)
    blob += struct.pack("<2I", 1, declared_count if declared_count is not None else len(flat_records))
    for record in flat_records:
        blob += record
    reconstructed = [None] * len(local_indices)
    for base, start, count in draw_metas:
        raw = local_indices[start:start + count]
        for relative in range(0, len(raw), 3):
            triangle = (raw[relative + 1] + base, raw[relative] + base, raw[relative + 2] + base)
            reconstructed[start + relative:start + relative + 3] = triangle
    stored = list(stored_override) if stored_override is not None else [int(value) for value in reconstructed]
    if include_global:
        blob += struct.pack("<2I", 1, len(stored))
        if stored:
            blob += struct.pack(f"<{len(stored)}I", *stored)
    blob += trailing
    return bytes(blob)


class DxLibraryTests(unittest.TestCase):
    def setUp(self):
        self.positions = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]

    def test_tag2_addressing_winding_and_texture_slots(self):
        record = simple_record(0, 2, 0, 3, ("body-tga", "chrome-tga", "Null"))
        model = parse_dx_bytes(synthetic_dx(self.positions, [0, 1, 2], [record], [(0, 0, 3)]))
        draw = model.physical_draws[0]
        self.assertEqual(draw.tag, 2)
        self.assertEqual(model.draw_global_indices(draw), (1, 0, 2))
        self.assertEqual(draw.texture_tuple, ("body-tga", "chrome-tga", "Null"))
        self.assertTrue(model.global_index_table.reconstructed_match)
        self.assertTrue(model.diagnostics.validated)

    def test_tag7_group_and_tag8_child(self):
        parent = tag7_record("screen", simple_record(0, 2, 0, 3), 1)
        child = tag8_record(simple_record(3, 2, 3, 3))
        positions = [(float(index), 0.0, 0.0) for index in range(6)]
        model = parse_dx_bytes(synthetic_dx(
            positions, [0, 1, 2, 0, 1, 2], [parent, child],
            [(0, 0, 3), (3, 3, 3)], declared_count=1,
        ))
        self.assertEqual([draw.tag for draw in model.physical_draws], [7, 8])
        self.assertEqual(model.draw_groups[0].root.group_label, "screen")
        self.assertEqual(model.draw_groups[0].draw_indices, [0, 1])
        self.assertEqual(model.draw_groups[0].root.children[0].record_path, "0.1")

    def test_multiple_and_no_uv_sets(self):
        record = simple_record(0, 2, 0, 3, ("Null",))
        uv_sets = [
            [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)],
            [(0.1, 0.2), (0.3, 0.4), (0.5, 0.6)],
        ]
        multi = parse_dx_bytes(synthetic_dx(self.positions, [0, 1, 2], [record], [(0, 0, 3)], uv_sets=uv_sets))
        none = parse_dx_bytes(synthetic_dx(self.positions, [0, 1, 2], [record], [(0, 0, 3)], uv_sets=[]))
        self.assertEqual(len(multi.uv_sets), 2)
        self.assertEqual(multi.uv_sets[1].values[2], (0.5, 0.6000000238418579))
        self.assertEqual(none.uv_sets, [])
        self.assertTrue(none.diagnostics.validated)

    def test_ambiguous_sidecar_material_matching(self):
        record = simple_record(0, 2, 0, 3, ("body-tga", "Null"))
        model = parse_dx_bytes(synthetic_dx(self.positions, [0, 1, 2], [record], [(0, 0, 3)]))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.txt"
            path.write_text(
                "Materials(Size 2)\n"
                "Material number [ 0] has name [One]\nTexture [ 0] Name[Body.tga]\n"
                "Material number [ 1] has name [Two]\nTexture [ 0] Name[body.tga]\n",
                encoding="latin-1",
            )
            sidecar = parse_sidecar(path)
        apply_material_candidates(model.physical_draws, sidecar)
        self.assertEqual([item.name for item in model.physical_draws[0].material_candidates], ["One", "Two"])

    def test_missing_sidecar_does_not_affect_binary_parse(self):
        record = simple_record(0, 2, 0, 3)
        model = parse_dx_bytes(synthetic_dx(self.positions, [0, 1, 2], [record], [(0, 0, 3)]))
        apply_material_candidates(model.physical_draws, None)
        self.assertEqual(model.physical_draws[0].material_candidates, [])
        self.assertTrue(model.diagnostics.validated)

    def test_missing_texture_is_diagnostic(self):
        record = simple_record(0, 2, 0, 3, ("missing-tga", "Null"))
        model = parse_dx_bytes(synthetic_dx(self.positions, [0, 1, 2], [record], [(0, 0, 3)]))
        with tempfile.TemporaryDirectory() as directory:
            binding = select_preview_binding(model.physical_draws[0], AssetResolver(Path(directory)))
        self.assertTrue(binding.missing_texture)
        self.assertIsNone(binding.texture_path)

    def test_malformed_length_prefixed_string(self):
        record = bytearray(simple_record(0, 2, 0, 3))
        struct.pack_into("<I", record, 44, 5000)
        blob = synthetic_dx(self.positions, [0, 1, 2], [bytes(record)], [(0, 0, 3)])
        with self.assertRaisesRegex(FormatError, "unreasonable length"):
            parse_dx_bytes(blob)

    def test_unknown_record_tag_has_evidence(self):
        record = struct.pack("<I", 99) + b"\0" * 64
        blob = synthetic_dx(self.positions, [0, 1, 2], [record], [(0, 0, 3)])
        with self.assertRaises(UnknownRecordTagError) as captured:
            parse_dx_bytes(blob, "unknown.dx")
        self.assertEqual(captured.exception.evidence.tag, 99)
        self.assertEqual(captured.exception.evidence.source, "unknown.dx")
        self.assertTrue(captured.exception.evidence.context_hex)

    def test_absent_global_table_at_eof_is_parseable(self):
        record = simple_record(0, 2, 0, 3)
        model = parse_dx_bytes(synthetic_dx(
            self.positions, [0, 1, 2], [record], [(0, 0, 3)], include_global=False
        ))
        self.assertIsNone(model.global_index_table)
        self.assertFalse(model.diagnostics.validated)
        self.assertTrue(any("absent" in warning for warning in model.diagnostics.warnings))

    def test_truncated_global_index_table(self):
        record = simple_record(0, 2, 0, 3)
        blob = synthetic_dx(self.positions, [0, 1, 2], [record], [(0, 0, 3)])[:-4]
        with self.assertRaisesRegex(BoundsError, "global index array"):
            parse_dx_bytes(blob)

    def test_global_index_mismatch_is_validation_error(self):
        record = simple_record(0, 2, 0, 3)
        model = parse_dx_bytes(synthetic_dx(
            self.positions, [0, 1, 2], [record], [(0, 0, 3)], stored_override=[0, 1, 2]
        ))
        self.assertFalse(model.diagnostics.validated)
        self.assertFalse(model.global_index_table.reconstructed_match)
        self.assertTrue(any("differ" in message for message in model.diagnostics.errors))

    def test_opaque_trailing_data_is_preserved(self):
        record = simple_record(0, 2, 0, 3)
        model = parse_dx_bytes(synthetic_dx(
            self.positions, [0, 1, 2], [record], [(0, 0, 3)], trailing=b"opaque-data"
        ))
        self.assertEqual(model.trailing.data, b"opaque-data")
        self.assertEqual(model.trailing.layout_family, "opaque")
        self.assertTrue(model.diagnostics.validated)

    def test_recognized_footer56(self):
        record = simple_record(0, 2, 0, 3)
        model = parse_dx_bytes(synthetic_dx(
            self.positions, [0, 1, 2], [record], [(0, 0, 3)], trailing=footer56(self.positions)
        ))
        self.assertEqual(model.trailing.layout_family, "footer56-bounds")
        self.assertTrue(model.trailing.bounding.matches_positions)
        self.assertEqual(model.trailing.bounding.minimum, (0.0, 0.0, 0.0))

    def test_unused_vertices_are_diagnostic_not_parse_failure(self):
        positions = self.positions + [(9.0, 9.0, 9.0)]
        record = simple_record(0, 2, 0, 3)
        model = parse_dx_bytes(synthetic_dx(positions, [0, 1, 2], [record], [(0, 0, 3)]))
        self.assertTrue(model.diagnostics.validated)
        self.assertEqual(model.diagnostics.vertex_coverage, "unused")
        self.assertEqual(model.diagnostics.unused_vertex_count, 1)

    def test_shared_vertex_ranges_are_diagnostic_not_parse_failure(self):
        positions = [(float(index), 0.0, 0.0) for index in range(4)]
        records = [simple_record(0, 2, 0, 3), simple_record(1, 2, 3, 3)]
        model = parse_dx_bytes(synthetic_dx(
            positions, [0, 1, 2, 0, 1, 2], records, [(0, 0, 3), (1, 3, 3)]
        ))
        self.assertTrue(model.diagnostics.validated)
        self.assertEqual(model.diagnostics.vertex_coverage, "shared")
        self.assertEqual(model.diagnostics.shared_vertex_count, 2)

    def test_structurally_valid_synthetic_gltf(self):
        record = simple_record(0, 2, 0, 3, ("Null",))
        model = parse_dx_bytes(synthetic_dx(self.positions, [0, 1, 2], [record], [(0, 0, 3)]), "synthetic.dx")
        with tempfile.TemporaryDirectory() as directory:
            result = export_gltf(model, Path(directory), flip_v=True)
            document = json.loads(result.gltf_path.read_text(encoding="utf-8"))
            binary = result.bin_path.read_bytes()
        self.assertEqual(document["asset"]["version"], "2.0")
        self.assertEqual(document["buffers"][0]["byteLength"], len(binary))
        self.assertEqual(len(document["meshes"][0]["primitives"]), 1)
        primitive = document["meshes"][0]["primitives"][0]
        self.assertIn("POSITION", primitive["attributes"])
        self.assertIn("NORMAL", primitive["attributes"])
        self.assertIn("TEXCOORD_0", primitive["attributes"])
        self.assertIn("COLOR_0", primitive["attributes"])
        self.assertLess(primitive["indices"], len(document["accessors"]))

    def test_bounds_errors_are_section_specific(self):
        cases = {
            "DX header": b"\x0d\xd0",
            "position section": struct.pack("<4I", DX_MAGIC, 135, 1337, 2) + b"\0" * 12,
            "UV set 0": struct.pack("<4I", DX_MAGIC, 135, 1337, 1) + b"\0" * 28 + struct.pack("<I", 1) + b"\0" * 4,
            "local index array": struct.pack("<4I", DX_MAGIC, 135, 1337, 1) + b"\0" * 28 + struct.pack("<I", 0) + struct.pack("<I", 3) + b"\0\0",
        }
        for expected, blob in cases.items():
            with self.subTest(expected=expected), self.assertRaisesRegex(BoundsError, expected):
                parse_dx_bytes(blob)

    def test_unreasonable_count_is_rejected(self):
        blob = struct.pack("<4I", DX_MAGIC, 135, 1337, MAX_VERTICES + 1)
        with self.assertRaisesRegex(FormatError, "unreasonable vertex count"):
            parse_dx_bytes(blob)


def png_scanlines(png: bytes) -> bytes:
    offset = 8
    idat = bytearray()
    while offset < len(png):
        length = struct.unpack_from(">I", png, offset)[0]
        kind = png[offset + 4:offset + 8]
        payload = png[offset + 8:offset + 8 + length]
        if kind == b"IDAT":
            idat.extend(payload)
        offset += length + 12
    return zlib.decompress(idat)


class DxtLibraryTests(unittest.TestCase):
    def test_bgra_to_rgba_channel_conversion(self):
        bgra = bytes((0, 0, 255, 255, 255, 0, 0, 128))
        texture = parse_dxt_bytes(struct.pack("<5I", DXT_MAGIC, 1, 7, 2, 1) + bgra)
        png = encode_png(texture, row_policy=PNG_ROWS_PRESERVE_STORED)
        self.assertEqual(png_scanlines(png), bytes((0, 255, 0, 0, 255, 0, 0, 255, 128)))

    def test_raw_stored_rows_are_preserved_and_png_rows_are_explicit(self):
        # Stored row 0: red, green. Stored row 1: blue, yellow. Every corner differs.
        stored_bgra = bytes((
            0, 0, 255, 255,    0, 255, 0, 255,
            255, 0, 0, 255,    0, 255, 255, 255,
        ))
        texture = parse_dxt_bytes(
            struct.pack("<5I", DXT_MAGIC, 1, 99, 2, 2) + stored_bgra,
            "asymmetric-rows.dxt",
        )
        self.assertEqual(texture.bgra, stored_bgra)

        preserve = png_scanlines(encode_png(texture, row_policy=PNG_ROWS_PRESERVE_STORED))
        flipped = png_scanlines(encode_png(texture, row_policy=PNG_ROWS_FLIP_VERTICAL))
        default = png_scanlines(encode_png(texture))
        stored_row_0 = bytes((0, 255, 0, 0, 255, 0, 255, 0, 255))
        stored_row_1 = bytes((0, 0, 0, 255, 255, 255, 255, 0, 255))
        self.assertEqual(preserve, stored_row_0 + stored_row_1)
        self.assertEqual(flipped, stored_row_1 + stored_row_0)
        self.assertEqual(default, flipped)

    def test_uv_v_transform_is_independent_of_png_rows(self):
        values = ((0.125, 0.2), (0.875, 0.7))
        self.assertEqual(transform_uv_values(values, False), values)
        flipped = transform_uv_values(values, True)
        self.assertAlmostEqual(flipped[0][0], 0.125)
        self.assertAlmostEqual(flipped[0][1], 0.8)
        self.assertAlmostEqual(flipped[1][0], 0.875)
        self.assertAlmostEqual(flipped[1][1], 0.3)


class ScannerRegressionTests(unittest.TestCase):
    def test_inventory_ignores_root_siblings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            expected = []
            for name in inventory_scanner.EXPECTED_ROOTS:
                child = root / name
                child.mkdir()
                path = child / f"{name}.bin"
                path.write_bytes(name.encode("ascii"))
                expected.append(path)
            outsider = root / "master_rallye_data_sma_tree.txt"
            outsider.write_text("not part of the archive", encoding="ascii")
            self.assertEqual(set(inventory_scanner.collect_paths(root)), set(expected))
            self.assertNotIn(outsider, inventory_scanner.collect_paths(root))


if __name__ == "__main__":
    unittest.main()
