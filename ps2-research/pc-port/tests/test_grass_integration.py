"""Bounded grass integration checks; native safety and runtime parity are separate."""
from pathlib import Path
import configparser
import os
import unittest

PORT = Path(__file__).resolve().parents[1]
RENDERER = Path(os.environ.get('MRR_PC_PORT_RENDERER_ROOT', PORT / '.staging/ps2-enabled/modernization/renderer'))


class GrassIntegrationTests(unittest.TestCase):
    def test_grass_and_other_pilots_are_stock_by_default(self):
        ini = configparser.ConfigParser()
        ini.read(PORT / 'PS2Port.ini.example')
        for key in ('Grass', 'Diagnostics', 'CourseObjects', 'Foliage', 'Reflection'):
            self.assertEqual(ini.getint('PS2Port', key), 0)

    def test_independent_proof_and_exact_owner_admission(self):
        source = (PORT / 'renderer/grass_native_integration.hpp').read_text()
        self.assertIn('d.ps2_port()->grass()', source)
        self.assertIn('ps2port::course_object_admission(a,p->course())', source)
        self.assertIn('courseintegration::certificate(d,single)', source)
        self.assertIn('p->select_course(cert.course_id.data(),*d.native())', source)
        water=(PORT/'renderer/course_objects_native_integration.hpp').read_text()
        self.assertIn('ps2port::turkey3_course(cert.course_id.data())',water)
        self.assertIn('a.state_block_recording=d.trace.shadow.recording||d.trace.effective_shadow.recording', source)
        self.assertNotIn('course_objects()->active()', source)
        self.assertNotIn('foliage_diagnostics', source)

    def test_private_pass_has_no_application_draw_tracker_or_depth_write(self):
        source = (PORT / 'renderer/grass_native_integration.hpp').read_text()
        self.assertEqual(source.count('DrawPrimitiveUP('), 1)
        self.assertNotIn('.after(71', source)
        self.assertNotIn('.after(72', source)
        self.assertNotIn('SetRenderTarget(', source)
        self.assertIn('CourseObjectMaterialState{FALSE,D3DTADDRESS_CLAMP,D3DTADDRESS_CLAMP}', source)
        self.assertLess(source.index('mark_up_stream_changed()'), source.index('DrawPrimitiveUP('))
        self.assertLess(source.index('build_vertices(proof.view,vertices)'), source.index('transaction.capture(n)'))
        self.assertIn('identity,proof.projection,writer', source)

    def test_successful_camera_world_depth_proof_required(self):
        source = (PORT / 'renderer/grass_native_integration.hpp').read_text()
        start = source.index('inline void observe_transform')
        end = source.index('inline void observe_world_draw', start)
        camera = source[start:end]
        self.assertLess(camera.index('p->proof.invalidate_depth()'), camera.index('FAILED(hr)'))
        for token in ('GAMEPLAY_VIEW_RETURN_RVA', 'GAMEPLAY_PROJECTION_RETURN_RVA', 'effective_shadow.matrices[type]', 'std::memcmp(&native,&tracked.value,64)'):
            self.assertIn(token, camera)
        world = source[end:source.index('inline HRESULT before_ui', end)]
        self.assertIn('FAILED(hr)', world)
        self.assertIn('func!=D3DCMP_LESSEQUAL', world)
        self.assertIn('same_identity(target.p,back.p)', world)
        self.assertIn('viewport.MinZ!=0||viewport.MaxZ!=1', world)

    def test_original_ui_draw_remains_single_and_after_private_scope(self):
        source = (RENDERER / 'src/visual_wrappers.cpp').read_text()
        start = source.index('HRESULT Device8::draw_primitive_at(')
        end = source.index('HRESULT STDMETHODCALLTYPE Device8::DrawIndexedPrimitive(', start)
        draw = source[start:end]
        self.assertEqual(draw.count('real_->DrawPrimitive('), 1)
        self.assertLess(draw.index('grassintegration::before_ui('), draw.index('UiWorldScope ui'))
        self.assertIn('clean_scope_id&&ui_margins.consumer_hook_intact()', draw)

    def test_reset_and_frame_changes_invalidate_proof(self):
        source = (RENDERER / 'src/forwarders.cpp').read_text()
        for method in ('BeginScene', 'EndScene'):
            part = source[source.index('Device8::' + method):]
            body = part[:part.index('\n}')]
            self.assertIn('ground_details()', body)
            self.assertIn('proof.clear()', body)
        self.assertIn('(flags&D3DCLEAR_ZBUFFER)', source)
        self.assertIn('detail->proof.invalidate_depth()', source)
        wrappers = (RENDERER / 'src/wrappers.cpp').read_text()
        self.assertIn('detail->before_reset()', wrappers)
        self.assertIn('detail->after_reset(*real_,native_reset_called,successful)', wrappers)
        release = wrappers[wrappers.index('ULONG STDMETHODCALLTYPE Device8::Release()'):]
        self.assertLess(release.index('detail->shutdown()'), release.index('n=real_->Release()'))

    def test_restoration_failure_blocks_original_submission(self):
        source = (PORT / 'renderer/grass_native_integration.hpp').read_text()
        self.assertIn('return FAILED(restored)?restored:S_OK;', source)
        self.assertIn('if(p->transaction.has_pending())restored=p->transaction.restore(n,writer);', source)
        self.assertIn('if(FAILED(restored))p->disable("native_grass_state_restore_failed")', source)
        self.assertIn('courseintegration::after_setter(d,slot,args,hr)', source)

    def test_diagnostics_are_bounded_and_population_limit_is_explicit(self):
        source = (PORT / 'renderer/grass_native_integration.hpp').read_text()
        self.assertIn('claim_log(false)', source)
        self.assertIn('claim_log(true)||FAILED(restored)', source)
        self.assertIn('SYNTHETIC_FULL_TRIANGLE_ACTIVATION', source)
        self.assertIn('original_incremental_clip', source)
        self.assertIn('runtime_visibility', source)
        self.assertIn('consume_boundary(a.frame,a.race,a.reset)', source)


if __name__ == '__main__':
    unittest.main()
