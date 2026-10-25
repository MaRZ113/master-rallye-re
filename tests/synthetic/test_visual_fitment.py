"""Asset-free selected mechanics correction and rigid attachment invariants."""
import copy
import hashlib
import math
import struct
import unittest

from test_library import footer56, simple_record, synthetic_dx, tag7_record, tag8_record
from master_rallye.dx import parse_dx_bytes
from master_rallye.bounds import compute_bounds1339, replace_bounds1339
from master_rallye.addon_sdk.visual_fitment import attachment_point, diagnose_mechanics, translate_mechanics
from master_rallye.addon_sdk.mechanical_attachments import build_mechanical_resources, verify_mechanical_resources
from master_rallye.addon_sdk.native_brakes import validate_brake_scene


def fixture():
    points = [(0., 0., 0.), (1., 0., 0.), (0., 1., 0.),
              (.8, .02, 1.1), (.8, .35, 1.1), (.8, .35, 1.42),
              (0., .5, -1.), (.1, .5, -1.), (.1, .6, -1.),
              (0., .5, -1.), (.1, .5, -1.), (.1, .6, -1.)]
    records = [simple_record(0, 2, 0, 3), simple_record(3, 2, 3, 3),
               tag7_record('blight', simple_record(6, 2, 6, 3), 1),
               tag8_record(simple_record(9, 2, 9, 3))]
    raw = synthetic_dx(points, [0, 1, 2] * 4, records,
                       [(i*3, i*3, 3) for i in range(4)],
                       declared_count=3, trailing=footer56(points))
    definition = {'profile_version': 1, 'source_sha256': hashlib.sha256(raw).hexdigest(),
                  'provenance': 'synthetic source hubs', 'groups': [
                      {'name': 'front-positive-x', 'draw_indices': [1],
                       'source_hub_m': [.745, .18535, 1.255],
                       'target_hub_m': [.745, .15, 1.3], 'provenance': 'synthetic rest datum'}]}
    return raw, definition


