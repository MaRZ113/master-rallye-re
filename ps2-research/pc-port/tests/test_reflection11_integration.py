"""Bounded integration/lifecycle witnesses; native mocks check actual transactions."""
from pathlib import Path
import os
import unittest

PORT=Path(__file__).resolve().parents[1]
RENDERER=Path(os.environ.get('MRR_PC_PORT_RENDERER_ROOT',PORT/'.staging/ps2-enabled/modernization/renderer'))

class Reflection11IntegrationTests(unittest.TestCase):
    def test_capture_repairs_before_native_or_effective_state_access(self):
        for filename,methods in [('quality_wrappers.cpp',('Present','SetViewport','GetViewport')),
                                 ('visual_wrappers.cpp',('SetTextureStageState','GetTextureStageState','GetTransform')),
                                 ('forwarders.cpp',('GetRenderTarget','GetDepthStencilSurface','SetRenderTarget','ValidateDevice'))]:
            source=(RENDERER/'src'/filename).read_text()
            for method in methods:
                part=source[source.index('Device8::'+method+'('):]
                part=part[:part.index('\n}')]
                self.assertLess(part.index('repair_reflection()'),part.index('real_->'+method+'('),method)
        source=(RENDERER/'src/visual_wrappers.cpp').read_text()
        part=source[source.index('Device8::SetTextureStageState('):]
        self.assertLess(part.index('repair_reflection()'),part.index('visuals.filter('))
        source=(RENDERER/'src/wrappers.cpp').read_text()
        self.assertIn('item.second->ps2_port()->native_states_pending()',source)
        self.assertIn('ps2_port_->native_states_pending()',source)

    def test_original_tata_identity_retained_by_explicit_verified_registry(self):
        # PORT2 authorizes a second layout. Native mocks exercise both while
        # this integration check preserves the historical source identity.
        import json
        old=json.loads((PORT/'docs/reflection-port1/material-source-contract.json').read_text())
        header=(PORT/'renderer/reflection_pilot.hpp').read_text()
        self.assertIn(old['pc_material']['geometry_sha256'],header)
        self.assertIn('{"Tata",kTataBonnetGeometrySha,55,48}',header)
        self.assertIn('bool expanded=false',header)
        source=(PORT/'renderer/reflection_pilot.cpp').read_text()
        for gate in ('missing_current_upload_or_resource_identity','native_material_stage_mismatch',
                     'live_race_owner_unverified','conflicting_viewdependent2d_policy'):
            self.assertIn(gate,source)

    def test_reset_releases_default_pool_and_pending_capture_cannot_be_ignored(self):
        h=(PORT/'renderer/reflection_pilot.hpp').read_text()
        source=(PORT/'renderer/reflection_pilot.cpp').read_text()
        self.assertIn('capture_.release()',h+source)
        self.assertIn('capture_.pending()',source)
        integration=(PORT/'renderer/reflection_native_integration.hpp').read_text()
        self.assertLess(integration.index('capture.repair('),integration.index('auto& t=pilot.transaction()'))
        capture=(PORT/'renderer/reflection_capture.cpp').read_text()
        self.assertNotIn('LockRect(',capture)
        self.assertNotIn('GetRenderTargetData',capture)
        self.assertNotIn('BeginScene(',capture)
        self.assertNotIn('EndScene(',capture)

if __name__=='__main__':unittest.main()
