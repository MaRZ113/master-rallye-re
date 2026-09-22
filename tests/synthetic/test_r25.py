from __future__ import annotations

import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from master_rallye.audit import audit_vehicle_textures
from master_rallye.dxt import (
    MAGIC as DXT_MAGIC,
    PNG_ROWS_FLIP_VERTICAL,
    decode_rgba_pixels,
    encode_dxt_pixels,
    parse_dxt_bytes,
    replace_dxt_pixels,
)
from master_rallye.errors import BoundsError
from master_rallye.sidecar import parse_sidecar, resolve_sidecar

from tests.synthetic.test_library import simple_record, synthetic_dx
from master_rallye.dx import parse_dx_bytes


def write_sidecar(path: Path, texture: str, *, flags: str = "", mesh_size: int = 1) -> None:
    path.write_text(
        "Materials(Size 1)\n"
        "Material number [ 0] has name [Synthetic]\n"
        f"Texture [ 0] {flags}Name[{texture}]\n"
        f"moMesh(Name [mesh] Index 0 Size {mesh_size})\n",
        encoding="latin-1",
    )


class DxtWriterTests(unittest.TestCase):
    def setUp(self):
        # Stored bottom row: red/transparent green; stored top row: blue/yellow.
        self.header = struct.pack("<5I", DXT_MAGIC, 0x11223344, 0x55667788, 2, 2)
        self.stored = bytes((
            0, 0, 255, 255, 0, 255, 0, 17,
            255, 0, 0, 128, 0, 255, 255, 64,
        ))
        self.texture = parse_dxt_bytes(self.header + self.stored, "asymmetric.dxt")

    def test_decode_encode_is_byte_exact_and_preserves_header(self):
        upright = decode_rgba_pixels(self.texture, PNG_ROWS_FLIP_VERTICAL)
        rebuilt = encode_dxt_pixels(
            self.texture, upright, 2, 2, row_policy=PNG_ROWS_FLIP_VERTICAL
        )
        self.assertEqual(rebuilt, self.header + self.stored)
        self.assertEqual(rebuilt[:20], self.header)

    def test_channels_rows_and_alpha_are_independently_visible(self):
        upright = decode_rgba_pixels(self.texture)
        self.assertEqual(
            upright,
            bytes((
                0, 0, 255, 128, 255, 255, 0, 64,
                255, 0, 0, 255, 0, 255, 0, 17,
            )),
        )
        rebuilt = replace_dxt_pixels(self.texture, upright, 2, 2)
        self.assertEqual(rebuilt[20:], self.stored)
        self.assertEqual(rebuilt[23::4], bytes((255, 17, 128, 64)))

    def test_dimension_and_payload_mismatches_are_rejected(self):
        upright = decode_rgba_pixels(self.texture)
        with self.assertRaisesRegex(ValueError, "dimensions"):
            encode_dxt_pixels(self.texture, upright, 1, 4)
        with self.assertRaisesRegex(BoundsError, "payload size"):
            encode_dxt_pixels(self.texture, upright[:-1], 2, 2)


class SidecarEvidenceTests(unittest.TestCase):
    def model(self, source: str = "wheel.dx"):
        positions = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
        record = simple_record(0, 2, 0, 3, ("body-tga", "Null"))
        return parse_dx_bytes(
            synthetic_dx(positions, [0, 1, 2], [record], [(0, 0, 3)]),
            source,
        )

    def test_txt_flags_preserve_false_true_and_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "flags.txt"
            write_sidecar(
                path,
                "body.tga",
                flags="HasAlpha [No] UsesAlpha [Yes] IsNoise [No] ",
            )
            parsed = parse_sidecar(path)
            texture = parsed.materials[0].textures[0]
            self.assertIs(texture.has_alpha, False)
            self.assertIs(texture.uses_alpha, True)
            self.assertIs(texture.is_noise, False)

            missing = Path(directory) / "missing.txt"
            write_sidecar(missing, "body.tga")
            texture = parse_sidecar(missing).materials[0].textures[0]
            self.assertIsNone(texture.has_alpha)
            self.assertIsNone(texture.uses_alpha)
            self.assertIsNone(texture.is_noise)

    def test_exact_stem_wins_when_evidence_is_equal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_sidecar(root / "wheel.txt", "body.tga")
            write_sidecar(root / "other.txt", "body.tga")
            result = resolve_sidecar(self.model(), root)
            self.assertEqual(result.selected_path.name, "wheel.txt")
            self.assertFalse(result.ambiguous)

    def test_strong_texture_evidence_beats_wrong_exact_stem(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_sidecar(root / "wheel.txt", "wrong.tga")
            write_sidecar(root / "ForesterWheel.txt", "body.tga")
            result = resolve_sidecar(self.model(), root)
            self.assertEqual(result.selected_path.name, "ForesterWheel.txt")
            self.assertGreater(result.candidates[0].score, result.candidates[1].score)

    def test_different_scores_choose_best_and_equal_scores_remain_ambiguous(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_sidecar(root / "one.txt", "body.tga")
            write_sidecar(root / "two.txt", "wrong.tga")
            result = resolve_sidecar(self.model(), root)
            self.assertEqual(result.selected_path.name, "one.txt")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_sidecar(root / "one.txt", "body.tga")
            write_sidecar(root / "two.txt", "body.tga")
            result = resolve_sidecar(self.model(), root)
            self.assertIsNone(result.selected_path)
            self.assertTrue(result.ambiguous)

    def test_no_candidate_and_malformed_candidate_are_not_selected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = resolve_sidecar(self.model(), Path(directory))
            self.assertIsNone(result.selected_path)
            self.assertEqual(result.candidates, [])

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "wheel.txt").write_text("not a sidecar\n", encoding="latin-1")
            result = resolve_sidecar(self.model(), root)
            self.assertIsNone(result.selected_path)
            self.assertTrue(result.candidates[0].malformed)


class TextureAuditTests(unittest.TestCase):
    def test_read_only_reference_audit_distinguishes_unreferenced_and_missing(self):
        positions = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
        record = simple_record(0, 2, 0, 3, ("body-tga", "missing-tga", "Null"))
        blob = synthetic_dx(positions, [0, 1, 2], [record], [(0, 0, 3)])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "car.dx").write_bytes(blob)
            write_sidecar(root / "car.txt", "body.tga")
            (root / "body-tga.dxt").write_bytes(b"reference-only")
            (root / "red-beta.dxt").write_bytes(b"reference-only")
            result = audit_vehicle_textures(root)

        self.assertEqual(result["dx_referenced"], ["body-tga", "missing-tga"])
        self.assertEqual(result["txt_referenced"], ["body-tga"])
        self.assertEqual(result["apparently_unreferenced"], ["red-beta.dxt"])
        self.assertEqual(result["missing_referenced_resources"], ["missing-tga"])
        self.assertEqual(result["candidate_alternative_or_beta"], ["red-beta.dxt"])

if __name__ == "__main__":
    unittest.main()
