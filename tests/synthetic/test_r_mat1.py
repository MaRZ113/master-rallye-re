"""Vehicle material branch coverage independent of Blender and resource names."""
import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from master_rallye.material_semantics import MaterialSemantics


def draw(slots=("body-tga", "rubber-tga", "Null"), flags=(0, 0, 1, 1), mask=7):
    return SimpleNamespace(texture_slots=[SimpleNamespace(slot=i, value=x) for i, x in enumerate(slots)],
                           flags_0x20=bytes(flags), unknown_0x24=mask, unknown_0x14=1,
                           unknown_0x18=0, unknown_0x1c_float=1.0)


class VehicleMaterialCloseoutTests(unittest.TestCase):
    def test_fixed_binding_never_promotes_null_slot0(self):
        sem = MaterialSemantics.from_draw(draw(("Null", "perspex-tga", "Null"), mask=6))
        self.assertFalse(sem.texture_stage_mapping["slot0"].bound)
        self.assertTrue(sem.texture_stage_mapping["slot1"].bound)
        self.assertEqual(sem.texture_stage_mapping["slot1"].d3d_stage, 1)
        self.assertFalse(sem.null_slot_behavior["promotion"])
        self.assertFalse(sem.null_slot_behavior["stage1_effective"])
        self.assertEqual(sem.runtime_shader_family, "shader/base_env")

    def test_textureless_diffuse_and_uv_flag(self):
        sem = MaterialSemantics.from_draw(draw(("Null",) * 3, (0, 0, 1, 0), 2))
        self.assertEqual(sem.runtime_shader_family, "shader/base")
        self.assertTrue(sem.vertex_diffuse_enabled)
        self.assertFalse(sem.source_uv_enabled)
        self.assertFalse(any(x.bound for x in sem.texture_stage_mapping.values()))

    def test_all_observed_masks_and_reflections_gate(self):
        for mask in (1, 2, 3, 5, 6, 7):
            slots = ("body" if mask & 1 else "Null", "env" if mask & 4 else "Null", "Null")
            for alpha, test in ((0, 0), (0, 1), (1, 0), (1, 1)):
                sem = MaterialSemantics.from_draw(draw(slots, (alpha, test, int(bool(mask & 2)), 1), mask))
                off = MaterialSemantics.from_draw(draw(slots, (alpha, test, int(bool(mask & 2)), 1), mask), reflections=False)
                suffix = "_alphatest" if alpha and test else "_alpha" if alpha else ""
                self.assertEqual(sem.classification, "CLASSIFIED")
                self.assertEqual(sem.runtime_shader_family, "shader/base" + ("_env" if mask & 4 else "") + suffix)
                self.assertEqual(off.runtime_shader_family, "shader/base" + suffix)
                self.assertFalse(off.texture_stage_mapping["slot1"].bound)
                self.assertEqual(off.texture_slots, slots)

    def test_base_alpha_states_and_instance_override_scope(self):
        sem = MaterialSemantics.from_draw(draw(("glass", "Null", "Null"), (1, 0, 1, 1), 3))
        self.assertFalse(sem.d3d8_render_states["ZWRITEENABLE"])
        self.assertFalse(sem.d3d8_render_states["ALPHATESTENABLE"])
        self.assertTrue(sem.d3d8_render_states["ALPHABLENDENABLE"])
        self.assertEqual(sem.d3d8_render_states["SRCBLEND"], "SRCALPHA")
        self.assertEqual(sem.d3d8_render_states["DESTBLEND"], "INVSRCALPHA")
        self.assertEqual(sem.render_state_scope["draw_overrides"]["ZWRITEENABLE"], "instance+0xA9")

    def test_alphatest_exact_greater_threshold(self):
        sem = MaterialSemantics.from_draw(draw(flags=(1, 1, 1, 1)))
        self.assertEqual(sem.d3d8_render_states["ALPHAFUNC"], "GREATER")
        self.assertEqual(sem.d3d8_render_states["ALPHAREF"], 128)
        self.assertFalse(sem.d3d8_render_states["ALPHABLENDENABLE"])

    def test_generic_stage1_is_filename_independent(self):
        for name in ("whitepaint", "chrome", "perspex", "rubber", "glass", "silverpaint", "lightshine", "lights", "new-helper"):
            sem = MaterialSemantics.from_draw(draw(("body", name, "Null")))
            self.assertEqual(sem.runtime_shader_family, "shader/base_env")
            self.assertEqual(sem.d3d8_texture_stage_states["stage1"]["COLOROP"], "MODULATEALPHA_ADDCOLOR")
            self.assertEqual(sem.d3d8_texture_stage_states["stage1"]["TEXCOORDINDEX"], 0x10000)

    def test_byte2_controls_vertex_diffuse_independently_of_alpha(self):
        for byte2 in (0, 1):
            sem = MaterialSemantics.from_draw(draw(flags=(1, 0, byte2, 1), mask=5 | byte2 * 2))
            self.assertEqual(sem.alpha_mode, "ALPHA_BLEND")
            self.assertEqual(sem.vertex_diffuse_enabled, bool(byte2))
            self.assertEqual(sem.runtime_flag_semantics["byte2"]["fvf_bit"], 0x40)

    def test_projection_does_not_mutate_raw_material(self):
        source = draw()
        before = deepcopy(vars(source))
        sem = MaterialSemantics.from_draw(source)
        json.loads(json.dumps(sem.to_dict()))
        self.assertEqual(vars(source), before)

    def test_unobserved_branches_have_explicit_unknown_reason(self):
        for source, reason in ((draw(mask=15), "FEATURES_OUTSIDE_RETAIL_VEHICLE_MASK_0x07"),
                               (draw(("body", "env", "third")), "SLOT2_USE_OUTSIDE_OBSERVED_VEHICLE_CORPUS"),
                               (draw(mask=4), "NO_OBSERVED_BASE_FAMILY_SELECTOR")):
            sem = MaterialSemantics.from_draw(source)
            self.assertEqual(sem.classification, "UNKNOWN")
            self.assertIn(reason, sem.unknown_reasons)
            self.assertIsNone(sem.runtime_shader_family)
            self.assertIsNone(sem.texture_combine_operations)
            self.assertIsNone(sem.texture_stage_mapping["slot0"].d3d_stage)
            self.assertEqual(sem.texture_stage_mapping["slot1"].confidence, "UNKNOWN")
        source = draw()
        source.unknown_0x18 = 1
        self.assertIn("OPTIONAL_RUNTIME_VARIANT_OBJECT", MaterialSemantics.from_draw(source).unknown_reasons)


if __name__ == "__main__":
    unittest.main()
