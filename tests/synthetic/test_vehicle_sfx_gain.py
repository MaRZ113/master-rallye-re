import math,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from vehicle_sfx_gain import sfx_volume_hundredth_db,sfx_near_amplitude


class NativeSFXGainTests(unittest.TestCase):
    def test_measured_original_backend_points(self):
        for gain,volume in ((.08,-6160),(.18,-3120),(.30,-1800),(.55,-900),(.60,-800),(.65,-700)):
            with self.subTest(gain=gain):self.assertEqual(sfx_volume_hundredth_db(gain),volume)

    def test_breakpoints_and_cutoff(self):
        for gain,volume in ((-1,-10000),(0,-10000),(.049999,-10000),(.05,-7600),(.125,-4000),(.25,-2000),(.5,-1000),(.75,-500),(1,0),(2,0)):
            with self.subTest(gain=gain):self.assertEqual(sfx_volume_hundredth_db(gain),volume)

    def test_near_amplitude_is_not_authored_gain(self):
        self.assertEqual(sfx_near_amplitude(.01),0)
        self.assertEqual(sfx_near_amplitude(1),1)
        self.assertAlmostEqual(sfx_near_amplitude(.18),10**(-31.2/20))
        self.assertLess(sfx_near_amplitude(.18),.03)
        self.assertAlmostEqual(sfx_near_amplitude(.55),10**(-9/20))

    def test_monotone_and_bad_input(self):
        values=[sfx_volume_hundredth_db(i/10000) for i in range(10001)]
        self.assertEqual(values,sorted(values))
        for value in (float('nan'),float('inf'),-float('inf'),True,'1',None):
            with self.subTest(value=value),self.assertRaises(ValueError):sfx_volume_hundredth_db(value)


if __name__=='__main__':unittest.main()
