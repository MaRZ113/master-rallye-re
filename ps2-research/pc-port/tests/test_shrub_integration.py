"""Integration safety checks supplement native two-category/resource tests."""
import configparser,json,os,unittest
from pathlib import Path
PORT=Path(__file__).resolve().parents[1]
STAGE=Path(os.environ.get('MRR_PC_PORT_RENDERER_ROOT',PORT/'.staging/ps2-enabled/modernization/renderer'))
class ShrubIntegrationTests(unittest.TestCase):
    def test_independent_stock_defaults(self):
        cfg=configparser.ConfigParser();cfg.read(PORT/'PS2Port.ini.example')
        self.assertEqual(cfg.getint('PS2Port','Grass'),0)
        self.assertEqual(cfg.getint('PS2Port','Shrubs'),0)
        self.assertEqual(cfg.getint('PS2Port','Diagnostics'),0)

    def test_second_category_owns_its_proof_transaction_and_texture(self):
        s=(PORT/'renderer/ps2_port_extension.cpp').read_text()
        self.assertIn('std::make_unique<GrassPilot>(build_valid_, ini,GroundDetailKind::Shrubs)',s)
        self.assertIn('(shrubs_ && (shrubs_->blocked() || shrubs_->transaction.has_pending()))',s)
        h=(PORT/'renderer/grass_native_integration.hpp').read_text()
        self.assertIn('before_ui_one(d,p,ui_callsite,ui_consumer)',h)
        self.assertIn('course_world_preflight(p->proof,boundary)',h)
        self.assertIn('p->boundary_consumed(',h)
        self.assertIn('quote(p->artifact_sha())',h)
        self.assertEqual(h.count('DrawPrimitiveUP('),1) # Shared producer, called independently per admitted category.

    def test_all_categories_invalidate_on_scene_depth_target_and_reset(self):
        f=(STAGE/'src/forwarders.cpp').read_text()
        for method in ('BeginScene','EndScene','Clear','SetRenderTarget'):
            body=f[f.index('Device8::'+method):];body=body[:body.index('\n}')]
            self.assertIn('ground_details()',body)
            self.assertIn('detail->proof.',body)
        w=(STAGE/'src/wrappers.cpp').read_text()
        for op in ('before_reset()','after_reset(*real_,native_reset_called,successful)','shutdown()'):
            self.assertIn('detail->'+op,w)

    def test_grass_working_source_hash_and_first_type_remain_pinned(self):
        previous=json.loads((PORT/'docs/grass-port1/source-contract.json').read_text())
        header=(PORT/'renderer/grass_pilot.hpp').read_text()
        self.assertIn(previous['artifact']['sha256'],header)
        self.assertIn(previous['artifact']['gxi_sha256'],header)
        new=json.loads((PORT/'docs/grass-port2/source-contract.json').read_text())
        self.assertNotEqual(new['artifact']['sha256'],previous['artifact']['sha256'])
        self.assertIn(new['artifact']['sha256'],header)
        self.assertIn(new['artifact']['gxi_sha256'],header)
        self.assertNotEqual(new['artifact']['gxi_sha256'],previous['artifact']['gxi_sha256'])

if __name__=='__main__':unittest.main()
