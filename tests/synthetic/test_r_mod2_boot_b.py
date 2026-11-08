from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class BootBSourceContractTests(unittest.TestCase):
    def test_boot_a_forwarding_contract_is_preserved(self):
        proxy = (ROOT / "src/native/rmod1/dinput8_proxy.cpp").read_text(encoding="utf-8")
        exports = (ROOT / "src/native/rmod1/dinput8_proxy.def").read_text(encoding="utf-8")
        self.assertIn('"DirectInput8Create", "DllCanUnloadNow", "DllGetClassObject"', proxy)
        self.assertIn("LoadLibraryExW(path.c_str(), nullptr, LOAD_LIBRARY_SEARCH_SYSTEM32)", proxy)
        self.assertIn("InitOnceExecuteOnce(&g_boot_once", proxy)
        self.assertIn("DllRegisterServer=_ProxyDllRegisterServer@0 @4", exports)
        self.assertIn("GetdfDIJoystick=_ProxyGetdfDIJoystick@0 @6", exports)
        self.assertNotIn("rmod2_boot::initialize", proxy[proxy.index("DllMain"):proxy.index("ProxyDirectInput8Create")])

    def test_inprocess_installer_is_pinned_to_f3_and_skips_oep_hook(self):
        source = (ROOT / "src/native/rmod1/rmod2_inprocess.cpp").read_text(encoding="utf-8")
        self.assertIn("rmod1_plan::kRetailSha256", source)
        self.assertIn("verify_mapped_image(disk,map_error)", source)
        self.assertIn('std::string_view(op.id)=="oep-bootstrap"', source)
        self.assertIn("kRuntimeCoreSha256", source)
        self.assertIn("MRConfigureBlobV1", source)
        self.assertIn("FlushInstructionCache", source)
        self.assertIn("FrozenThreads frozen", source)
        self.assertIn("BOOT_B_READY", source)
        self.assertIn("BOOT_B_FAILED", source)
        self.assertIn("BOOT_B_NO_FEATURES", source)

    def test_live_image_verification_uses_virtual_extent_and_exact_selected_preimages(self):
        source = (ROOT / "src/native/rmod1/rmod2_inprocess.cpp").read_text(encoding="utf-8")
        helper = (ROOT / "src/native/rmod1/runtime_image_diff.hpp").read_text(encoding="utf-8")
        self.assertIn("virtual_size > rmod1_plan::kImageSize-rva", source)
        self.assertIn("scan_mapped_section(disk.data()+raw,raw_size,base+rva,virtual_size,rva,planned)", source)
        self.assertIn("IMAGE_SELECTED_HOOK_CONFLICT", source)
        self.assertIn("section=%s RVA=0x%08X VA=0x%08X", source)
        self.assertIn("page_protect=0x%08X", source)
        self.assertIn("overlaps_selected_operation=%s", source)
        self.assertIn("std::memcmp(actual.data(),p.expected.data(),p.expected.size())", source)
        self.assertIn("i < virtual_size", helper)
        self.assertNotIn("memcmp(base+rva,disk.data()+raw,raw_size)", source)

    def test_mapped_image_diff_harness_covers_padding_and_hook_conflicts(self):
        harness = (ROOT / "tests/rmod1/runtime_image_diff_harness.cpp").read_text(encoding="utf-8")
        builder = (ROOT / "tools/build_rmod2_boot_b.py").read_text(encoding="utf-8")
        self.assertIn("File-alignment padding", harness)
        self.assertIn("selected_hook_conflict=1", harness)
        self.assertIn("runtime_image_diff_harness.exe", builder)
        self.assertIn("windows_image_diff_harness=", builder)

    def test_failure_transaction_restores_or_terminates_without_resuming_partial_hooks(self):
        source = (ROOT / "src/native/rmod1/rmod2_inprocess.cpp").read_text(encoding="utf-8")
        self.assertIn("native patch transaction failed; original bytes restored", source)
        self.assertIn("if(!rollback_ok) TerminateProcess(GetCurrentProcess()", source)
        self.assertLess(source.index("frozen.freeze("), source.index("std::memcpy(reinterpret_cast<void*>(p.address)"))
        self.assertIn("frozen.resume();", source)

    def test_builder_keeps_runtime_core_and_profile_separate_from_bootstrap(self):
        builder = (ROOT / "tools/build_rmod2_boot_b.py").read_text(encoding="utf-8")
        self.assertIn('checkpoint="f3"', builder)
        self.assertIn("EXPECTED_F3_CORE", builder)
        self.assertIn('"oep-bootstrap"', builder)
        self.assertIn('"sample_profile_native_operation_count"', builder)
        self.assertIn('"renderer_proxy_modified": False', builder)
        self.assertIn('"human_game_runtime": "PENDING"', builder)

    def test_inprocess_ini_is_consumed_directly_and_offsets_remain_typed(self):
        source = (ROOT / "src/native/rmod1/rmod2_inprocess.cpp").read_text(encoding="utf-8")
        planner = (ROOT / "tools/r_mod1_native_plan.py").read_text(encoding="utf-8")
        self.assertIn("configure(blob.data())", source)
        self.assertIn('std::string_view(op.id)=="oep-bootstrap"', source)
        self.assertIn("only generated code that reads", source)
        self.assertNotIn("kConfigOffset-rmod1_plan::kDataBase", source)
        self.assertNotIn("kDllPathOffset-rmod1_plan::kDataBase", source)
        self.assertIn("kConfigOffset = 0x{CONFIG_BLOB - DATA_BASE:x}u", planner)
        self.assertIn("kDllPathOffset = 0x{DLL_PATH - DATA_BASE:x}u", planner)

    def test_host_qualified_preflight_harness_exercises_production_helpers(self):
        source = (ROOT / "src/native/rmod1/rmod2_inprocess.cpp").read_text(encoding="utf-8")
        helper = (ROOT / "src/native/rmod1/rmod2_startup_preflight.hpp").read_text(encoding="utf-8")
        harness = (ROOT / "tests/rmod1/rmod2_host_qualified_preflight_harness.cpp").read_text(encoding="utf-8")
        builder = (ROOT / "tools/build_rmod2_boot_b.py").read_text(encoding="utf-8")
        for contract in ("copy_generated_template", "validate_operation_spans", "verify_native_preimages", "write_u32_address"):
            self.assertIn(contract, source)
            self.assertIn(contract, harness)
            self.assertIn(contract, helper)
        self.assertIn("maximum-4096-byte-ini", harness)
        self.assertIn("provided-configversion2-ini", harness)
        self.assertIn("empty-default-config", harness)
        self.assertIn("rmod2_host_qualified_preflight_harness.exe", builder)
        self.assertIn("host_qualified_preflight=", builder)


if __name__ == "__main__":
    unittest.main()
