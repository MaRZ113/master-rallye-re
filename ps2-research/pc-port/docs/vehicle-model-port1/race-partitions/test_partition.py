import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('partition_audit',HERE/'audit.py')
audit=importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class PartitionTests(unittest.TestCase):
    def test_unsigned_key_does_not_change_original_winding(self):
        face=((0.,0.,0.),(1.,0.,0.),(0.,1.,0.))
        self.assertEqual(audit.face_hash(face),audit.face_hash((face[2],face[1],face[0])))
        self.assertEqual(audit.face_hash(face),audit.face_hash((face[1],face[2],face[0])))
        self.assertEqual(audit.ordered_runs(['carshiny','carflat','carshiny']),[
            {'first_source_face':0,'source_face_count':1,'category':'carshiny'},
            {'first_source_face':1,'source_face_count':1,'category':'carflat'},
            {'first_source_face':2,'source_face_count':1,'category':'carshiny'}])

    def test_unknown_and_conflicting_materials_fail_closed(self):
        self.assertEqual(audit.classification([]),'UNMATCHED')
        self.assertEqual(audit.classification([{'category':'carshiny'},{'category':'carflat'}]),'AMBIGUOUS')
        self.assertEqual(audit.classification([{'category':'carshiny'},{'category':'carshiny'}]),'carshiny')

    def test_runtime_reordering_and_multiplicity(self):
        keys=['a','a','b'];digest=hashlib.sha256('aab'.encode('ascii')).hexdigest()
        counts={'a':{'multiplicity':2,'category':'carshiny'},'b':{'multiplicity':1,'category':'carflat'}}
        self.assertEqual(audit.classify_runtime_hashes(digest,counts,keys),[
            {'first_source_face':0,'source_face_count':2,'category':'carshiny'},
            {'first_source_face':2,'source_face_count':1,'category':'carflat'}])
        self.assertEqual(len(audit.classify_runtime_hashes(digest,counts,['a','b','a'])),3)
        self.assertIsNone(audit.classify_runtime_hashes(digest,counts,['a','b']))
        self.assertIsNone(audit.classify_runtime_hashes(digest,counts,['a','b','b']))
        self.assertIsNone(audit.classify_runtime_hashes(digest,counts,['a','a','c']))
        counts['a']['category']='AMBIGUOUS'
        self.assertIsNone(audit.classify_runtime_hashes(digest,counts,keys))

    def test_original_records_keep_material_separation(self):
        report=json.loads((HERE/'partition-evidence.json').read_text())
        cases={(v['pc_family'],d['draw_index']):d for v in report['vehicles'] for d in v['draws']}
        self.assertEqual(report['tolerance'],.001)
        self.assertEqual(cases['Xtrail',1]['source_face_counts'],{'carflat':14,'carshiny':195})
        self.assertEqual(cases['Xtrail',1]['source_ordered_runs'],[
            {'first_source_face':0,'source_face_count':195,'category':'carshiny'},
            {'first_source_face':195,'source_face_count':14,'category':'carflat'}])
        self.assertEqual(cases['ChevyBlazer',7]['source_face_counts'],{'carglass':10,'carshiny':60})
        self.assertEqual(cases['LandCruiser',8]['source_face_counts']['UNMATCHED'],25)
        self.assertEqual(cases['LandCruiser',9]['source_face_counts']['UNMATCHED'],104)
        self.assertEqual(cases['Bruno',4]['source_face_counts']['UNMATCHED'],3)
        self.assertEqual(cases['SeatBuggy',7]['source_face_counts']['UNMATCHED'],4)
        forester=next(v for v in report['vehicles'] if v['pc_family']=='Forester')
        self.assertEqual(forester['ps2_family'],'WOOLDAND')
        self.assertEqual(cases['Forester',9]['source_face_counts'],{'UNTAGGED_AUTHORED_MAPS':28,'carshiny':43})

    def test_runtime_ordinal_is_never_geometry_proof(self):
        report=json.loads((HERE/'runtime-evidence.json').read_text())
        self.assertEqual(report['exact_current_hash_events'],[])
        self.assertTrue(report['layout_only_candidates'])
        self.assertTrue(all(r['classification']=='LAYOUT_ONLY_NOT_GEOMETRY_IDENTITY'
                            for r in report['layout_only_candidates']))


if __name__=='__main__':unittest.main()
