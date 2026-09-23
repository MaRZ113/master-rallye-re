from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from master_rallye.material_semantics import MaterialSemantics, texture_presence_mask


def draw(slots, flags, mask):
    return SimpleNamespace(
        texture_slots=[SimpleNamespace(slot=i, value=value) for i, value in enumerate(slots)],
        flags_0x20=bytes(flags), unknown_0x24=mask,
        unknown_0x14=17, unknown_0x18=23, unknown_0x1c_float=0.5,
    )


class R4D1MaterialTests(unittest.TestCase):
    def test_texture_mask_all_presence_combinations(self):
        for slots, base in (
            (("Null", "Null", "Null"), 0),
            (("a-tga", "Null", "Null"), 1),
            (("Null", "b-tga", "Null"), 4),
            (("a-tga", "b-tga", "Null"), 5),
        ):
            for flag2 in (0, 1):
                self.assertEqual(texture_presence_mask(slots, flag2), base | flag2 * 2)

    def test_flag2_nonzero_sets_mask_bit_without_changing_presence(self):
        self.assertEqual(texture_presence_mask(("Null", "Null", "Null"), 255), 2)
        with self.assertRaises(ValueError):
            texture_presence_mask(("a", "b"), 0)

    def test_alpha_mapping_and_metadata_are_serializable(self):
        cases = (
            ((0, 0, 1, 1), "OPAQUE", False, False),
            ((1, 0, 1, 1), "ALPHA_BLEND", True, False),
            ((1, 1, 1, 1), "ALPHA_TEST", True, True),
        )
        for flags, mode, enabled, test in cases:
            item = MaterialSemantics.from_draw(draw(("body-tga", "glass-tga", "Null"), flags, 7))
            value = json.loads(json.dumps(item.to_dict()))
            self.assertEqual(value["texture_slots"], ["body-tga", "glass-tga", "Null"])
            self.assertEqual(value["serialized_draw_flags"], bytes(flags).hex())
            self.assertEqual(value["serialized_texture_mask"], 7)
            self.assertEqual(value["runtime_feature_mask"], 7)
            self.assertEqual(value["alpha_mode"], mode)
            self.assertEqual(value["alpha_enabled"], enabled)
            self.assertEqual(test, value["d3d8_render_states"]["ALPHATESTENABLE"])
            self.assertIsNone(value["texture_stage_mapping"])
            self.assertIsNone(value["texture_combine_operations"])
            self.assertIsNone(value["runtime_shader_family"])
            self.assertEqual(value["unknown_fields"]["unknown_0x14"], 17)


if __name__ == "__main__":
    unittest.main()
