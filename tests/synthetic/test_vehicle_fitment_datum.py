from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from diagnose_vehicle_fitment import source_rest_datum
import hashlib
from types import SimpleNamespace
from unittest.mock import patch
import xml.etree.ElementTree as ET
from render_vehicle_fitment_overlay import render


def rows(y=-.05,target=.1452):
    return [{'axle':axle,'positive_x':side==1,'native_attachment':[side*.85,y,sign*1.4],
             'source_reference_hub':[side*.70,target,sign*1.25]}
            for axle,sign in [('Front',1),('Rear',-1)] for side in (1,-1)]


class FitmentDatumTests(unittest.TestCase):
    def test_source_derived_reference_not_fixed_value(self):
        self.assertAlmostEqual(source_rest_datum(rows())['Front'],-.1952)
        self.assertAlmostEqual(source_rest_datum(rows(y=.02,target=.12))['Rear'],-.1)

    def test_native_sign_and_reapplication(self):
        baseline=rows();reference=source_rest_datum(baseline)
        for row in baseline:row['native_attachment'][1]-=reference[row['axle']]
        self.assertEqual(source_rest_datum(baseline),{'Front':0.,'Rear':0.})

    def test_ambiguity_and_budget_rejected(self):
        bad=rows();bad[0]['source_reference_hub'][1]+=.02
        with self.assertRaises(ValueError):source_rest_datum(bad)
        with self.assertRaises(ValueError):source_rest_datum(rows(target=1.))
        with self.assertRaises(ValueError):source_rest_datum(rows()[:3])

    def test_overlay_model_pin(self):
        with self.assertRaises(ValueError):render(b'fixture',{'model_sha256':'0'*64})

    def test_overlay_deterministic_and_explicit_static_boundary(self):
        report={'family':'Test & vehicle','model_sha256':hashlib.sha256(b'fixture').hexdigest(),
                'collision_aabb_m':[[-1,0,-2],[1,1,2]],'rows':rows()}
        for row in report['rows']:row.update(physical_radius_m=.38,visual_radial_envelope_m=.3652)
        model=SimpleNamespace(diagnostics=SimpleNamespace(validated=True),vertices=SimpleNamespace(positions=[(-1,0,-2),(1,0,-2),(0,1,2)]),
                              physical_draws=[object()],draw_global_indices=lambda _: [0,1,2])
        with patch('render_vehicle_fitment_overlay.parse_dx_bytes',return_value=model):
            svg=render(b'fixture',report);self.assertEqual(svg,render(b'fixture',report))
        ET.fromstring(svg)
        self.assertIn('Test &amp; vehicle',svg)
        self.assertIn('no tyre contact',svg)


if __name__=='__main__':unittest.main()
