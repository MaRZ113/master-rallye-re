"""Reset integration regression; default and raw escape behavior remain strict."""
from pathlib import Path
import json
import unittest

PORT=Path(__file__).resolve().parents[1]


class ResetOverlayTests(unittest.TestCase):
    def test_exact_patch_preserves_only_owned_reset_survivors(self):
        patch=(PORT/'overlay/patches/0001-renderer-integration.patch').read_text()
        policy=(PORT/'renderer/buffer_reset_policy.hpp').read_text()
        self.assertIn('retain_managed_mirror_on_reset',patch)
        self.assertIn('ps2_port_->buffer_mirroring_required()',patch)
        self.assertIn('reason&&!std::strcmp(reason,"device_reset")',patch)
        self.assertIn('proxy->second->generation()',patch)
        self.assertIn('trace.resources.generation(reinterpret_cast<uintptr_t>(entry.first))',patch)
        self.assertIn('mirror.available && !mirror.poisoned',policy)
        self.assertIn('mirror.generation==registered_proxy_generation',policy)
        self.assertIn('mirror.pool==D3DPOOL_MANAGED || mirror.pool==D3DPOOL_SYSTEMMEM',policy)
        self.assertNotIn('D3DPOOL_DEFAULT',policy)
        self.assertIn('mirror.poisoned=true;mirror.initialized.clear()',patch)
        self.assertIn('stream_buffers_.fill(nullptr);index_buffer_=nullptr',patch)

    def test_echo_stays_outside_reset_lifecycle_and_logs_rearm_real_success_only(self):
        patch=(PORT/'overlay/patches/0001-renderer-integration.patch').read_text()
        cpp=(PORT/'renderer/reflection_pilot.cpp').read_text()
        self.assertIn('if(native_reset_called&&successful)ps2_port_->device_reset(true)',patch)
        self.assertIn('if (called && successful) { blocked_ = false; suspended_ = false; logged_.fill(0); }',cpp)
        self.assertIn('device_reset_failed_reflection_suspended_stock',cpp)
        self.assertIn('mirror.poison_reason=reason?reason:"device_reset"',patch)

    def test_frozen_renderer_identity_unchanged(self):
        lock=json.loads((PORT/'overlay/baseline-lock.json').read_text())
        # COURSE-ALIVE1 adopted the opt-in probe teleport / crash log commits (lock probe_baseline_adoption).
        self.assertEqual(lock['renderer_tree'],'46663a8db86922443e74f4fb760b29b2d8ae6978')
        self.assertEqual(lock['baseline_head'],'c357e8b780734b1505acb86f723a0e1b57f3c8a8')
        self.assertEqual(lock['probe_baseline_adoption']['previous_renderer_tree'],'e33386bcf682db6983380c499e4928726c758fe0')


if __name__=='__main__':unittest.main()
