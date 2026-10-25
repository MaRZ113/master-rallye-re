import copy,hashlib,unittest
from master_rallye.dx import parse_dx_bytes
from master_rallye.glass_authoring import redistribute_glass
from master_rallye.topology_writer import source_geometry
from tests.synthetic.test_library import simple_record,synthetic_dx,footer56,tag7_record,tag8_record


def fixture():
    tri=[(0.,0.,0.),(1.,0.,0.),(0.,1.,0.)]
    points=tri+tri+[(0.,0.,1.),(1.,0.,1.),(0.,1.,1.)]+tri+tri
    glass=('intact-tga','glass-tga','Null');broken=('broken-tga','glass-tga','Null')
    plain=('synthetic-tga','Null','Null')
    records=[simple_record(0,2,0,3,plain),tag7_record('screenfront',simple_record(3,5,3,6,glass),1),tag8_record(simple_record(9,2,9,3,broken)),simple_record(12,2,12,3,plain)]
    raw=synthetic_dx(points,[0,1,2,0,1,2,3,4,5,0,1,2,0,1,2],records,[(0,0,3),(3,3,6),(9,9,3),(12,12,3)],declared_count=3,trailing=footer56(points))
    return raw,{'source_sha256':hashlib.sha256(raw).hexdigest(),'source_draw':1,'panes':[{'label':'screenfront','intact_draw':1,'broken_draw':2,'triangles':[0],'broken_uv_axes':[0,1]}],'static':{'draw':0,'triangles':[1]}}


class GlassAuthoringTests(unittest.TestCase):
    def test_preview_per_pane_cases_are_explicit_and_bounded(self):
        import json,struct,tempfile
        from pathlib import Path
        from master_rallye.preview_scene import stage_vehicle
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);raw,_=fixture();(r/'car.dx').write_bytes(raw)
            m=parse_dx_bytes(raw)
            for d in m.physical_draws:
                for name in d.texture_tuple:
                    if name!='Null':(r/(name+'.dxt')).write_bytes(struct.pack('<5I',0xfeed,1,0,1,1)+b'\xff'*4)
            p=r/'profile.json';p.write_text(json.dumps({'glass_states':{'screenfront':2}}))
            stage_vehicle(r/'car.dx',r/'scene.mrpv',profile=p)
            report=json.loads((r/'scene.json').read_text());self.assertEqual(report['draws'],3)
            for states in ({'screenfront':3},{'screenfront':True},{'screenrear':2}):
                p.write_text(json.dumps({'glass_states':states}))
                with self.assertRaises(ValueError):stage_vehicle(r/'car.dx',r/'scene.mrpv',profile=p)

    def test_complete_allocation_preserves_controls_collision_and_unrelated_draw(self):
        raw,p=fixture();data,report=redistribute_glass(raw,p);a,b=map(parse_dx_bytes,(raw,data))
        self.assertTrue(report['outside_target_geometry_preserved']);self.assertFalse(report['runtime_qualified'])
        self.assertEqual([d.control_words for d in a.physical_draws],[d.control_words for d in b.physical_draws])
        self.assertEqual(raw[a.trailing.offset:],data[b.trailing.offset:])
        g=source_geometry(b);self.assertEqual([len(g[i].triangles) for i in range(4)],[1,1,1,1])
        self.assertEqual(b.physical_draws[0].texture_tuple,a.physical_draws[1].texture_tuple)
        self.assertEqual(b.physical_draws[3].texture_tuple,a.physical_draws[3].texture_tuple)
        self.assertEqual(data,redistribute_glass(raw,p)[0])

    def test_rejects_coverage_duplicates_missing_and_wrong_case(self):
        raw,p=fixture()
        for change in ('duplicate','missing','case','hash'):
            q=copy.deepcopy(p)
            if change=='duplicate':q['static']['triangles']=[0]
            if change=='missing':q['static']['triangles']=[]
            if change=='case':q['panes'][0]['intact_draw'],q['panes'][0]['broken_draw']=2,1
            if change=='hash':q['source_sha256']='0'*64
            with self.assertRaises(ValueError):redistribute_glass(raw,q)

    def test_roster_repair_cannot_target_unknown_or_stock(self):
        from tools.build_sdk_roster import apply_base_glass_profiles
        for profiles in ([],{'stock':'irrelevant'},{1:'irrelevant'}):
            with self.assertRaises(ValueError):apply_base_glass_profiles({},[],profiles)
