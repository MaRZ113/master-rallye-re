import math
import unittest

from tools.scanner.r_demo2_7_hull_divergence import (
    CORPUS_ID,
    EXE_SHA256,
    compare_endpoint_graphs,
    deterministic_json,
    endpoint_identity_graph,
    plane_equivalent,
    pointer_to_index,
    validate_pinned_gxm_hashes,
    validate_runtime_capture,
    walk_circular_ring,
)


class RuntimeStructureTests(unittest.TestCase):
    def test_pointer_to_index_checks_exact_range_and_alignment(self):
        self.assertEqual(pointer_to_index(0x1040, 0x1000, 0x1100, 0x20), 2)
        with self.assertRaisesRegex(ValueError, "outside vector"):
            pointer_to_index(0x1100, 0x1000, 0x1100, 0x20)
        with self.assertRaisesRegex(ValueError, "aligned"):
            pointer_to_index(0x1044, 0x1000, 0x1100, 0x20)
        with self.assertRaisesRegex(ValueError, "stride multiple"):
            pointer_to_index(0x1040, 0x1000, 0x1101, 0x20)

    def test_walks_circular_ring_and_checks_count(self):
        memory = {
            0x100: (0x200, 0x300, 0xDEADBEEF),
            0x200: (0x300, 0x100, 0xA001),
            0x300: (0x100, 0x200, 0xA002),
        }
        self.assertEqual(walk_circular_ring(memory, 0x100, expected_count=2),
                         [(0x200, 0xA001), (0x300, 0xA002)])
        with self.assertRaisesRegex(ValueError, "count"):
            walk_circular_ring(memory, 0x100, expected_count=3)

    def test_rejects_corrupt_ring_and_payload_aliasing(self):
        corrupt = {
            0x100: (0x200, 0x300, 0xDEADBEEF),
            0x200: (0x300, 0x100, 0xA001),
            0x300: (0x200, 0x200, 0xA002),
        }
        with self.assertRaisesRegex(ValueError, "cycles before"):
            walk_circular_ring(corrupt, 0x100)
        alias = {
            0x100: (0x200, 0x200, 0xDEADBEEF),
            0x200: (0x100, 0x100, 0x200),
        }
        with self.assertRaisesRegex(ValueError, "aliases"):
            walk_circular_ring(alias, 0x100)


class EndpointGraphTests(unittest.TestCase):
    def test_builds_endpoint_identity_components(self):
        graph = endpoint_identity_graph({
            "edge-0": ("v0", "v1"),
            "edge-1": ("v1", "v2"),
            "edge-2": ("v8", "v9"),
        })
        self.assertEqual(graph["component_count"], 2)
        self.assertEqual(graph["components"], [
            {"edges": ["edge-0", "edge-1"], "vertices": ["v0", "v1", "v2"]},
            {"edges": ["edge-2"], "vertices": ["v8", "v9"]},
        ])

    def test_compares_candidate_and_baseline_graphs(self):
        result = compare_endpoint_graphs(
            {"edge-0": ("v0", "v1"), "edge-1": ("v1", "v2")},
            {"edge-0": ("v0", "v1"), "edge-1": ("v3", "v4")},
        )
        self.assertEqual(result["added_or_changed_edges"], ["edge-1"])
        self.assertEqual(result["removed_or_changed_edges"], ["edge-1"])
        self.assertEqual(result["baseline"]["component_count"], 1)
        self.assertEqual(result["candidate"]["component_count"], 2)

    def test_rejects_bad_endpoint_sets(self):
        with self.assertRaisesRegex(ValueError, "exactly two"):
            endpoint_identity_graph({"edge": ("v0",)})
        with self.assertRaisesRegex(ValueError, "distinct"):
            endpoint_identity_graph({"edge": ("v0", "v0")})


class PlaneReplayContractTests(unittest.TestCase):
    def test_plane_equivalence_uses_strict_native_boundaries(self):
        first = {"normal": (1.0, 0.0, 0.0), "d": 0.0}
        at_d_boundary = {"normal": (1.0, 0.0, 0.0), "d": 0.0005}
        inside_d_boundary = {
            "normal": (1.0, 0.0, 0.0),
            "d": math.nextafter(0.0005, 0.0),
        }
        at_normal_boundary = {"normal": (0.9995, 0.0, 0.0), "d": 0.0}
        inside_normal_boundary = {
            "normal": (math.nextafter(0.9995, 1.0), 0.0, 0.0), "d": 0.0,
        }
        self.assertFalse(plane_equivalent(first, at_d_boundary, 0.0005))
        self.assertTrue(plane_equivalent(first, inside_d_boundary, 0.0005))
        self.assertFalse(plane_equivalent(first, at_normal_boundary, 0.0005))
        self.assertTrue(plane_equivalent(first, inside_normal_boundary, 0.0005))

    def test_runtime_capture_rejects_wrong_build_and_asset_hashes(self):
        capture = {
            "corpus_id": CORPUS_ID,
            "exe_sha256": EXE_SHA256,
            "baseline_gxm_sha256": "a" * 64,
            "candidate_gxm_sha256": "b" * 64,
            "candidate_breakpoint_hit": True,
        }
        validate_runtime_capture(capture, baseline_sha256="a" * 64,
                                 candidate_sha256="b" * 64)
        wrong = dict(capture, corpus_id="demo-9.3.1")
        with self.assertRaisesRegex(ValueError, "build ID"):
            validate_runtime_capture(wrong, baseline_sha256="a" * 64,
                                     candidate_sha256="b" * 64)
        wrong = dict(capture, candidate_gxm_sha256="c" * 64)
        with self.assertRaisesRegex(ValueError, "candidate GXM hash"):
            validate_runtime_capture(wrong, baseline_sha256="a" * 64,
                                     candidate_sha256="b" * 64)

    def test_pinned_input_hashes_reject_other_build_assets(self):
        validate_pinned_gxm_hashes(
            "fd08bc10c440fce261ef126e40445002fb56359d4011c1dcbf9c2f71b0e91047",
            "0425e1636bc83844da241d48e30fedae2d48aff024cb4f1e329506ac64b1e699",
        )
        with self.assertRaisesRegex(ValueError, "baseline SHA256"):
            validate_pinned_gxm_hashes("0" * 64, "0425e1636bc83844da241d48e30fedae2d48aff024cb4f1e329506ac64b1e699")
        with self.assertRaisesRegex(ValueError, "candidate SHA256"):
            validate_pinned_gxm_hashes(
                "fd08bc10c440fce261ef126e40445002fb56359d4011c1dcbf9c2f71b0e91047",
                "0" * 64,
            )

    def test_json_encoding_is_deterministic(self):
        value = {"z": [1, 2], "a": {"y": 3, "x": 4}}
        self.assertEqual(deterministic_json(value), deterministic_json(value))
        self.assertLess(deterministic_json(value).index('"a"'),
                        deterministic_json(value).index('"z"'))


if __name__ == "__main__":
    unittest.main()
