"""Ordering checks supplement native math/preflight/transaction tests."""
from pathlib import Path
import unittest

PORT=Path(__file__).resolve().parents[1]

class MenuGrassFixTests(unittest.TestCase):
    def test_preflight_precedes_broker_and_gpu_reads(self):
        for name in ('course_objects_native_integration.hpp','grass_native_integration.hpp'):
            s=(PORT/'renderer'/name).read_text()
            s=s[s.index('inline HRESULT before_ui'):]
            self.assertLess(s.index('course_world_preflight('),s.index('certificate(single)'))
            self.assertLess(s.index('boundary_consumed('),s.index('certificate(single)'))
            self.assertLess(s.index('course_world_preflight('),s.index('GetRenderTarget('))
            self.assertIn('course_object_admission(a,p->course())' if name=='grass_native_integration.hpp'
                          else 'course_object_admission(a)',s)

    def test_frontend_excluded_before_full_camera_certificate(self):
        s=(PORT/'renderer/course_objects_native_integration.hpp').read_text()
        s=s[s.index('inline RaceCertificate certificate'):s.index('inline bool same_identity')]
        self.assertLess(s.index('live_race_hud_context()'),s.index('live_race_certificate(camera)'))
        self.assertIn('if(!hud.valid||hud.attract)return {};',s)

    def test_object_layers_do_not_run_foliage_snapshot(self):
        s=(PORT/'overlay/patches/0001-renderer-integration.patch').read_text()
        self.assertIn('pilot_extension->foliage_analysis_enabled()',s)
        self.assertNotIn('pilot_extension->analysis_enabled()',s)
        s=(PORT/'renderer/ps2_port_extension.hpp').read_text()
        method=s[s.index('bool foliage_analysis_enabled()'):]
        method=method[:method.index('}')]
        self.assertIn('mode_!=PilotMode::Stock||pixel_probe_enabled()',method)
        self.assertNotIn('grass_',method)
        self.assertNotIn('course_objects_',method)

    def test_failure_evidence_survives_menu_rejection(self):
        s=(PORT/'renderer/grass_native_integration.hpp').read_text()
        self.assertIn('claim_build_log()',s)
        self.assertLess(s.index('claim_build_log()'),s.index('if(!built)'))
        self.assertIn('ps2_grass_build',s)

if __name__=='__main__':unittest.main()
