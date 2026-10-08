from __future__ import annotations

import hashlib
import copy
import json
import sys
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/runtime"))
sys.path.insert(0, str(ROOT / "tools"))
import observatory_compatibility as compat
import observatory_profile_resolver as resolver
import mr_observe as observe
import dev_command_trigger as commands
from test_research_build_profiles import capability_fixture


class PortableCompatibilityTests(unittest.TestCase):
    def setUp(self):
        image, canonical = capability_fixture()
        self.image = image
        self.canonical = canonical
        self.registry = {"schema_version": 1, "detection_fingerprints": {}}

    def hardened_trampoline_fixture(self):
        image = bytearray(self.image)
        canonical = copy.deepcopy(self.canonical)
        pe = compat.pe_layout(image)
        walker = next(row for row in canonical["anchors"] if row["name"] == "native_dump_walker")
        walker.update(va=0x401400, length=0x600, section=".text")
        anchor_start = next(s["raw_offset"] + walker["va"] - pe["image_base"] - s["rva"]
                            for s in pe["sections"] if s["name"] == ".text")
        stock = bytes((index * 37 + 11) & 0xFF for index in range(walker["length"]))
        image[anchor_start:anchor_start + len(stock)] = stock

        specs = [
            dict(name="stringlist-null-guard", offset=798, original_hex="8b7b043b7b08",
                 stub_length=19, stub_prefix_hex="85db0f84", stub_body_hex="8b7b043b7b08",
                 null_delta=0x240, resume_delta=0x224, stub_va=0x402100),
            dict(name="xmldata-null-guard", offset=1107, original_hex="8b108bc8ff520c",
                 stub_length=20, stub_prefix_hex="85c00f84", stub_body_hex="8b108bc8ff520c",
                 null_delta=0x48E, resume_delta=0x45A, stub_va=0x402120),
        ]
        image[anchor_start + 798:anchor_start + 804] = bytes.fromhex(specs[0]["original_hex"])
        image[anchor_start + 1107:anchor_start + 1114] = bytes.fromhex(specs[1]["original_hex"])
        stock = bytes(image[anchor_start:anchor_start + walker["length"]])

        def file_offset(va):
            rva = va - pe["image_base"]
            section = next(s for s in pe["sections"] if s["rva"] <= rva < s["rva"] + s["raw_size"])
            return section["raw_offset"] + rva - section["rva"]

        def rel32(source_after_instruction, target):
            return struct.pack("<i", target - source_after_instruction)

        stable_spans = [(0, 798), (804, 1107), (1114, walker["length"])]
        stable_segments = [dict(offset=start, length=end - start,
                                sha256=hashlib.sha256(stock[start:end]).hexdigest())
                           for start, end in stable_spans]
        hooks = []
        for spec in specs:
            hook_va = walker["va"] + spec["offset"]
            null_target = walker["va"] + spec["null_delta"]
            resume_target = walker["va"] + spec["resume_delta"]
            stub_va = spec["stub_va"]
            prefix = bytes.fromhex(spec["stub_prefix_hex"])
            body = bytes.fromhex(spec["stub_body_hex"])
            stub_length = spec["stub_length"]
            branch = prefix + rel32(stub_va + len(prefix) + 4, null_target) + body
            stub = branch + b"\xE9" + rel32(stub_va + stub_length, resume_target)
            self.assertEqual(len(stub), stub_length)
            stub_offset = file_offset(stub_va)
            image[stub_offset:stub_offset + len(stub)] = stub
            patch = b"\xE9" + rel32(hook_va + 5, stub_va) + b"\x90" * (len(bytes.fromhex(spec["original_hex"])) - 5)
            hook_offset = anchor_start + spec["offset"]
            image[hook_offset:hook_offset + len(patch)] = patch
            hooks.append({key: spec[key] for key in ("name", "offset", "original_hex", "stub_length",
                                                        "stub_prefix_hex", "stub_body_hex")})
            hooks[-1].update(null_target_va=null_target, resume_target_va=resume_target)
        walker["sha256"] = hashlib.sha256(stock).hexdigest()
        walker["semantic_variants"] = [dict(id="native-hardened-null-safe-stubs-v1",
                                             stable_segments=stable_segments, hooks=hooks)]
        return bytes(image), canonical

    def test_portable_data_has_no_external_research_paths(self):
        self.assertTrue((ROOT / "tools/runtime/data/broker-families.json").is_file())
        self.assertTrue((ROOT / "tools/runtime/data/registry-profiles.json").is_file())
        text = (ROOT / "tools/runtime/observatory_compatibility.py").read_text(encoding="utf-8")
        self.assertNotIn("research_build_profiles", text)
        self.assertNotIn("master-rallye-re-general", text)
        self.assertNotIn("r_ai", text.casefold())

    def test_structurally_compatible_family_is_audited(self):
        with patch.object(compat, "definitions", return_value=self.canonical), \
             patch.object(compat, "registry_definitions", return_value=self.registry):
            audit = compat.audit_build(self.image)
        self.assertTrue(audit["layout_compatible"])
        self.assertTrue(audit["capabilities"]["broker_read"])
        self.assertEqual(audit["status"], "FULL_FAMILY_COMPATIBLE")
        self.assertFalse(audit["capabilities"]["post_results_native_dump_safe"])

    def test_null_safe_trampoline_variant_is_automatically_classified_hardened(self):
        image, canonical = self.hardened_trampoline_fixture()
        with tempfile.TemporaryDirectory() as folder:
            cache = Path(folder) / "build-profiles"
            with patch.object(compat, "definitions", return_value=canonical), \
                 patch.object(compat, "registry_definitions", return_value=self.registry):
                audit = compat.audit_build(image)
                self.assertEqual(audit["status"], "FULL_FAMILY_COMPATIBLE")
                self.assertEqual(audit["build_classification"], "hardened")
                self.assertEqual(audit["capabilities"]["broker_dump_variant"], "native_hardened")
                self.assertTrue(audit["capabilities"]["hardened_dump"])
                self.assertTrue(audit["capabilities"]["post_results_native_dump_safe"])
                profile = compat.resolve_build(image, cache_root=cache)
                self.assertEqual(profile["profile_id"], "local-hardened-" + profile["sha256"][:12])
                self.assertEqual(profile["build_classification"], "hardened")
                self.assertTrue(profile["capabilities"]["open_broker_editor"])
                self.assertTrue(profile["capabilities"]["native_dump"])
                runtime_profile = resolver._from_audit(profile)
                self.assertEqual(runtime_profile.id, profile["profile_id"])
                self.assertTrue(runtime_profile.supports("open_broker_editor"))
                self.assertTrue(runtime_profile.supports("native_dump"))
                self.assertFalse(runtime_profile.supports("flow_builder"))
                provenance = resolver.profile_provenance(runtime_profile)
                self.assertEqual(provenance["build_classification"], "hardened")
                self.assertEqual(provenance["disk_broker_dump_variant"], "native_hardened")
                self.assertEqual(provenance["effective_broker_dump_variant"], "not_attested")
                self.assertIsNone(provenance["native_dump_post_results_safe"])
                self.assertEqual(runtime_profile.build_classification, "hardened")
                process = Mock(profile=runtime_profile, pid=77)
                existing_window = object()
                with patch.object(commands, "find_tool_windows", return_value=[existing_window]) as find_windows:
                    self.assertIs(observe.ensure_tool(process, "broker-editor"), existing_window)
                find_windows.assert_called_once_with(77, "broker-editor", runtime_profile)
                second = compat.resolve_build(image, cache_root=cache)
                self.assertTrue(second["cache_reused"])

    def test_malformed_hardened_stub_never_enables_native_dump(self):
        image, canonical = self.hardened_trampoline_fixture()
        walker = next(row for row in canonical["anchors"] if row["name"] == "native_dump_walker")
        patch_offset = 0x1000 + walker["va"] - 0x401000
        bad_stub = bytearray(image)
        # The synthetic first stub is at 0x402100 in the fixture's executable .text section.
        stub_offset = 0x1000 + (0x402100 - 0x401000)
        bad_stub[stub_offset] ^= 1
        bad_hook = bytearray(image)
        bad_hook[patch_offset + 798 + 1] ^= 1
        for broken in (bad_stub, bad_hook):
            with patch.object(compat, "definitions", return_value=canonical), \
                 patch.object(compat, "registry_definitions", return_value=self.registry):
                audit = compat.audit_build(bytes(broken))
            self.assertFalse(audit["family_anchor_compatible"])
            self.assertFalse(audit["capabilities"]["hardened_dump"])
            self.assertFalse(audit["capabilities"]["native_dump"])
            self.assertFalse(audit["capabilities"]["open_broker_editor"])

    def test_change_to_unchanged_walker_bytes_is_not_accepted_as_hardened(self):
        image, canonical = self.hardened_trampoline_fixture()
        walker = next(row for row in canonical["anchors"] if row["name"] == "native_dump_walker")
        anchor_offset = 0x1000 + walker["va"] - 0x401000
        changed = bytearray(image)
        changed[anchor_offset + 100] ^= 1
        with patch.object(compat, "definitions", return_value=canonical), \
             patch.object(compat, "registry_definitions", return_value=self.registry):
            audit = compat.audit_build(bytes(changed))
        self.assertFalse(audit["family_anchor_compatible"])
        self.assertFalse(audit["capabilities"]["hardened_dump"])
        self.assertFalse(audit["capabilities"]["native_dump"])

    def test_hardened_walker_does_not_override_broken_broker_core(self):
        image, canonical = self.hardened_trampoline_fixture()
        changed = bytearray(image)
        changed[0x1004] ^= 1
        with patch.object(compat, "definitions", return_value=canonical), \
             patch.object(compat, "registry_definitions", return_value=self.registry):
            audit = compat.audit_build(bytes(changed))
        self.assertFalse(audit["capabilities"]["broker_read"])
        self.assertFalse(audit["capabilities"]["native_dump"])
        self.assertFalse(audit["capabilities"]["hardened_dump"])
        self.assertEqual(audit["build_classification"], "incompatible")

    def test_unknown_compatible_build_gets_sha_bound_reaudited_cache(self):
        with tempfile.TemporaryDirectory() as folder:
            cache = Path(folder) / "build-profiles"
            with patch.object(compat, "definitions", return_value=self.canonical), \
                 patch.object(compat, "registry_definitions", return_value=self.registry):
                first = compat.resolve_build(self.image, cache_root=cache)
                self.assertEqual(first["profile_origin"], "locally_audited")
                self.assertFalse(first["cache_reused"])
                cache_file = next(cache.glob("*.json"))
                second = compat.resolve_build(self.image, cache_root=cache)
                self.assertTrue(second["cache_reused"])
                cached = json.loads(cache_file.read_text(encoding="utf-8"))
                cached["sha256"] = "0" * 64
                cache_file.write_text(json.dumps(cached), encoding="utf-8")
                third = compat.resolve_build(self.image, cache_root=cache)
                self.assertFalse(third["cache_reused"])
                self.assertEqual(third["sha256"], hashlib.sha256(self.image).hexdigest())

    def test_critical_anchor_change_is_rejected(self):
        changed = bytearray(self.image)
        changed[0x1004] ^= 1
        with patch.object(compat, "definitions", return_value=self.canonical), \
             patch.object(compat, "registry_definitions", return_value=self.registry):
            audit = compat.audit_build(bytes(changed))
            self.assertFalse(audit["capabilities"]["broker_read"])
            with self.assertRaisesRegex(ValueError, "failed structural"):
                compat.resolve_build(bytes(changed), write_local_profile=False)

    def test_resolver_never_imports_repository_auditor(self):
        source = (ROOT / "tools/runtime/observatory_profile_resolver.py").read_text(encoding="utf-8")
        self.assertNotIn("import research_build_profiles", source)
        self.assertIn("observatory_compatibility", source)


if __name__ == "__main__":
    unittest.main()
