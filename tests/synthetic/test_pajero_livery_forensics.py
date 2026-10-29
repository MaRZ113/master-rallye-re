"""Invented pixels/references only, no original MR or donor assets."""
import hashlib
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from master_rallye import pajero_livery_forensics as f


class LiveryTests(unittest.TestCase):
    def test_txt_ownership_retains_original_reference_and_slot(self):
        text='Material number [12] has name [Door]\n Texture [0] HasAlpha [No] Name[D:\\projects\\Pajero\\Door.tga]\n'
        rows=f.txt_materials(text);self.assertEqual(rows[0]['texture_stem'],'door-tga');self.assertEqual(rows[0]['name'],'Door');self.assertEqual(rows[0]['slot'],0)

    def test_equal_uv_bounds_do_not_prove_atlas_identity(self):
        uv=[[0,0],[1,0],[0,1]]
        self.assertFalse(f.direct_compatible(uv,uv,source_layout_hash='a',target_layout_hash='b'))
        self.assertFalse(f.direct_compatible(uv,uv,source_layout_hash='',target_layout_hash=''))
        self.assertTrue(f.direct_compatible(uv,uv,source_layout_hash='a',target_layout_hash='a'))
        self.assertFalse(f.direct_compatible(uv,uv[::-1],source_layout_hash='a',target_layout_hash='a'))

    def test_patch_is_bounded_alpha_preserving_and_deterministic(self):
        base=bytes([1,2,3,91])*64;badge=bytes([200,9,8,0])*4
        a,p=f.patch_badge(base,8,8,badge,2,2,[[2,2,4,4]])
        self.assertEqual(len(p),4);self.assertEqual(a[3::4],base[3::4]);self.assertEqual(a,f.patch_badge(base,8,8,badge,2,2,[[2,2,4,4]])[0])
        self.assertEqual(base,bytes([1,2,3,91])*64)
        for i in range(64):
            if i not in p:self.assertEqual(a[i*4:i*4+4],base[i*4:i*4+4])

    def test_opposed_island_mapping_is_explicit(self):
        base=bytes([0,0,0,255])*16;badge=bytes([10,0,0,255,20,0,0,255,30,0,0,255,40,0,0,255])
        a,_=f.patch_badge(base,4,4,badge,2,2,[[0,0,2,2]],mirror_x=())
        b,_=f.patch_badge(base,4,4,badge,2,2,[[0,0,2,2]],mirror_x=(0,))
        self.assertEqual(a[:8],bytes([30,0,0,255,40,0,0,255]));self.assertEqual(b[:8],bytes([40,0,0,255,30,0,0,255]))

    def test_bad_dimensions_spans_and_nonuniform_marking_rejected(self):
        base=b'\0'*64;badge=b'\0'*16
        for rect in [[-1,0,1,2],[0,0,5,5],[0,0,2,3],[0.,0,2,2]]:
            with self.assertRaises(ValueError):f.patch_badge(base,4,4,badge,2,2,[rect])
        with self.assertRaises(ValueError):f.patch_badge(base,4,4,badge,2,2,[[0,0,2,2]],mirror_x=(1,))

    def test_history_undo_redo_restore_and_reopening(self):
        h=f.OverlayHistory();self.assertFalse(h.enabled);h.apply(True);self.assertTrue(h.enabled)
        h.undo();self.assertFalse(h.enabled);h.redo();self.assertTrue(h.enabled);h.restore();self.assertFalse(h.enabled)
        with tempfile.TemporaryDirectory()as tmp:
            p=Path(tmp)/'history.json';h.save(p);other=f.OverlayHistory.load(p);self.assertEqual(other.states,h.states);self.assertEqual(other.cursor,h.cursor)
        h.undo();h.apply(False);h.redo();self.assertFalse(h.enabled)

    def test_invalid_history_and_unqualified_scene_rejected(self):
        for states,cursor in [([{'enabled':'yes'}],0),([{'enabled':True}],True),([{'enabled':False}],9)]:
            with self.assertRaises(ValueError):f.OverlayHistory(states,cursor)
        with tempfile.TemporaryDirectory()as tmp:
            p=Path(tmp)/'scene.json';p.write_text('{}')
            with self.assertRaisesRegex(ValueError,'Qualified immutable'):f.badge_experiment(p,Path(tmp)/'out',Path(tmp),f.OverlayHistory())
            self.assertFalse((Path(tmp)/'out').exists())

    def test_synthetic_clean_archive_ownership_and_drift(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);family=root/'retail/Data.sma_unpacked/DataGx/Vehicles/Pajero';family.mkdir(parents=True)
            blob=struct.pack('<5I',0xfeed,1,0,1,1)+bytes([3,5,7,255]);(family/'door-tga.dxt').write_bytes(blob)
            (family/'Pajero.txt').write_text('Material number [0] has name [Door]\nTexture [0] Name[D:\\Door.tga]\n')
            archive=root/'retail/Data.sma'
            with zipfile.ZipFile(archive,'w')as z:
                for p in family.iterdir():z.writestr('DataGx/Vehicles/Pajero/'+p.name,p.read_bytes())
            with patch.object(f,'RETAIL_SHA',f.file_hash(archive)):
                a=f.inventory(root);self.assertEqual(a['textures'][0]['ownership'],'TXT_ONLY');self.assertTrue(a['textures'][0]['archive_exact'])
                (family/'door-tga.dxt').write_bytes(blob[:-1]+b'\0')
                with self.assertRaisesRegex(ValueError,'differs'):f.inventory(root)


if __name__=='__main__':unittest.main()
