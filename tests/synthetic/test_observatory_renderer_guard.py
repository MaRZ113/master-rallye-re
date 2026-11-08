"""Renderer NULL-guard native Dump variant (Observatory 0.3.1).

Golden stubs were read from a live retail process running the modernization d3d8
renderer (2026-11-08): StringList stub at 0x00F70000, XmlData stub at 0x02840000,
both counting NULL hits at 0x009F6D4C / 0x009F6D50.
"""
from __future__ import annotations

import struct
import unittest

import observatory_compatibility as compat

STRINGLIST_LIVE = bytes.fromhex(
    "85db0f850e0000009cf0ff054c6d9f009de92a2069ff8b7b043b7b08e9032069ff")
XMLDATA_LIVE = bytes.fromhex(
    "9c85c00f840d0000009d8b108bc8685a216000ff620c9d9cf0ff05506d9f009de96921dcfd")
WALKER_VA = 0x00601D00
WALKER_LEN = 0x600


class RendererNullStubTests(unittest.TestCase):
    def test_stub_builder_matches_live_renderer_bytes(self):
        self.assertEqual(compat.renderer_null_stub("stringlist", 0x00F70000, 0x009F6D4C), STRINGLIST_LIVE)
        self.assertEqual(compat.renderer_null_stub("xmldata", 0x02840000, 0x009F6D50), XMLDATA_LIVE)

    def _memory(self, walker: bytes):
        mem = {WALKER_VA: walker, 0x00F70000: STRINGLIST_LIVE, 0x02840000: XMLDATA_LIVE}

        def read(va, size):
            for base, blob in mem.items():
                if base <= va and va + size <= base + len(blob):
                    return blob[va - base:va - base + size]
            raise ValueError("unmapped")
        return read

    def _guarded(self, stock: bytes) -> bytes:
        walker = bytearray(stock)
        for site, stub, pad in ((0x0060201E, 0x00F70000, 1), (0x00602153, 0x02840000, 2)):
            off = site - WALKER_VA
            walker[off:off + 5 + pad] = b"\xe9" + struct.pack("<i", stub - (site + 5)) + b"\x90" * pad
        return bytes(walker)

    def _anchor(self, stock: bytes):
        return {"va": WALKER_VA, "length": WALKER_LEN, "sha256": compat.digest(stock)}

    def _stock(self) -> bytes:
        walker = bytearray(range(256)) * 6
        walker[0x31E:0x324] = bytes.fromhex("8b7b043b7b08")
        walker[0x453:0x45A] = bytes.fromhex("8b108bc8ff520c")
        return bytes(walker)

    def test_guarded_walker_restores_to_stock(self):
        stock = self._stock()
        verified = compat._match_renderer_null_guard(self._memory(self._guarded(stock)), self._anchor(stock))
        self.assertIsNotNone(verified)
        self.assertEqual([v["target_va"] for v in verified], ["0x00F70000", "0x02840000"])

    def test_other_change_in_walker_is_rejected(self):
        stock = self._stock()
        guarded = bytearray(self._guarded(stock))
        guarded[0x10] ^= 0xFF
        self.assertIsNone(compat._match_renderer_null_guard(self._memory(bytes(guarded)), self._anchor(stock)))

    def test_foreign_stub_is_rejected(self):
        stock = self._stock()
        read = self._memory(self._guarded(stock))

        def tampered(va, size):
            data = bytearray(read(va, size))
            if va == 0x00F70000:
                data[20] ^= 0x01
            return bytes(data)
        self.assertIsNone(compat._match_renderer_null_guard(tampered, self._anchor(stock)))

    def test_post_results_safe(self):
        self.assertTrue(compat.native_dump_post_results_safe(compat.RENDERER_NULL_GUARD_VARIANT_ID))


if __name__ == "__main__":
    unittest.main()
