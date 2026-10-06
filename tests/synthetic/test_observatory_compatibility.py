from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/runtime"))
sys.path.insert(0, str(ROOT / "tools"))
import observatory_compatibility as compat
import observatory_profile_resolver as resolver
from test_research_build_profiles import capability_fixture


class PortableCompatibilityTests(unittest.TestCase):
    def setUp(self):
        image, canonical = capability_fixture()
        self.image = image
        self.canonical = canonical
        self.registry = {"schema_version": 1, "detection_fingerprints": {}}

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
