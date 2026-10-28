"""Stable quality gates and isolated source-backed upper lamp partition."""
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from master_rallye.topology_writer import CompiledVertex,DrawGeometry
from master_rallye.scene_dx_writer import ScenePart
from master_rallye.fourrunner_upper_lamp import author
from master_rallye.source_garage_pilot import create_pilot
from master_rallye.fourrunner_visual_kit import options,OPTIONS


def fixture():
    vertices=[]
    for u,v in ((0.,448.),(120.,448.),(120.,458.),(0.,458.)):
        vertices.append(CompiledVertex(((60-u)*.008,1.27+(458-v)*.009,-2.1),(0.,0.,-1.),bytes([255]*4),((u/512,v/512),)))
    body=ScenePart(DrawGeometry(tuple(vertices),((0,1,2),(0,2,3))),('body','Null','Null'))
    lower=replace(body,geometry=replace(body.geometry,vertices=tuple(replace(v,position=(v.position[0],.5,v.position[2]))for v in vertices)))
    ledger={'source_scene_sha256':'05cb2b9db5b3c103cd623b8c1282099ac9f1f1f93593ad95d8243003f41e33dd',
            'body_partition_ledger':[{'source_triangle':i,'barycentric':[(1.,0.,0.),(0.,1.,0.),(0.,0.,1.)]}for i in (595,596)]}
    return [body,lower],ledger


class StabilizationTests(unittest.TestCase):
    def test_all_five_rejected_before_reading_source_or_creating_output(self):
        for key in OPTIONS:
            with tempfile.TemporaryDirectory()as tmp:
                out=Path(tmp)/'output'
                with patch('master_rallye.source_garage_pilot.uvs.load_scene')as read,self.assertRaisesRegex(ValueError,'Owner-rejected'):
                    create_pilot(Path(tmp)/'missing',Path(tmp),Path(tmp)/'missing.sma',out,visual_options={key:True})
                read.assert_not_called();self.assertFalse(out.exists())

    def test_default_and_explicit_options_off_are_identical(self):
        self.assertEqual(options(None),dict.fromkeys(OPTIONS,False))
        self.assertEqual(options({}),options(None))
        self.assertEqual(options(dict.fromkeys(OPTIONS,False)),options(None))

    def test_upper_option_off_conserves_every_part_identity(self):
        parts,report=fixture();before=repr(parts)
        result,evidence=author(parts,1,report)
        self.assertEqual(result,parts);self.assertIs(result[0],parts[0]);self.assertEqual(repr(parts),before)
        self.assertFalse(evidence['enabled'])

    def test_upper_option_retains_lower_triangles_exact_and_original_uv_provenance(self):
        parts,report=fixture();before=repr(parts);out,evidence=author(parts,1,report,enabled=True)
        lower=parts[1].geometry;merged=out[1].geometry
        self.assertEqual(merged.vertices[:len(lower.vertices)],lower.vertices)
        self.assertEqual(merged.triangles[:len(lower.triangles)],lower.triangles)
        self.assertEqual(repr(parts),before)
        count=evidence['triangles'];self.assertGreater(count,0)
        self.assertEqual(len(evidence['source_ledger']['inside']),count)
        self.assertEqual(out[0].textures,parts[0].textures);self.assertEqual(out[1].textures,parts[1].textures)
        self.assertFalse(out[0].environment);self.assertFalse(out[0].alpha)
        for row,tri in zip(evidence['source_ledger']['inside'],merged.triangles[-count:]):
            original=parts[0].geometry;source=original.triangles[row['source_triangle']-595]
            for weights,index in zip(row['barycentric'],tri):
                v=merged.vertices[index]
                for axis in range(3):
                    self.assertAlmostEqual(v.position[axis],sum(weights[j]*original.vertices[source[j]].position[axis]for j in range(3)))
                self.assertGreaterEqual(v.uvs[0][0]*512,50.-1e-8);self.assertLessEqual(v.uvs[0][0]*512,70.+1e-8)
        self.assertEqual(author(parts,1,report,enabled=True),(out,evidence))

    def test_unqualified_source_missing_faces_and_wrong_spatial_plane_fail_closed(self):
        parts,report=fixture()
        with self.assertRaisesRegex(ValueError,'qualified source'):author(parts,1,{**report,'source_scene_sha256':'bad'},enabled=True)
        with self.assertRaisesRegex(ValueError,'ledger mismatch'):author(parts,1,{**report,'body_partition_ledger':[]},enabled=True)
        bad=replace(parts[0],geometry=replace(parts[0].geometry,vertices=tuple(replace(v,position=(v.position[0],v.position[1]+.5,v.position[2]))for v in parts[0].geometry.vertices)))
        with self.assertRaisesRegex(ValueError,'escapes'):author([bad,parts[1]],1,report,enabled=True)
        with self.assertRaisesRegex(ValueError,'boolean'):author(parts,1,report,enabled=1)
