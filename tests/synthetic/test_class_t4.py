import unittest
import xml.etree.ElementTree as ET

from master_rallye.addon_sdk.roster_layout import resolve_layout, BASE
from master_rallye.addon_sdk.collection import reserve_roster
from master_rallye.dakar2_classic_pilot import orient
from master_rallye.topology_writer import CompiledVertex, DrawGeometry
from tools.roster_scene_layout import reorder_scene
from tools.prepare_sdk_capacity_probe import scene_append
import tools.sdk_capacity_native as native


def rows():
    spec = [(28, 'T2', 8), (29, 'T2', 9), (30, 'T2', 10), (31, 'T2', 11), (32, 'T3', 12), (33, 'T4', 0), (34, 'T4', 1)]
    return [{'physical_id': i, 'vehicle_class': c, 'class_local_index': n,
             'frontend': {'vehicle_select_art': {'frame': i + 100}}} for i, c, n in spec]


def order():
    return {'T1': BASE['T1'][:], 'T2': [7, 8, 30, 9, 10, 11, 12, 31, 13, 27, 28, 29],
            'T3': [14, 32] + list(range(15, 26)), 'T4': [34, 33]}


class ClassT4LayoutTests(unittest.TestCase):
    def test_fourth_frontend_class_maps_without_renumbering(self):
        layout = resolve_layout(rows(), order())
        self.assertEqual(layout['canonical']['T4'], [33, 34])
        self.assertEqual(layout['class_to_physical_ids']['T4'], [34, 33])
        self.assertEqual(layout['physical_id_to_class_local']['33'], {'vehicle_class': 'T4', 'class_local_index': 1})
        self.assertEqual([len(v) for v in layout['class_to_physical_ids'].values()], [8, 12, 13, 2])

    def test_t4_must_be_declared_consistently(self):
        without = order(); del without['T4']
        with self.assertRaises(ValueError): resolve_layout(rows(), without)
        empty = order(); empty['T4'] = []
        with self.assertRaises(ValueError): resolve_layout(rows()[:5], empty)
        foreign = order(); foreign['T4'] = [33, 32]; foreign['T3'].remove(32); foreign['T3'].append(34)
        with self.assertRaises(ValueError): resolve_layout(rows(), foreign)

    def test_reservations_start_t4_at_local_zero(self):
        slots = [{'physical_id': 33, 'vehicle_class': 'T4', 'class_local_index': 0}]
        lock, active = reserve_roster([{'addon_id': 'd2pajero', 'vehicle_class': 'T4', 'physical_id': 33}], slots=slots)
        self.assertEqual(active[0]['class_local_index'], 0)

    def test_widgets_use_xy_row_three_after_last_t3(self):
        text = '<Scene>\n'
        for cls, ids in BASE.items():
            for n, physical in enumerate(ids):
                text += f'<Egg Name="{cls}_Car{n+1}">\n'
                for key, value in [('en2d Image Bank Index', physical + 100), ('True Value', physical + 100), ('X ID', n),
                                   ('Y ID', {'T1': 0, 'T2': 1, 'T3': 2}[cls]), ('XPos*', f'Frontend/VehicleSelect/Button{n}XPos')]:
                    text += f'<Value Name="{key}" Value="{value}"/>\n'
                text += '</Egg>\n'
        raw = scene_append((text + '</Scene>').encode(), rows())
        tree = ET.fromstring(reorder_scene(raw, resolve_layout(rows(), order())))
        names = [e.get('Name') for e in tree.iter('Egg')]
        self.assertEqual(names[-2:], ['T4_Car1', 'T4_Car2'])
        for n, physical in enumerate(order()['T4']):
            egg = next(e for e in tree.iter('Egg') if e.get('Name') == f'T4_Car{n+1}')
            values = {v.get('Name'): v.get('Value') for v in egg}
            self.assertEqual((values['Y ID'], values['X ID'], values['en2d Image Bank Index']), ('3', str(n), str(physical + 100)))


class ClassT4NativeTests(unittest.TestCase):
    def test_relocated_object_layout(self):
        self.assertEqual([native._relocate(d) for d in (0x14, 0x18, 0x1c, 0x20, 0x24, 0x28)], [0x34, 0x38, 0x3c, 0x44, 0x48, 0x4c])
        self.assertEqual(native.T4_COUNT + 12 + 4, native.T4_OBJECT_SIZE)
        for bad in (0x10, 0x2c, 0x30):
            with self.assertRaises(ValueError): native._relocate(bad)
        sites = [va for va, _ in native.T4_DISPLACEMENTS]
        self.assertEqual(len(sites), len(set(sites)))


def vertex(p, n):
    return CompiledVertex(p, n, b'\xff\xff\xff\xff', ((0., 0.),))


class OrientationTests(unittest.TestCase):
    def test_triangles_follow_source_normals(self):
        up = (0., 1., 0.)
        g = DrawGeometry((vertex((0, 0, 0), up), vertex((0, 0, 1), up), vertex((1, 0, 0), up)), ((0, 2, 1),))
        out, stats = orient(g)
        a, b, c = (out.vertices[i].position for i in out.triangles[0])
        cross = ((b[1]-a[1])*(c[2]-a[2])-(b[2]-a[2])*(c[1]-a[1]), (b[2]-a[2])*(c[0]-a[0])-(b[0]-a[0])*(c[2]-a[2]),
                 (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
        self.assertGreater(cross[1], 0); self.assertEqual(stats['flipped'] + stats['kept'], 1)

    def test_undecided_triangle_is_two_sided(self):
        side = (1., 0., 0.)
        g = DrawGeometry((vertex((0, 0, 0), side), vertex((0, 0, 1), side), vertex((1, 0, 0), side)), ((0, 1, 2),))
        out, stats = orient(g)
        self.assertEqual(stats['two_sided'], 1); self.assertEqual(len(out.triangles), 2); self.assertEqual(len(out.vertices), 6)
        self.assertEqual(out.vertices[3].normal, (-1., -0., -0.))


if __name__ == '__main__':
    unittest.main()