class VisualFitmentTests(unittest.TestCase):
    def test_unsprung_resource_extraction_preserves_lamps_and_inverse_side_basis(self):
        hubs=[(.745,.18535,1.255),(-.745,.18535,1.255),(.745,.18535,-1.255),(-.745,.18535,-1.255)]
        points=[(0.,0.,0.),(1.,0.,0.),(0.,1.,0.)]
        for hub in hubs:
            points.extend([(hub[0]+(.03734 if hub[0]>0 else -.03734),hub[1]+dy,hub[2]+dz) for dy,dz in [(0,0),(.1,0),(0,.1)]])
        points += [(0.,.5,-1.),(.1,.5,-1.),(.1,.6,-1.)]*3
        def record(index,*,lit=False,glow=False):
            r=bytearray(simple_record(index*3,2,index*3,3,('mechanics','Null','Null')))
            r[0x20]=int(glow);r[0x22]=int(not lit)
            struct.pack_into('<I',r,0x24,1 if lit else 3)
            return bytes(r)
        records=[record(i) for i in range(5)]
        records += [tag7_record('blight',record(5),1),tag8_record(record(6,lit=True),controls=(2,2)),record(7,lit=True,glow=True)]
        raw=synthetic_dx(points,[0,1,2]*8,records,[(i*3,i*3,3) for i in range(8)],declared_count=6,trailing=footer56(points))
        model=parse_dx_bytes(raw)
        raw=replace_bounds1339(raw,compute_bounds1339(model.vertices.positions,model.collision.convex_hull,offset=model.collision.unparsed_offset),footer_offset=model.collision.unparsed_offset)
        p={'profile_version':1,'source_sha256':hashlib.sha256(raw).hexdigest(),'provenance':'synthetic callbacks','groups':[
            {'name':str(i),'draw_indices':[i+1],'source_hub_m':list(h),'target_hub_m':list(h),'provenance':'synthetic'} for i,h in enumerate(hubs)]}
        outputs,report=build_mechanical_resources(raw,raw,p,stock_brake_template=raw)
        body=parse_dx_bytes(outputs['car.dx'])
        self.assertEqual(body.vertex_count,12)
        self.assertEqual(len(body.physical_draws),4)
        validate_brake_scene(raw,outputs['car.dx'])
        for i in range(4):
            m=parse_dx_bytes(outputs[f'mechanics{i}.dx'])
            self.assertEqual(m.vertex_count,3)
            self.assertAlmostEqual(m.vertices.positions[0][0],-.03734,places=6)
            self.assertAlmostEqual(m.vertices.positions[0][1],0,places=6)
            self.assertAlmostEqual(m.vertices.positions[0][2],0,places=6)
        self.assertFalse(report['runtime_qualified'])
        corrupted=dict(outputs)
        aux=parse_dx_bytes(corrupted['mechanics0.dx']);blob=bytearray(corrupted['mechanics0.dx'])
        blob[aux.vertices.color_offset]^=1;corrupted['mechanics0.dx']=bytes(blob)
        with self.assertRaisesRegex(ValueError,'auxiliary'):
            verify_mechanical_resources(raw,corrupted,p,stock_brake_template=raw)

    def test_explicit_identity_profile_preserves_entire_file(self):
        raw, definition = fixture()
        definition['groups'][0]['target_hub_m'] = definition['groups'][0]['source_hub_m'][:]
        result, report = translate_mechanics(raw, definition)
        self.assertEqual(result, raw)
        self.assertEqual(report['changed_vertex_count'], 0)

    def test_selected_geometry_changes_without_control_or_attribute_changes(self):
        raw, definition = fixture()
        result, report = translate_mechanics(raw, definition)
        old, new = parse_dx_bytes(raw), parse_dx_bytes(result)
        self.assertEqual(report['changed_vertex_count'], 3)
        self.assertEqual(old.physical_draws, new.physical_draws)
        self.assertEqual(old.vertices.normals, new.vertices.normals)
        self.assertEqual(old.vertices.colors, new.vertices.colors)
        self.assertEqual(old.uv_sets, new.uv_sets)
        self.assertEqual(old.local_indices, new.local_indices)
        self.assertEqual(old.vertices.positions[:3], new.vertices.positions[:3])
        self.assertEqual(old.vertices.positions[6:], new.vertices.positions[6:])
        self.assertEqual(raw[old.draw_table_offset:old.collision.unparsed_offset],
                         result[new.draw_table_offset:new.collision.unparsed_offset])
        for before, after in zip(old.vertices.positions[3:6], new.vertices.positions[3:6]):
            self.assertAlmostEqual(after[0], before[0], places=6)
            self.assertAlmostEqual(after[1] - before[1], -.03535, places=6)
            self.assertAlmostEqual(after[2] - before[2], .045, places=6)
        self.assertFalse(report['runtime_qualified'])

    def test_hash_controls_duplicate_and_large_motion_fail_closed(self):
        raw, definition = fixture()
        invalid = []
        p = copy.deepcopy(definition); p['source_sha256'] = '0'*64; invalid.append(p)
        p = copy.deepcopy(definition); p['groups'][0]['draw_indices'] = [2]; invalid.append(p)
        p = copy.deepcopy(definition); p['groups'].append(copy.deepcopy(p['groups'][0])); invalid.append(p)
        p = copy.deepcopy(definition); p['groups'][0]['target_hub_m'][1] = 10; invalid.append(p)
        p = copy.deepcopy(definition); p['groups'][0]['source_hub_m'][0] = float('nan'); invalid.append(p)
        p = copy.deepcopy(definition); p['physics'] = {}; invalid.append(p)
        for value in invalid:
            with self.subTest(profile=value), self.assertRaises(ValueError):
                translate_mechanics(raw, value)

    def test_shared_vertices_cannot_move_unselected_draw(self):
        raw, definition = fixture()
        old = parse_dx_bytes(raw)
        import struct
        blob = bytearray(raw)
        struct.pack_into('<I', blob, old.physical_draws[1].core_offset + 4, 0)
        # Regenerate global table for the shared geometry to keep parser valid.
        offset = old.global_index_table.data_offset
        struct.pack_into('<3I', blob, offset + 3*4, *old.draw_global_indices(old.physical_draws[0]))
        definition['source_sha256'] = hashlib.sha256(blob).hexdigest()
        with self.assertRaisesRegex(ValueError, 'shared'):
            translate_mechanics(bytes(blob), definition)

    def test_diagnostic_never_promotes_aabb_centre_to_a_hub(self):
        raw, definition = fixture()
        report = diagnose_mechanics(raw, definition)
        row = report['groups'][0]
        self.assertEqual(row['source_hub_m'], [.745, .18535, 1.255])
        self.assertAlmostEqual(row['hub_difference_m'], math.hypot(.03535, .045))
        self.assertIn('not a hub detector', row['draws'][0]['note'])

    def test_dynamic_unsprung_pose_preserves_offset_and_excludes_spin_by_callers_choice(self):
        # A 90-degree steering rotation about Y, and +.08 m jounce.
        rotation = ((0., 0., 1.), (0., 1., 0.), (-1., 0., 0.))
        source = (.745, .18535, 1.255)
        target = (.745, .23, 1.3)
        point = (.78234, .18535, 1.255)
        result = attachment_point(point, source, target, rotation)
        self.assertAlmostEqual(result[0], target[0])
        self.assertAlmostEqual(result[1], target[1])
        self.assertAlmostEqual(result[2], target[2] - .03734)
        self.assertAlmostEqual(math.dist(result, target), math.dist(point, source))
        for bad in [((2,0,0),(0,1,0),(0,0,1)), ((-1,0,0),(0,1,0),(0,0,1))]:
            with self.assertRaises(ValueError): attachment_point(point, source, target, bad)


if __name__ == '__main__':
    unittest.main()
