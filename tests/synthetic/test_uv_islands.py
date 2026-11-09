import unittest
from master_rallye.workshop.uv_islands import island_groups

class IslandTests(unittest.TestCase):
    def test_corner_contact_is_not_an_island(self):
        self.assertEqual(len(island_groups([[(0,0),(1,0),(0,1)],[(0,0),(-1,0),(0,-1)]])),2)
    def test_continuous_shared_edge_connects(self):
        triangles=[[(0,0),(1,0),(0,1)],[(1,0),(1,1),(0,1)]]
        self.assertEqual(len(island_groups(triangles,[[0,1,2],[1,3,2]])),1)
    def test_overlapping_uvs_on_separate_geometry_stay_separate(self):
        triangles=[[(0,0),(1,0),(0,1)]]*2
        self.assertEqual(len(island_groups(triangles,[[0,1,2],[3,4,5]])),2)
    def test_native_edge_with_uv_seam_stays_separate(self):
        self.assertEqual(len(island_groups([[(0,0),(1,0),(0,1)],[(2,0),(1,1),(0,1)]],[[0,1,2],[1,3,2]])),2)

if __name__=='__main__':unittest.main()
