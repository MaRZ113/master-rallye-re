"""SPLIT-GRASS1 source contracts; per-pass proof logic and the viewport transaction are native ctest cases."""
from pathlib import Path
import unittest

PORT=Path(__file__).resolve().parents[1]

class SplitGrassTests(unittest.TestCase):
    def setUp(self):
        self.split=(PORT/'renderer/grass_split_native.hpp').read_text()
        self.grass=(PORT/'renderer/grass_native_integration.hpp').read_text()

    def test_single_path_only_dispatches(self):
        self.assertEqual(self.grass.count('grasssplit::'),3)
        self.assertNotIn('apply_viewport',self.grass)
        self.assertNotIn('capture_viewport',self.grass)
        transform=self.grass[self.grass.index('inline void observe_transform_one'):]
        self.assertLess(transform.index('grasssplit::observe_transform('),transform.index('p->proof.invalidate_depth()'))

    def test_split_requires_split_certificate(self):
        transform=self.split[self.split.index('inline bool observe_transform'):self.split.index('inline bool observe_world_draw')]
        self.assertLess(transform.index('FAILED(hr)'),transform.index('certificate(d,single,split)'))
        self.assertIn('if(!split||!single||!cert.valid)return false;',transform)
        self.assertIn('std::memcmp(&current,&passes.projection,64)',transform)
        self.assertIn('std::memcmp(&native,&tracked.value,64)',transform)
        world=self.split[self.split.index('inline bool observe_world_draw'):self.split.index('inline HRESULT before_ui')]
        self.assertIn('cert.camera!=pass->camera',world)
        self.assertIn('func!=D3DCMP_LESSEQUAL',world)
        self.assertIn('same_identity(target.p,back.p)',world)
        self.assertIn('course_split_viewport(viewport,desc.Width,desc.Height)',world)

    def test_ui_boundary_order_and_private_draw(self):
        ui=self.split[self.split.index('inline HRESULT before_ui'):]
        self.assertLess(ui.index('boundary_consumed('),ui.index('certificate(d,single,split)'))
        self.assertLess(ui.index('boundary_consumed('),ui.index('GetRenderTarget('))
        self.assertIn('course_split_admission(a,passes,p->course())',ui)
        self.assertEqual(ui.count('DrawPrimitiveUP('),1)
        self.assertNotIn('.after(71',ui);self.assertNotIn('.after(72',ui);self.assertNotIn('SetRenderTarget(',ui)
        order=['transaction.capture(n)','capture_viewport(n)','apply_viewport(n,pass.viewport,writer)',
               'identity,pass.projection,writer','mark_up_stream_changed()','DrawPrimitiveUP(','transaction.restore(n,writer)']
        positions=[ui.index(token) for token in order]
        self.assertEqual(positions,sorted(positions))
        self.assertIn('CourseObjectMaterialState{FALSE,D3DTADDRESS_CLAMP,D3DTADDRESS_CLAMP}',ui)
        self.assertIn('return result;',ui)

    def test_viewport_slot_is_tracked(self):
        tx=(PORT/'renderer/course_object_transaction.hpp').read_text()
        self.assertIn('kSetViewportSlot=40',tx)
        names=(PORT.parents[1]/'modernization/renderer/include/method_names.hpp').read_text().split('METHOD_NAMES[] = {',1)[1]
        self.assertEqual([n.strip().strip('"') for n in names.split(',')][40],'SetViewport')

if __name__=='__main__':unittest.main()
