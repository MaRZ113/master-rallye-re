from __future__ import annotations
import copy,hashlib,json,struct,sys,tempfile,unittest,zipfile,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.addon_sdk.ui_assets import *
from master_rallye.dxt import parse_dxt_bytes,decode_rgba_pixels,png_chunk
from master_rallye.addon_sdk.manifest import load_manifests,load_capabilities,validate_manifests
import gtmat,gt3_ui_icon

def bank(prefix,count):
    out=struct.pack('<3I',0xf001,125,count)+b''.join(struct.pack('<2I',i,i) for i in range(count))+struct.pack('<I',count)
    for i in range(count):
        name=f'{prefix}_{i:03d}_000'.encode();out+=struct.pack('<I',2)
        for _ in range(2):out+=bytes(48)+struct.pack('<I',len(name))+name
    return out

class UiAssetTests(unittest.TestCase):
    def test_append_preserves_all_stock_records_and_two_names(self):
        original=bank('carsheet',32);after,name=append_frame(original,23)
        parsed=parse_bank(after);self.assertEqual(parsed['records'][:-1],parse_bank(original)['records'])
        self.assertEqual((name,parsed['count']),('carsheet_032_000',33))

    def test_parser_rejects_unknown_and_truncated_layout(self):
        good=bank('carsheet',2)
        for data in (good[:-1],good+b'junk',b'\0'*20,good[:12]+struct.pack('<I',9)+good[16:]):
            with self.assertRaises(AddonValidationError):parse_bank(data)

    def test_fit_crops_without_stretch_and_preserves_alpha_colour(self):
        src=bytes((100,150,200,128))*8
        out=fit_rgba((4,2,src),8,8,padding=1)
        points=[(i%8,i//8) for i,a in enumerate(out[3::4]) if a]
        self.assertEqual((max(x for x,y in points)-min(x for x,y in points)+1,max(y for x,y in points)-min(y for x,y in points)+1),(6,3))
        self.assertTrue(all(out[i:i+4]==bytes((100,150,200,128)) for i in range(0,len(out),4) if out[i+3]))

    def test_fit_rejects_clear_input(self):
        with self.assertRaises(AddonValidationError):fit_rgba((2,2,bytes(16)),32,16)

    def fixture(self,root):
        project=root/'project';project.mkdir();(project/'ui').mkdir();png=gtmat.png_from_rgba(8,4,bytes((10,50,200,255))*32)
        (project/'ui/icon.png').write_bytes(png)
        addon={'frontend':{role:{'policy':'project_frame','frame':values[1]} for role,values in BANKS.items()}}
        cfg={'version':1,'icons':{role:{'png':'ui/icon.png','sha256':sha(png)} for role in BANKS}}
        (project/'ui-assets.json').write_text(json.dumps(cfg))
        sma=root/'data.sma'
        with zipfile.ZipFile(sma,'w') as z:
            for role,(prefix,count,template,size) in BANKS.items():
                z.writestr(prefix+'.dxb',bank(Path(prefix).name,count))
                z.writestr(f'{prefix}_{template:03d}_000.dxt',struct.pack('<5I',0xfeed,1,0,*size)+bytes((20,20,20,255))*(size[0]*size[1]))
        return project,addon,sma,cfg

    def test_custom_png_build_roundtrip_and_runtime_reference_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            root,addon,sma,cfg=self.fixture(Path(temp));assets,report=build_ui_assets(root,addon,sma)
            self.assertEqual(len(assets),4)
            for path,data in assets.items():p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
            (root/'ui-assets.report.json').write_text(json.dumps(report))
            with zipfile.ZipFile(sma) as z:self.assertEqual(verify_ui_resources(root,addon,z),assets)
            for role,r in report['roles'].items():
                t=parse_dxt_bytes(assets[r['frame_path']]);self.assertEqual((t.width,t.height),tuple(r['dimensions']))
                self.assertEqual(t.word_0x08,zlib.crc32(t.bgra)&0xffffffff)
                self.assertTrue(any(decode_rgba_pixels(t)[3::4]))
            r=report['roles']['smallcarsheet'];(root/r['bank_path']).write_bytes(assets[r['bank_path']]+b'junk')
            with zipfile.ZipFile(sma) as z:
                with self.assertRaises(AddonValidationError):verify_ui_resources(root,addon,z)

    def test_hash_selector_and_path_errors_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root,addon,sma,cfg=self.fixture(Path(temp))
            for mutation in ('sha','frame','escape','missing_role'):
                c=copy.deepcopy(cfg);a=copy.deepcopy(addon)
                if mutation=='sha':c['icons']['smallcarsheet']['sha256']='0'*64
                if mutation=='frame':a['frontend']['smallcarsheet']['frame']=13
                if mutation=='escape':c['icons']['smallcarsheet']['png']='../icon.png'
                if mutation=='missing_role':del c['icons']['smallcarsheet']
                (root/'ui-assets.json').write_text(json.dumps(c))
                with self.assertRaises((AddonValidationError,FileNotFoundError)):build_ui_assets(root,a,sma)

    def test_stock_policy_needs_no_sidecar(self):
        self.assertEqual(build_ui_assets(Path('does-not-exist'),{'frontend':{r:{'policy':'stock_frame'} for r in BANKS}},None),({},None))

    def test_manifest_project_frame_and_abi_range(self):
        manifests,_=load_manifests([ROOT/'research/vehicles/sdk/examples/glacier-sprint-t2.json'])
        caps,_=load_capabilities(ROOT/'research/vehicles/sdk/capabilities/retail-2001.json')
        manifests[0]['frontend']['smallcarsheet']={'policy':'project_frame','frame':30}
        validate_manifests(manifests,caps)
        manifests[0]['frontend']['smallcarsheet']['frame']=128
        with self.assertRaises(AddonValidationError):validate_manifests(manifests,caps)

    def test_named_gt3_imgs_extraction_reports_shared_placeholder(self):
        tex=b'Tex1'+bytes(8)+struct.pack('<I',48)+bytes(32)
        names=[b'car_a',b'car_b'];data=b'IMGS'+bytes(4)+struct.pack('<2I',2,144)
        for i,name in enumerate(names):data+=name.ljust(60,b'\0')+struct.pack('<I',i)
        data+=tex*2
        out,report=gt3_ui_icon.named_texture(data,'car_b')
        self.assertEqual(out,tex);self.assertEqual(report['status'],'SHARED_TEXTURE_REVIEW_REQUIRED')
        with self.assertRaises(ValueError):gt3_ui_icon.named_texture(data[:-1],'car_b')

    def test_gt3_selective_rofs_read(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'GT3.VOL';b=bytearray(2052);struct.pack_into('<5I',b,0,0x53466f52,0x20002,96,64,0)
            struct.pack_into('<3I',b,20,0x1000000+64,1,40);struct.pack_into('<3I',b,40,66,1,4)
            b[64:77]=b'.\0test.imgs\0\0';b[2048:2052]=b'IMGS';p.write_bytes(b)
            data,row=gt3_ui_icon.read_member(p,'test.imgs');self.assertEqual(data,b'IMGS');self.assertEqual(row['inventory_count'],1)

if __name__=='__main__':unittest.main()
