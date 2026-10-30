import hashlib
import struct
import unittest
import importlib.util
from pathlib import Path
from master_rallye.source_adapters import evo2_color as c


def palette():
    # Synthetic palette, no proprietary pixels.
    return struct.pack('<768H', *[value * 257 for channel in range(3) for value in range(256)])


class Evo2ColorTests(unittest.TestCase):
    def test_auxiliary_is_not_ordinary_alpha_or_unconditional_recolor(self):
        original = bytes((10,20,30,0)) * 256
        adjusted = bytes((110,120,130,0)) * 256
        data = c.composite(bytes((0,0,0,128,0,129,0,254,0,255)), original, adjusted)
        self.assertEqual(data[:8], bytes((10,20,30,0,10,20,30,128)))
        self.assertEqual(data[8:12], bytes((10,20,30,129)))
        self.assertEqual(data[12:16], bytes((109,119,129,254)))
        self.assertEqual(data[16:], bytes((110,120,130,255)))
        self.assertNotEqual(data[3::4], bytes([255])*5)

    def test_every_auxiliary_byte_and_palette_index_preserved(self):
        p = b''.join(bytes((i,i,i,0)) for i in range(256))
        samples = b''.join(bytes((i,255-i)) for i in range(256))
        out = c.composite(samples,p,p)
        self.assertEqual(out[3::4], samples[1::2])
        self.assertEqual(out[::4], samples[::2])

    def test_rounding_uses_truncation_not_nearest(self):
        p=bytes((0,0,0,0))*256;q=bytes((100,100,100,0))*256
        self.assertEqual(c.composite(bytes((0,130)),p,q)[:3], bytes((1,1,1)))

    def test_limits_and_ambiguous_palette_rejected(self):
        cases = [(b'',palette(),0,[0,0,0]),(bytes(2),palette(),513,[0,0,0]),
                 (bytes(2),palette(),1,[float('nan'),0,0]),
                 (bytes(2),palette(),1,[0,101,0]),(bytes(2),palette(),1,[True,0,0]),
                 (bytes(2),bytes(1535),1,[0,0,0]),(bytes(1),palette(),1,[0,0,0]),
                 (bytes(2),bytes((1,))+bytes(1535),1,[0,0,0])]
        for args in cases:
            with self.subTest(args=args[2:]):
                with self.assertRaises(ValueError): c.validate_inputs(*args)
        for data in (b'0', bytes(c.MAX_EDGE*c.MAX_EDGE*2+2)):
            with self.assertRaises(ValueError): c.composite(data,bytes(1024),bytes(1024))

    def test_wrong_executable_fails_before_emulation(self):
        with self.assertRaisesRegex(ValueError,'SHA256'):
            c.reconstruct(b'unqualified',bytes(2),palette(),1,[0,0,0])

    def test_original_native_consumer_synthetic_case(self):
        if importlib.util.find_spec('unicorn')is None:self.skipTest('optional original-instruction replay requires Unicorn')
        path=Path('E:/RallyWorkshop_Sources/sources/4x4 Evo 2/4x42.exe')
        if not path.is_file(): self.skipTest('owner-local qualified Evo2 EXE unavailable')
        # Complete 0..255 auxiliary coverage and all palette entries.
        samples=b''.join(bytes((i,255-i))for i in range(256))
        exe=path.read_bytes()
        first=c.reconstruct(exe,samples,palette(),16,[0,0,0])
        second=c.reconstruct(exe,samples,palette(),16,[0,0,0])
        self.assertEqual(first,second)
        self.assertEqual(first['packed_bgra'][3::4],samples[1::2])
        self.assertEqual(first['rgba'][3::4],bytes([255])*256)
        self.assertEqual(first['rgba'][::4],samples[::2])
        # Mixed path must also agree with exact original instructions.
        color=c.reconstruct(exe,samples,palette(),16,[339,81.25,-17.08])
        self.assertTrue(color['evidence']['native_composite_matches'])
        self.assertNotEqual(first['rgba'],color['rgba'])


if __name__=='__main__': unittest.main()
