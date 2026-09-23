from __future__ import annotations

import hashlib
import math
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
for directory in (ROOT/"src",ROOT/"tests"/"blender",ROOT/"tools"/"scanner"):
    sys.path.insert(0,str(directory))

from generate_fixture import build_dx
from master_rallye.dx import parse_dx_bytes
from master_rallye.r4e_writer import patch_dx_attributes
from r4e1_runtime_probes import rotate_source_y_90


class FocusedWriterAudit(unittest.TestCase):
    def setUp(self):
        self.template=build_dx()
        self.model=parse_dx_bytes(self.template)

    def test_normal_zero_edit_preserves_exact_bytes(self):
        patch=patch_dx_attributes(self.template,normals=self.model.vertices.normals)
        self.assertEqual(patch.data,self.template)
        self.assertEqual(patch.diff.changed_byte_count,0)
        self.assertEqual(patch.changes,())

    def test_90_degree_normal_rotation_length_and_authorized_spans(self):
        rotated=[rotate_source_y_90(value) for value in self.model.vertices.normals]
        patch=patch_dx_attributes(self.template,normals=rotated)
        output=parse_dx_bytes(patch.data)
        self.assertEqual(len(patch.changes),self.model.vertex_count)
        self.assertEqual({change.field for change in patch.changes},{"normal"})
        start=self.model.vertices.normal_offset
        end=self.model.vertices.color_offset
        self.assertTrue(all(start <= change.offset and change.offset+12 <= end for change in patch.changes))
        self.assertEqual(len(patch.diff.unexpected_ranges),0)
        for original,actual in zip(self.model.vertices.normals,output.vertices.normals):
            expected=rotate_source_y_90(original)
            self.assertEqual(actual,expected)
            self.assertAlmostEqual(math.sqrt(sum(x*x for x in original)),math.sqrt(sum(x*x for x in actual)),places=6)
        self.assertEqual(output.vertices.positions,self.model.vertices.positions)
        self.assertEqual(output.vertices.colors,self.model.vertices.colors)
        self.assertEqual([x.values for x in output.uv_sets],[x.values for x in self.model.uv_sets])
        self.assertEqual(output.local_indices,self.model.local_indices)
        self.assertEqual(output.collision.convex_hull.sha256,self.model.collision.convex_hull.sha256)
        self.assertEqual([draw.unknown_0x24 for draw in output.physical_draws],[draw.unknown_0x24 for draw in self.model.physical_draws])

    def test_env_disable_enable_one_byte_and_unknown_fields_preserved(self):
        # Replace the synthetic four-byte Null slot-1 name with an equally sized helper.
        original_draw=self.model.physical_draws[0]
        slot=original_draw.texture_slots[1]
        self.assertEqual(slot.raw,b"Null")
        source=bytearray(self.template)
        source[slot.data_offset:slot.data_offset+4]=b"envx"
        source=bytes(source)
        parsed=parse_dx_bytes(source)
        draw=parsed.physical_draws[0]
        self.assertEqual(draw.texture_tuple[1],"envx")
        self.assertEqual(draw.unknown_0x24,5)
        disabled=patch_dx_attributes(source,material_env={0:False})
        after=parse_dx_bytes(disabled.data)
        self.assertEqual(after.physical_draws[0].unknown_0x24,1)
        self.assertEqual(disabled.diff.changed_byte_count,1)
        self.assertEqual(len(disabled.diff.unexpected_ranges),0)
        self.assertEqual(disabled.changes[0].field,"material_env_bit")
        self.assertEqual(disabled.changes[0].offset,draw.core_offset+0x24)
        self.assertEqual(draw.texture_tuple,after.physical_draws[0].texture_tuple)
        self.assertEqual(draw.flags_0x20,after.physical_draws[0].flags_0x20)
        self.assertEqual(draw.unknown_0x14,after.physical_draws[0].unknown_0x14)
        self.assertEqual(draw.unknown_0x18,after.physical_draws[0].unknown_0x18)
        self.assertEqual(parsed.vertices,after.vertices)
        self.assertEqual(parsed.collision.convex_hull.sha256,after.collision.convex_hull.sha256)
        enabled=patch_dx_attributes(disabled.data,material_env={0:True})
        self.assertEqual(enabled.data,source)
        self.assertEqual(enabled.diff.changed_byte_count,1)
        with self.assertRaisesRegex(Exception,"slot-1 helper"):
            patch_dx_attributes(self.template,material_env={0:False})


if __name__=="__main__":
    unittest.main()
