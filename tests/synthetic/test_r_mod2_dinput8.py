from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import audit_dinput8_exports as audit


class DInput8ProxySourceTests(unittest.TestCase):
    def test_forwarder_preserves_known_system_export_names_and_ordinals(self) -> None:
        system = Path(r"C:\Windows\SysWOW64\dinput8.dll")
        if not system.is_file():
            self.skipTest("Windows x86 DirectInput system DLL is unavailable")
        observed = audit.exports(system.read_bytes())
        for name, ordinal in audit.EXPECTED.items():
            self.assertEqual(observed.get(name), ordinal)

    def test_proxy_has_no_static_import_of_its_own_dll_and_minimal_dllmain(self) -> None:
        source = (ROOT / "src/native/rmod1/dinput8_proxy.cpp").read_text(encoding="utf-8")
        self.assertIn("GetSystemDirectoryW", source)
        self.assertIn("LoadLibraryExW(path.c_str(), nullptr, LOAD_LIBRARY_SEARCH_SYSTEM32)", source)
        self.assertIn("GetModuleFileNameW(g_system_dinput8", source)
        self.assertIn("CompareStringOrdinal(path.c_str()", source)
        self.assertIn("InitOnceExecuteOnce", source)
        dllmain = source.split("extern \"C\" BOOL WINAPI DllMain", 1)[1].split("extern \"C\" HRESULT", 1)[0]
        self.assertNotIn("LoadLibrary", dllmain)
        self.assertNotIn("CreateThread", dllmain)
        self.assertNotIn("DisableThreadLibraryCalls", dllmain)

    def test_proxy_definition_covers_all_names_and_exact_ordinals(self) -> None:
        definition = (ROOT / "src/native/rmod1/dinput8_proxy.def").read_text(encoding="ascii")
        for name, ordinal in audit.EXPECTED.items():
            self.assertIn(f"{name}=", definition)
            self.assertIn(f"@{ordinal}", definition)

    def test_export_audit_fails_on_non_pe32_or_truncated_data(self) -> None:
        with self.assertRaises(audit.ExportAuditError):
            audit.exports(b"MZ" + bytes(20))


if __name__ == "__main__":
    unittest.main()
