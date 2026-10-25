"""Regression coverage for the native selector truth table and visible cutout depth behavior."""
import tempfile
import unittest
from pathlib import Path

from master_rallye.dx import parse_dx_bytes
from master_rallye.r4e_writer import patch_dx_attributes, DxWriteError
from tools import vmesh_geometry as geo, vmesh_materials as vm, vmesh_lod0 as lod, vmesh_raster as raster, vmesh_fitment as fitment
from tests.synthetic.test_vmesh_geometry import DONOR_DIR, HAVE_DONOR, _png
from tests.synthetic.test_vmesh_lod0 import write_assets
from tests.synthetic.test_vmesh_materials import SPECIAL, RESERVED


class RasterTests(unittest.TestCase):
    def test_tyre_outline_tests_actual_shape_rather_than_only_vertical_radius(self):
        hull = [(0, -2), (1, 0), (0, 2), (-1, 0)]
        self.assertGreater(fitment.outline_depth((0, 1.5), hull), 0)
        self.assertLess(fitment.outline_depth((1.1, 0), hull), 0)

    def test_alpha_test_discards_clear_texels_without_painting_black_or_hiding_behind(self):
        tri = ((-1, 0, 0), (1, 0, 0), (0, 2, 0), (0, 0), (0, 0), (0, 0),
               (255, 255, 255), (255, 255, 255), (255, 255, 255))
        tex = (1, 1, bytes((0, 0, 0, 0)))
        cam = raster.Camera(az=180, el=0, scale=12, centre=(0, 1, 0))
        broken = raster.render([raster.DrawItem("V44 inert selector", [tri], tex)], cam, 32, 32)
        fixed = raster.render([raster.DrawItem("cutout", [tri], tex, alpha_test=True)], cam, 32, 32)
        background = bytes((196, 200, 204)) * 32 * 32
        self.assertNotEqual(broken, background)
        self.assertEqual(fixed, background)


@unittest.skipUnless(HAVE_DONOR, "retail donor unavailable")
class NativeMaterialTests(unittest.TestCase):
    def test_serialized_alpha_test_requires_alpha_enable_gate(self):
        source = (DONOR_DIR / "complete.dx").read_bytes()
        with self.assertRaisesRegex(DxWriteError, "requires alpha enable"):
            patch_dx_attributes(source, material_alpha={4: False}, material_alpha_test={4: True})
        result = patch_dx_attributes(source, material_alpha={4: True}, material_alpha_test={4: True})
        self.assertEqual(tuple(parse_dx_bytes(result.data).physical_draws[4].flags_0x20[:2]), (1, 1))

    def test_paint_panel_nonzero_alpha_is_coverage_while_glazing_stays_translucent(self):
        with tempfile.TemporaryDirectory() as tmp:
            obj = write_assets(Path(tmp))
            (Path(tmp) / "paint.png").write_bytes(_png(8, 8, lambda x, y: (20, 30, 200, 65)))
            gt = geo.parse_gt_full(obj)
            cl = lod.Lod0Classifier(gt["faces"], gt["textures"])
            donor = {n: (DONOR_DIR / n).read_bytes() for n in ("car.dx", "complete.dx")}
            plan = vm.MaterialPlan(gt["faces"], gt["textures"], cl, 1, donor, DONOR_DIR, SPECIAL, RESERVED,
                                   structural_coverage=True)
            self.assertEqual(set(plan.textures["Mat1_Tex0"].alpha), {255})
            self.assertEqual(set(plan.textures["Mat6_Tex37"].alpha), {230})
            for fi, (obj_name, _, _) in enumerate(gt["faces"]):
                if obj_name == "body":
                    self.assertEqual(plan.routes[fi][1][1].pass_, "opaque")

    def test_radial_growth_does_not_require_tyre_width_growth(self):
        source = (DONOR_DIR / "wheel.dx").read_bytes()
        result, _ = geo.build_wheel_candidate(source, 0.98, lateral_scale=0.88)
        model = parse_dx_bytes(result)
        old = parse_dx_bytes(source)
        for a, b in zip(old.vertices.positions, model.vertices.positions):
            self.assertAlmostEqual(b[0], a[0] * 0.88, places=6)
            self.assertAlmostEqual(b[1], a[1] * 0.98, places=6)
            self.assertAlmostEqual(b[2], a[2] * 0.98, places=6)
