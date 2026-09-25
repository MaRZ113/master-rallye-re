import struct
import unittest

from master_rallye.errors import BoundsError, FormatError
from master_rallye.gxm_hierarchy import find_nodes, parse_gxm_hierarchy_tail, walk_depth_first


def _record(name, start, count, children=(), *, node_type=1, version=1):
    encoded = name.encode("ascii")
    return (struct.pack("<BBHIIH", node_type, version, len(children), start, count, len(encoded))
            + encoded + b"".join(children))


class GxmHierarchyTests(unittest.TestCase):
    def test_parses_mesh_nodes_and_depth_first_loader_order(self):
        data = (struct.pack("<H", 5) + b"Model"
                + _record("shell", 0, 2, (
                    _record("interior", 2, 1, (_record("driver", 3, 4),)),
                    _record("paint $paint", 7, 8),
                ))
                + _record("$chull(Trooper)", 15, 68))
        tree = parse_gxm_hierarchy_tail(data, 0)
        self.assertEqual(tree.root_name, "Model")
        self.assertEqual(tree.node_count, 5)
        self.assertEqual([n.name for n in walk_depth_first(tree.roots)],
                         ["shell", "interior", "driver", "paint $paint", "$chull(Trooper)"])
        hull, = find_nodes(tree.roots, "$chull(Trooper)")
        self.assertEqual((hull.mesh_start, hull.mesh_count, hull.child_count), (15, 68, 0))
        self.assertEqual(hull.node_type, 1)
        self.assertEqual(hull.version, 1)

    def test_name_offsets_and_record_offsets_are_absolute(self):
        tail = struct.pack("<H", 5) + b"Model" + _record("mesh", 4, 5)
        data = b"prefix" + tail
        parsed = parse_gxm_hierarchy_tail(data, len(b"prefix"))
        node, = parsed.roots
        self.assertEqual(node.record_offset, 13)
        self.assertEqual(node.name_offset, 25)

    def test_rejects_unsupported_layout_and_non_model_root(self):
        for tail in (
            struct.pack("<H", 4) + b"Root" + _record("mesh", 0, 1),
            struct.pack("<H", 5) + b"Model" + _record("mesh", 0, 1, node_type=0),
            struct.pack("<H", 5) + b"Model" + _record("mesh", 0, 1, version=2),
        ):
            with self.subTest(tail=tail):
                with self.assertRaises(FormatError):
                    parse_gxm_hierarchy_tail(tail, 0)

    def test_rejects_truncated_node_and_trailing_child_count(self):
        truncated = struct.pack("<H", 5) + b"Model" + struct.pack("<BBHII", 1, 1, 0, 0, 1)
        with self.assertRaises(BoundsError):
            parse_gxm_hierarchy_tail(truncated, 0)
        bad_child = struct.pack("<H", 5) + b"Model" + struct.pack("<BBHIIH", 1, 1, 1, 0, 1, 4) + b"root"
        with self.assertRaises(BoundsError):
            parse_gxm_hierarchy_tail(bad_child, 0)

    def test_bounded_tail_does_not_consume_following_bytes(self):
        tail = struct.pack("<H", 5) + b"Model" + _record("mesh", 1, 2)
        data = tail + b"unrelated"
        tree = parse_gxm_hierarchy_tail(data, 0, tail_size=len(tail))
        self.assertEqual(tree.consumed_size, len(tail))
        with self.assertRaises((FormatError, BoundsError)):
            parse_gxm_hierarchy_tail(data, 0)


class GxmRuntimeMappingTests(unittest.TestCase):
    def test_runtime_binding_slots_and_sibling_links(self):
        from master_rallye.gxm_hierarchy import runtime_node_bindings
        data = (struct.pack("<H", 5) + b"Model"
                + _record("parent", 0, 1, (_record("left", 1, 1), _record("right", 2, 1)))
                + _record("tail", 3, 1))
        tree = parse_gxm_hierarchy_tail(data, 0)
        bindings = {entry.node.name: entry for entry in runtime_node_bindings(tree.roots)}
        left = bindings["left"]
        self.assertEqual((left.parent_name, left.previous_sibling_name, left.next_sibling_name),
                         ("parent", None, "right"))
        self.assertEqual((left.child_pointer_offset, left.sibling_pointer_offset,
                          left.parent_pointer_offset, left.name_pointer_offset,
                          left.mesh_start_offset, left.mesh_count_offset),
                         (0x04, 0x08, 0x0C, 0x14, 0x1C, 0x20))
        self.assertEqual(bindings["parent"].next_sibling_name, "tail")

    def test_serialized_c_triangle_stream_keeps_record_and_corner_order(self):
        from master_rallye.gxm_hierarchy import serialized_c_triangle_stream
        records = bytearray(3 * 52)
        for record, indices in enumerate(((10, 11, 12), (12, 11, 13), (99, 98, 97))):
            struct.pack_into("<3I", records, record * 52 + 16, *indices)
        stream = serialized_c_triangle_stream(bytes(records), 0, 3, 0, 2)
        self.assertEqual([(item.record_index, item.c_indices) for item in stream],
                         [(0, (10, 11, 12)), (1, (12, 11, 13))])

    def test_serialized_c_triangle_stream_rejects_out_of_range_mesh_span(self):
        from master_rallye.gxm_hierarchy import serialized_c_triangle_stream
        with self.assertRaises(FormatError):
            serialized_c_triangle_stream(bytes(52), 0, 1, 1, 1)


class GxmTailBoundTests(unittest.TestCase):
    def test_root_and_node_names_must_fit_bounded_tail(self):
        root_name = struct.pack("<H", 5) + b"Model"
        with self.assertRaises(BoundsError):
            parse_gxm_hierarchy_tail(root_name + b"suffix", 0, tail_size=4)
        record = struct.pack("<BBHIIH", 1, 1, 0, 0, 1, 8) + b"nameMORE"
        with self.assertRaises(BoundsError):
            parse_gxm_hierarchy_tail(root_name + record, 0, tail_size=len(root_name) + 16)


if __name__ == "__main__":
    unittest.main()
