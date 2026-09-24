from __future__ import annotations

import struct
import unittest
import zlib

from master_rallye.gxi import encode_gxi_as_observed_dxt, parse_gxi_bytes
from tools.scanner.r_demo_texture_compare import compare_pipeline
from tools.runtime.demo_debug_capture import LineAccumulator, text_delta
from tools.runtime.demo_debug_classify import classify_line


class DemoRuntimeToolTests(unittest.TestCase):
    def setUp(self):
        self.gxi = struct.pack("<IHH", 0x00013039, 2, 1) + bytes((1, 2, 3, 4, 5, 6, 7, 8))
        self.offline = encode_gxi_as_observed_dxt(parse_gxi_bytes(self.gxi))

    def compare(self, runtime):
        return compare_pipeline("demo-8.4.1", "DataGx/test.gxi", self.gxi,
                                "DataGx/test.dxt", self.offline,
                                runtime, "run/test.dxt")

    def test_three_way_dxt_verdicts(self):
        identical = self.compare(self.offline)
        self.assertEqual(identical["verdict"], "THREE_WAY_BYTE_IDENTICAL")
        self.assertTrue(identical["original_dxt"]["crc_valid"])
        self.assertTrue(identical["comparisons"]["original_vs_runtime"]["full_byte_identical"])
        changed_header = bytearray(self.offline)
        struct.pack_into("<I", changed_header, 4, 2)
        header_report = self.compare(bytes(changed_header))
        self.assertEqual(header_report["verdict"], "PAYLOAD_IDENTICAL_HEADERS_DIFFER")
        self.assertEqual(header_report["comparisons"]["original_vs_runtime"]["header_field_differences"][0]["field"], "version")
        changed_payload = bytearray(self.offline[20:])
        changed_payload[0] ^= 1
        changed_dxt = struct.pack("<5I", 0xFEED, 1, zlib.crc32(changed_payload), 2, 1) + changed_payload
        self.assertEqual(self.compare(changed_dxt)["verdict"], "PAYLOAD_DIFFERS")
        self.assertEqual(compare_pipeline("demo-8.4.1", "a.gxi", self.gxi,
                                         "a.dxt", self.offline)["verdict"], "RUNTIME_PENDING")

    def test_text_delta_and_line_accumulation(self):
        self.assertEqual(text_delta("one\n", "one\ntwo\n"), ("two\n", False))
        self.assertEqual(text_delta("old\n", "new\n"), ("new\n", True))
        lines = LineAccumulator()
        self.assertEqual(lines.feed("first\r\nsec"), ["first"])
        self.assertEqual(lines.feed("ond\n"), ["second"])
        self.assertEqual(lines.flush(), "")

    def test_only_evidenced_debug_templates(self):
        cached = classify_line("14:32:10.421 | Loaded cached DX texture: [Black-tga.dxt]")
        self.assertEqual(cached["category"], "cached_dxt_load")
        self.assertEqual(cached["fields"]["resource"], "Black-tga.dxt")
        self.assertEqual(classify_line("Shader [shader/particle_blend], entry 0 selected")["category"],
                         "shader_selection")
        self.assertEqual(classify_line("Building convex hull for Trooper")["category"],
                         "convex_hull_build")
        self.assertEqual(classify_line("Caching disabled. Reading GXM: [Trooper]")["category"],
                         "model_gxm_read")
        self.assertEqual(classify_line("Some new debug message")["category"], "unclassified")


if __name__ == "__main__":
    unittest.main()
