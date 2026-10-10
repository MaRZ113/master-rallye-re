from __future__ import annotations

import copy
import hashlib
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/runtime"))
sys.path.insert(0, str(ROOT / "tests/synthetic"))

import broker_observatory as broker
import observatory_compatibility as compat
from observatory_build_profiles import RETAIL_PRISTINE
from test_observatory_live_memory import FIXTURE, MockProcessMemory


class RemoteAnchorVerificationTests(unittest.TestCase):
    """Exercise the complete Broker remote-anchor gate with bounded mock memory."""

    def setUp(self):
        self.canonical = copy.deepcopy(compat.definitions())
        self.pe = self.canonical["retail_pe"]
        self.base = self.pe["image_base"]
        self.walker = next(row for row in self.canonical["anchors"]
                           if row["name"] == "native_dump_walker")
        self.walker_rva = self.walker["va"] - self.base
        self.anchors, self.ranges = self._build_anchor_fixture()

    def _build_anchor_fixture(self):
        anchors = []
        ranges = []
        stock = bytes.fromhex(FIXTURE["walker"]["stock_bytes_hex"])
        for row in self.canonical["anchors"]:
            rva = row["va"] - self.base
            if row["name"] == "native_dump_walker":
                content = stock
                digest = row["sha256"]
            else:
                seed = row["name"].encode("ascii")
                content = (seed * ((row["length"] // len(seed)) + 1))[:row["length"]]
                digest = hashlib.sha256(content).hexdigest()
            anchors.append({"name": row["name"], "rva": rva,
                            "length": row["length"], "sha256": digest,
                            "section": row["section"]})
            ranges.append((self.base + rva, content))
        return anchors, ranges

    def _profile(self, anchors=None, *, sha256=None):
        return replace(
            RETAIL_PRISTINE,
            sha256=sha256 or RETAIL_PRISTINE.sha256,
            runtime_anchors=tuple(copy.deepcopy(anchors or self.anchors)),
            capabilities={"native_dump": True},
            pe_identity={"image_base": self.base,
                         "size_of_image": self.pe["size_of_image"]},
        )

    def _verify(self, memory, profile=None, *, disk_sha256=None):
        with patch.object(compat, "definitions", return_value=self.canonical), \
                patch.object(broker, "_read_remote",
                             side_effect=lambda _kernel, _process, address, size, _ctypes:
                             memory.read(address, size)):
            return broker._verify_remote_anchors(
                object(), object(), self.base, object(), profile or self._profile(),
                "native_dump", pe=self.pe, runtime_details={},
                disk_sha256=disk_sha256 or RETAIL_PRISTINE.sha256,
                disk_size=RETAIL_PRISTINE.file_size,
            )

    def _memory(self, walker_bytes=None, *, altered_stub=False, duplicate_walker_at=None):
        ranges = list(self.ranges)
        if walker_bytes is not None:
            ranges = [(address, data) for address, data in ranges
                      if address != self.base + self.walker_rva]
            ranges.append((self.base + self.walker_rva, walker_bytes))
        if walker_bytes is not None and hashlib.sha256(walker_bytes).hexdigest() == FIXTURE["walker"]["j1_sha256"]:
            for stub in FIXTURE["trampolines"]:
                data = bytes.fromhex(stub["bytes_hex"])
                if altered_stub and stub["name"] == "xmldata-null-guard":
                    data = bytes([data[0] ^ 1]) + data[1:]
                ranges.append((stub["va"], data))
        if duplicate_walker_at is not None:
            stock = bytes.fromhex(FIXTURE["walker"]["stock_bytes_hex"])
            ranges.append((self.base + duplicate_walker_at, stock))
        return MockProcessMemory(ranges)

    def test_pristine_retail_with_stock_walker_is_accepted(self):
        verified = self._verify(self._memory())
        self.assertIn("native_dump_walker:native_stock", verified)

    def test_pristine_retail_with_exact_j1_walker_and_trampolines_is_accepted(self):
        walker = bytes.fromhex(FIXTURE["walker"]["j1_bytes_hex"])
        verified = self._verify(self._memory(walker))
        self.assertIn("native_dump_walker:native-hardened-null-safe-stubs-v1", verified)

    def test_reference_rva_must_be_canonical_va_minus_image_base(self):
        altered = copy.deepcopy(self.anchors)
        row = next(item for item in altered if item["name"] == "native_dump_walker")
        row["rva"] += 1
        with self.assertRaisesRegex(broker.ObservatoryError, "reference differs"):
            self._verify(self._memory(duplicate_walker_at=self.walker_rva + 1),
                         self._profile(altered))
        self.assertEqual(self.walker_rva, 0x201D00)

    def test_altered_walker_reference_sha_is_rejected(self):
        altered = copy.deepcopy(self.anchors)
        row = next(item for item in altered if item["name"] == "native_dump_walker")
        row["sha256"] = "0" * 64
        with self.assertRaisesRegex(broker.ObservatoryError, "reference differs"):
            self._verify(self._memory(), self._profile(altered))

    def test_altered_j1_trampoline_is_rejected(self):
        walker = bytes.fromhex(FIXTURE["walker"]["j1_bytes_hex"])
        with self.assertRaisesRegex(broker.ObservatoryError, "neither exact stock"):
            self._verify(self._memory(walker, altered_stub=True))

    def test_wrong_executable_identity_is_rejected(self):
        with self.assertRaisesRegex(broker.ObservatoryError, "exact pristine retail"):
            self._verify(self._memory(), self._profile(sha256="1" * 64))


if __name__ == "__main__":
    unittest.main()
