"""Bounded object-layer integration checks; runtime visual acceptance is separate."""
from pathlib import Path
import json, os, unittest

PORT=Path(__file__).resolve().parents[1]
RENDERER=Path(os.environ.get('MRR_PC_PORT_RENDERER_ROOT',PORT/'.staging/ps2-enabled/modernization/renderer'))

class CourseObjectsIntegrationTests(unittest.TestCase):
    def test_original_data_witness_and_no_original_geometry_in_metadata(self):
        evidence=json.loads((PORT/'docs/course-objects1/source-contract.json').read_text())
        self.assertEqual(evidence['artifact']['sha256'],'2e3d6f8c90b3ed602d121f96fe7246a6fe3b70ab7c3c5d547c4bb8bf03a02b95')
        self.assertEqual(evidence['artifact']['triangle_count'],745)
        self.assertEqual(len(evidence['artifact']['source_meshes']),17)
        self.assertEqual(evidence['geometry_kind'],'SOURCE_GEOMETRY_STATIC_MATERIAL_PREVIEW')
        self.assertNotIn('vertices',evidence['artifact'])

    def test_stock_defaults_and_static_asset_never_requests_cpu_mirroring(self):
        import configparser
        ini=configparser.ConfigParser();ini.read(PORT/'PS2Port.ini.example')
        for key in ('CourseObjectsMode','CourseObjectsDiagnostics','FoliageMode','PixelProbe','ReflectionMode'):
            self.assertEqual(ini.getint('PS2Port',key),0)
        source=(PORT/'renderer/ps2_port_extension.cpp').read_text()
        start=source.index('bool PS2PortExtension::buffer_mirroring_required()')
        end=source.index('\n',start)
        self.assertNotIn('course_objects',source[start:end])
        self.assertIn('course_objects_->identity_requested()',source)

    def test_only_proven_ui_boundary_before_original_ui_native_draw(self):
        source=(RENDERER/'src/visual_wrappers.cpp').read_text()
        start=source.index('HRESULT Device8::draw_primitive_at(');end=source.index('HRESULT STDMETHODCALLTYPE Device8::DrawIndexedPrimitive(',start)
        draw=source[start:end]
        self.assertEqual(draw.count('real_->DrawPrimitive('),1)
        self.assertLess(draw.index('courseintegration::before_ui('),draw.index('UiWorldScope ui'))
        self.assertIn('clean_scope_id&&ui_margins.consumer_hook_intact()',draw)

    def test_private_draw_has_no_application_draw_tracker_submission(self):
        source=(PORT/'renderer/course_objects_native_integration.hpp').read_text()
        self.assertEqual(source.count('DrawPrimitiveUP('),1)
        self.assertNotIn('.after(71',source)
        self.assertNotIn('.after(72',source)
        self.assertNotIn('SetRenderTarget(',source)
        self.assertIn('mark_up_stream_changed()',source)

    def test_scene_depth_clear_and_camera_failure_invalidate_proof(self):
        source=(RENDERER/'src/forwarders.cpp').read_text()
        for method in ('BeginScene','EndScene'):
            part=source[source.index('Device8::'+method):]
            self.assertIn('proof.clear()',part[:part.index('\n}')])
        self.assertIn('(flags&D3DCLEAR_ZBUFFER)',source)
        self.assertIn('proof.invalidate_depth()',source)
        camera=(PORT/'renderer/course_objects_native_integration.hpp').read_text()
        start=camera.index('inline void observe_transform');end=camera.index('inline bool native_dependencies',start)
        part=camera[start:end]
        self.assertLess(part.index('p->proof.invalidate_depth()'),part.index('FAILED(hr)'))
        self.assertIn('state_block_recording=d.trace.shadow.recording||d.trace.effective_shadow.recording',camera)

    def test_reset_release_and_mutating_paths_repair_pending_state(self):
        source=(RENDERER/'src/wrappers.cpp').read_text()
        self.assertIn('course_objects()->before_reset()',source)
        self.assertIn('course_objects()->after_reset(*real_,native_reset_called,successful)',source)
        release=source[source.index('ULONG STDMETHODCALLTYPE Device8::Release()'):]
        self.assertLess(release.index('course_objects()->shutdown()'),release.index('n=real_->Release()'))
        f=(RENDERER/'src/forwarders.cpp').read_text()
        for method in ('SetRenderState','SetTexture','SetVertexShader','SetPixelShader','SetStreamSource','GetStreamSource'):
            part=f[f.index('Device8::'+method+'('):];part=part[:part.index('\n}')]
            self.assertLess(part.index('ps2_safe=repair_reflection()'),part.index('real_->'+method+'('))

if __name__=='__main__':unittest.main()
