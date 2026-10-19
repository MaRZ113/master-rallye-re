"""Tests for the pure parts of collision_diag: column classification, connected regions, candidate ranking."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import collision_diag as cd  # noqa: E402


class ClassifyTests(unittest.TestCase):
    def test_classes(self):
        c = cd.classify
        self.assertEqual(c(10, 10.0, False, 10.1, False, False), 'agree')
        self.assertEqual(c(10, None, False, None, False, False), 'agree')
        self.assertEqual(c(10, 10.0, False, None, False, False), 'missing_support')
        self.assertEqual(c(10, 10.0, False, 9.0, False, False), 'missing_support')
        self.assertEqual(c(10, 10.0, False, 11.0, False, False), 'invisible_block')
        self.assertEqual(c(10, 10.0, False, 16.0, True, False), 'invisible_block')   # patched query starts inside solid
        self.assertEqual(c(10, None, False, 10.0, False, False), 'ps2_void')
        self.assertEqual(c(10, 10.0, False, 30.0, False, True), 'ps2_exterior')      # exterior wins over everything
        self.assertEqual(c(10, 10.0, False, 10.0 + cd.TOL, False, False), 'agree')    # tolerance is inclusive

    def test_components_are_eight_connected_and_sorted(self):
        cells = {(0, 0), (1, 1), (5, 5), (5, 6), (9, 9)}
        comps = cd.components(cells)
        self.assertEqual([len(x) for x in comps], [2, 2, 1])
        self.assertEqual(comps[0], [(0, 0), (1, 1)])


def region(**kw):
    base = {'class': 'invisible_block', 'columns': 10, 'area_units2': 360, 'unresolved_columns_without_ps2_or_patched_surface': 0, 'multilayer_columns': 0,
            'overhang_columns': 0, 'bsp_second_surface_columns': 0, 'distance_to_raceline': 40.0, 'distance_to_converted_object': 500.0,
            'isolation_to_next_region': 100.0, 'error_new_mean_abs': 1.5, 'error_new_max_abs': 2.0, 'centroid_xz': [0.0, 0.0],
            'bounds_xz': [0, 0, 6, 6], 'retail_class_counts': {}, 'probes': [], '_columns': []}
    base.update(kw)
    return base


class RankTests(unittest.TestCase):
    def test_eligibility_rules(self):
        cols = {}
        bad = [region(columns=2), region(columns=80), region(unresolved_columns_without_ps2_or_patched_surface=1), region(multilayer_columns=1),
               region(bsp_second_surface_columns=1), region(distance_to_raceline=120.0), region(distance_to_converted_object=20.0),
               region(isolation_to_next_region=10.0), region(error_new_mean_abs=0.1)]
        self.assertEqual(cd.rank(bad, 6.0, cols), [])
        for r in bad:
            self.assertTrue(r['ineligible_reasons'])

    def test_exterior_free_first(self):
        near_exterior = region(centroid_xz=[0.0, 0.0], isolation_to_next_region=200.0, error_new_mean_abs=3.0)
        clean = region(centroid_xz=[1000.0, 0.0], isolation_to_next_region=60.0, error_new_mean_abs=0.8)
        cols = {(0, 0): {'x': 10.0, 'z': 0.0, 'class_new': 'ps2_exterior'}, (1, 0): {'x': 1010.0, 'z': 0.0, 'class_new': 'agree'}}
        ranking = cd.rank([near_exterior, clean], 6.0, cols)
        self.assertEqual([r['exterior_free_within_36_units'] for r in ranking], [True, False])
        self.assertEqual([r['rank'] for r in ranking], [1, 2])
        self.assertGreater(ranking[1]['score'], ranking[0]['score'] - 1000)


class GrazingLeafTests(unittest.TestCase):
    def test_zero_thickness_solid_leaf_is_not_a_surface(self):
        class N:
            def __init__(self, plane=None, f0=1, child=None, sibling=None):
                self.plane, self.field_0, self.child, self.sibling, self.payload = plane, f0, child, sibling, None
        def column(lower):
            # root: y = 0.5 (front empty); back: plane y = lower (front solid, back empty) -> solid between `lower` and 0.5
            return [N((0, 1, 0, -0.5), 0, 1, 2), N((0, 1, 0, -lower), 0, 3, 4), N(f0=1), N(f0=1), N(f0=0xffffffff)]
        self.assertAlmostEqual(cd.pc_first_contact(column(0.0), (0, 5, 0), (0, -5, 0)), 0.45)          # 0.5 thick: a surface
        self.assertIsNone(cd.pc_first_contact(column(0.5 - 1e-7), (0, 5, 0), (0, -5, 0)))               # 1e-7 thick: grazing a cell edge


if __name__ == '__main__':
    unittest.main()
