"""Source-free Silver policy regression: topology ownership, alpha and datum."""
import copy
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from master_rallye import paris_dakar_silver_pilot as pilot
from master_rallye import universal_vehicle_scene as uvs
from master_rallye.scene_dx_writer import ScenePart
from master_rallye.topology_writer import CompiledVertex,DrawGeometry
from master_rallye.workshop.source_garage_ui import native_creation_available
from tests.synthetic.test_universal_vehicle_scene import fixture


def geometry(count,*,lamp=False):
    vertices=[];triangles=[]
    for i in range(count):
        start=len(vertices)
        # Lamp triangles span repeated V tiles, deliberately covering all lens
        # and non-lens areas. Geometry is synthetic, not a donor resource.
        for x,y in ((0.,0.),(1.,0.),(0.,1.)):
            vertices.append(CompiledVertex((x,y,float(i)),(0.,0.,1.),bytes((255,255,255,255)),((x,y+1 if lamp else y),)))
        triangles.append((start,start+1,start+2))
    return DrawGeometry(tuple(vertices),tuple(triangles))


def result():
    return {'report':{'source_scene_sha256':pilot.SCENE_SHA256,
            'body_draws':[{'mesh_id':key,'draw_index':i}for i,key in enumerate(('r0001-mat-01','r0001-mat-02','r0001-mat-06'))]},
        'body_parts':[ScenePart(geometry(8,lamp=True),('lamp','Null','Null')),
                      ScenePart(geometry(1),('body','Null','Null')),
                      ScenePart(geometry(38),('window','Null','Null'),alpha=True)]}


def area(g):
    total=0.
    for t in g.triangles:
        a,b,c=[g.vertices[i].position for i in t]
        u=[b[k]-a[k]for k in range(3)];v=[c[k]-a[k]for k in range(3)]
        total+=math.hypot(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])/2
    return total


class SilverPolicyTests(unittest.TestCase):
    def test_exact_profile_guard_rejects_other_self_consistent_scene(self):
        with tempfile.TemporaryDirectory()as temp:
            base=Path(temp);source=base/'source';source.mkdir();scene,assets=fixture(source)
            uvs.save_scene(scene,base/'scene',assets)
            with self.assertRaisesRegex(ValueError,'exact reviewed'):pilot.pilot_profile(base/'scene/scene.json')
            self.assertFalse((base/'output').exists())

    def test_profile_has_common_origin_only_and_explicit_submicrometre_symmetry(self):
        scene={'source':{'catalog':'Data/PajeroSilver.tc','container_sha256':pilot.TC_SHA256},'materials':[{'id':'r0001-mat-06'}],
               'nodes':[{'id':'body','role':'body','visible':True,'mesh_ids':['mesh']}]}
        with patch.object(pilot.uvs,'load_scene',return_value=scene),patch.object(pilot.uvs,'read_bounded',return_value=b'synthetic'),patch.object(pilot,'SCENE_SHA256',uvs.sha(b'synthetic')):
            profile=pilot.pilot_profile(Path('synthetic'))
        self.assertAlmostEqual(uvs.determinant(profile['authoring_transform']),1.)
        self.assertEqual(profile['authoring_transform'][7],-.63896)
        hubs=profile['hub_overrides'];self.assertAlmostEqual(hubs['front_left'][2]-hubs['rear_left'][2],2.52778)
        self.assertAlmostEqual(hubs['front_left'][0]-hubs['front_right'][0],1.622151)
        self.assertEqual(hubs['front_left'][1],-.05)
        self.assertNotIn('alpha_override',profile['materials']['r0001-mat-06'])
        self.assertEqual(profile['materials']['r0001-mat-06']['mode'],'alpha_blend')

    def test_only_exact_silver_catalog_opens_native_ui_gate(self):
        scene={'metadata':{'adapter':'paris-dakar-source/1'},'source':{'catalog':'Data/PajeroSilver.tc','container_sha256':pilot.TC_SHA256}}
        self.assertTrue(native_creation_available(scene))
        for key,value in [('catalog','Data/PajeroRED.tc'),('container_sha256','0'*64)]:
            wrong=copy.deepcopy(scene);wrong['source'][key]=value;self.assertFalse(native_creation_available(wrong))

    def test_headlight_alpha_preserved_and_never_assigned_glass_damage(self):
        source=result();before=copy.deepcopy(source);parts,panes,lamp,core,report=pilot.semantic_parts(source)
        head=next(p for p in parts if p.textures[0]=='window'and len(p.geometry.triangles)==22)
        self.assertTrue(head.alpha);self.assertFalse(head.alpha_test)
        self.assertEqual([len(parts[i].geometry.triangles)for i in panes.values()],[8,4,4])
        self.assertEqual(report['headlight_source_triangles'],list(range(22)))
        selected=[i for rows in report['panes'].values()for i in rows]
        self.assertEqual(sorted(selected),list(range(22,38)))
        self.assertEqual(source,before);self.assertNotIn('screenrear',panes)
        self.assertTrue(all(parts[i].textures[0]=='body'for i in core))

    def test_lamp_cut_conserves_area_attributes_and_barycentric_provenance(self):
        source=result();parts,panes,lamp,_,report=pilot.semantic_parts(source)
        all_lamps=[p for p in parts if p.textures[0]=='lamp']
        self.assertAlmostEqual(sum(area(p.geometry)for p in all_lamps),area(source['body_parts'][0].geometry),places=9)
        selected=parts[lamp].geometry
        for t,row in zip(selected.triangles,report['brake_source_triangle_ledger']):
            original=source['body_parts'][0].geometry
            triangle=[original.vertices[i]for i in original.triangles[row['source_triangle']]]
            for index,weights in zip(t,row['barycentric']):
                v=selected.vertices[index];self.assertAlmostEqual(sum(weights),1.)
                for axis in range(3):self.assertAlmostEqual(v.position[axis],sum(weights[k]*triangle[k].position[axis]for k in range(3)))
                u,w=v.uvs[0];w%=1.
                self.assertTrue(any(u0-1e-8<=u<=u1+1e-8 and v0-1e-8<=w<=v1+1e-8 for u0,v0,u1,v1 in pilot.LENS_RECTS))
        self.assertTrue(report['ordinary_lamp_source_triangle_ledger'])

    def test_semantics_deterministic_and_fail_closed_on_hash_or_topology(self):
        self.assertEqual(pilot.semantic_parts(result()),pilot.semantic_parts(result()))
        changed=result();changed['report']['source_scene_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'Unqualified'):pilot.semantic_parts(changed)
        changed=result();changed['body_parts'][2]=ScenePart(geometry(37),('window','Null','Null'),alpha=True)
        with self.assertRaisesRegex(ValueError,'topology'):pilot.semantic_parts(changed)

    def test_physics_is_independent_pajero_and_not_source_solver_values(self):
        with patch('master_rallye.addon_sdk.project.read_sma_member',return_value=b'synthetic'):
            physics=pilot._physics(Path('synthetic.sma'))
        self.assertEqual((physics['donor_family'],physics['runtime_family']),('Pajero','PDSilver'))
        values=physics['overrides']['DataGame/vehicles.xml']
        self.assertEqual(values['Dimensions/WheelRadiusFront'],.390497)
        self.assertFalse(any('RideHeight'in k or 'Mass'in k or 'DriveType'in k for k in values))


if __name__=='__main__':unittest.main()
