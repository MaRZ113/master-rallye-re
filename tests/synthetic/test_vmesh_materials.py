"""Tests for the V-MESH4.2 material planner, alpha-toggle validation and mapping verification (synthetic input, real Navara donor)."""
import tempfile
import unittest
from pathlib import Path

from tools import gtmat
from tools import vmesh_geometry as geo
from tools import vmesh_lod0 as l0
from tools import vmesh_materials as vm
from tests.synthetic.test_vmesh_geometry import AXLES, DONOR_DIR, HAVE_DONOR
from tests.synthetic.test_vmesh_lod0 import write_assets

RESERVED = {"car.dx": {1, 2, 3, 9, 16, 17, 18, 19, 20, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36},
            "complete.dx": {3, 9, 16, 20, 21, 22, 23, 24, 25}}
SPECIAL = {"glass": {"car.dx": 35, "complete.dx": 24}, "head_lamp": {"car.dx": 25, "complete.dx": 25},
           "tail_lamp": {"car.dx": 24, "complete.dx": 16}}


@unittest.skipUnless(HAVE_DONOR, "unpacked retail Navara donor not available")
class PlannerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.obj = write_assets(Path(cls.tmp.name))
        cls.donor = {n: (DONOR_DIR / n).read_bytes() for n in ("car.dx", "complete.dx", "wheel.dx")}
        cls.ctx = geo.make_context(cls.donor["car.dx"], cls.donor["complete.dx"], cls.donor["wheel.dx"])
        cls.gplan = geo.plan_fit(cls.ctx, AXLES, 0.29, lift=0.12)
        cls.gt = geo.parse_gt_full(cls.obj)
        cls.cl = l0.Lod0Classifier(cls.gt["faces"], cls.gt["textures"])
        cls.mp = vm.MaterialPlan(cls.gt["faces"], cls.gt["textures"], cls.cl, cls.gplan.scale, cls.donor, DONOR_DIR, SPECIAL, RESERVED)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def face(self, obj):
        return next(i for i, (o, m, t) in enumerate(self.gt["faces"]) if o == obj)

    def test_pool_discovery_excludes_reserved_and_shared_textures(self):
        cands = {c["name"]: c for c in vm.discover_pools({n: self.donor[n] for n in ("car.dx", "complete.dx")}, DONOR_DIR, RESERVED)}
        self.assertEqual(cands["sidenav1-tga"]["draws"], {"car.dx": 4, "complete.dx": 4})
        self.assertEqual((cands["sidenav1-tga"]["width"], cands["sidenav1-tga"]["height"]), (128, 128))
        self.assertEqual(cands["frontwa-tga"]["draws"], {"car.dx": 22, "complete.dx": 18})   # differing indices per file
        for banned in ("black-tga", "colour-tga", "windscreen32-tga", "headlamp-tga", "backlightjnavp-tga", "xhelmet32-tga", "nevwheel-tga"):
            self.assertNotIn(banned, cands)

    def test_clear_decals_dropped_lone_overlay_kept_flat_trim_to_black_draw(self):
        self.assertEqual(self.mp.routes[self.face("decal")][0], "drop")           # footprint is fully transparent
        self.assertEqual(self.mp.routes[self.face("trim")][0], "black")           # flat dark opaque -> donor trim texture
        self.assertEqual(self.mp.routes[self.face("cabin")][0], "black")

    def test_special_roles_keep_their_donor_draws_and_get_remapped_uvs(self):
        for obj, role in (("pane", "glass"), ("lampL", "head_lamp"), ("shape17_tail_lamp_off", "tail_lamp")):
            fi = self.face(obj)
            target, uvs = self.mp.route(fi, self.gt["faces"][fi][2], role)
            self.assertEqual(target, role)
            self.assertTrue(all(0.0 <= u <= 1.0 and 0.0 <= v <= 1.0 for u, v in uvs))

    def test_opaque_paint_goes_to_an_opaque_pool_and_blend_pools_get_alpha_toggles(self):
        fi = self.face("body")
        target, uvs = self.mp.route(fi, self.gt["faces"][fi][2], "paint")
        self.assertTrue(target.startswith("pool:"))
        pool = next(p for p in self.mp.pools if p.role == target)
        self.assertEqual(pool.pass_, "opaque")
        for f, toggles in self.mp.alpha_toggles.items():
            for draw in toggles:
                self.assertIn(draw, [p.draws[f] for p in self.mp.pools if p.pass_ == "blend"]
                              + [p.draws[f] for p in self.mp.pools if p.role == "head_lamp"])
        for f, toggles in self.mp.alpha_test_toggles.items():
            for draw in toggles:
                self.assertIn(draw, [p.draws[f] for p in self.mp.pools if getattr(p, "alpha_test", False)]
                              + [p.draws[f] for p in self.mp.pools if p.role == "head_lamp"])
                self.assertTrue(self.mp.alpha_toggles[f].get(draw, False))

    def test_build_with_plan_validates_toggles_alpha_and_maps_back_to_the_source(self):
        import hashlib
        from master_rallye.dx import parse_dx_bytes
        from master_rallye.r4e_writer import patch_dx_attributes
        from master_rallye.vehicle_project import _topology_candidate
        smap = []
        data, rep = geo.build_candidate(self.obj, self.donor["complete.dx"], self.ctx, self.gplan, "complete",
                                        geo.BuildOptions(arch="native"), classifier=self.cl, source_map=smap, material_plan=self.mp)
        toggles = dict(self.mp.alpha_toggles["complete.dx"])
        test_toggles = dict(self.mp.alpha_test_toggles["complete.dx"])
        if toggles or test_toggles:
            data = patch_dx_attributes(data, material_alpha=toggles, material_alpha_test=test_toggles).data
        detail = _topology_candidate(self.donor["complete.dx"], data, "complete.dx")
        self.assertEqual(sorted(t["draw"] for t in detail["alpha_toggles"]), sorted(set(toggles) | set(test_toggles)))
        model = parse_dx_bytes(data)
        for d in toggles:
            self.assertEqual(model.physical_draws[d].flags_0x20[0], toggles[d])
        for d in test_toggles:
            self.assertEqual(model.physical_draws[d].flags_0x20[1], test_toggles[d])
        tp, _ = self.gplan.transform(self.ctx, "complete")
        verdict = l0.verify_source_map(data, smap, self.gt["faces"], tp)
        self.assertEqual(verdict["mismatches"], 0)
        # source UVs are preserved in the map, the DX UVs are the remapped ones
        self.assertTrue(all(e["corners"][0]["uv"] is not None for e in smap))
        self.assertTrue(any(e.get("dx_uv") for e in smap))

    def test_validator_still_rejects_other_material_changes(self):
        from master_rallye.dx import parse_dx_bytes
        from master_rallye.vehicle_project import _topology_candidate
        data, rep = geo.build_candidate(self.obj, self.donor["complete.dx"], self.ctx, self.gplan, "complete",
                                        geo.BuildOptions(arch="native"), classifier=self.cl, material_plan=self.mp)
        model = parse_dx_bytes(data)
        tampered = bytearray(data)
        tampered[model.physical_draws[4].core_offset + 0x24] ^= 4          # feature mask: must stay locked
        with self.assertRaises(ValueError):
            _topology_candidate(self.donor["complete.dx"], bytes(tampered), "complete.dx")

    def test_mapping_verification_on_decoded_pool_images(self):
        images = self.mp.pool_images()
        decoded = {name: (w, h, px) for name, (w, h, px) in images.items()}
        result = vm.verify_material_mapping(self.mp, self.gt["faces"], decoded)
        self.assertGreater(result["triangles_checked"], 0)
        self.assertEqual(result["opaque_pool_triangles_with_transparent_footprint"], 0)
        self.assertLess(result["mean_colour_error"], 12)

    def test_reflection_normalization_changes_alpha_without_changing_opaque_draw_pass(self):
        opaque = [p for p in self.mp.pools if p.pass_ == "opaque"]
        self.assertTrue(opaque)
        images = self.mp.pool_images()
        expected = int(255 * 0.58 + 0.5)
        for pool in opaque:
            pixels = images[pool.name + ".dxt"][2]
            self.assertEqual(set(pixels[3::4]), {expected})
        lamp = next(p for p in self.mp.pools if p.role == "head_lamp")
        self.assertEqual(lamp.alpha_scale, 0.72)

    def test_alpha_test_pools_preserve_binary_holes_and_reflection_attenuation(self):
        expected = int(255 * self.mp.body_reflection_scale + 0.5)
        class Island:
            alpha_test = True
        px = bytearray()
        for a in (0, 128, 129, 255):
            px.extend((10, 20, 30, a))
        vm.apply_alpha_test_mask(px, 4, 1, [(Island(), 0, 0, 4, 1)], expected)
        self.assertEqual(list(px[3::4]), [0, 0, expected, expected])

    def test_reflection_scales_are_range_checked(self):
        with self.assertRaises(ValueError):
            vm.MaterialPlan(self.gt["faces"], self.gt["textures"], self.cl, self.gplan.scale, self.donor,
                            DONOR_DIR, SPECIAL, RESERVED, body_reflection_scale=1.01)


if __name__ == "__main__":
    unittest.main()
