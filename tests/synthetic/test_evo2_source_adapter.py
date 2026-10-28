"""Bounded Evo2 format and neutral adapter checks using invented game resources."""
from contextlib import ExitStack
import copy
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from master_rallye import universal_vehicle_scene as uvs
from master_rallye.source_adapters import evo2
from master_rallye.source_adapters import evo2_formats as formats


def pod(resources):
    items=list(resources.items());names=b'';offsets=[]
    for name,_ in items:offsets.append(len(names));names+=name.encode('ascii')+b'\0'
    at=96+20*len(items)+len(names);data=bytearray(at);data[:4]=b'POD2'
    struct.pack_into('<II',data,88,len(items),0)
    data[96+20*len(items):]=names
    for index,((_,blob),name_offset)in enumerate(zip(items,offsets)):
        struct.pack_into('<5I',data,96+20*index,name_offset,len(blob),at,123,456)
        data.extend(blob);at+=len(blob)
    return bytes(data)


def smf(name='BODY',point=1.,frames=1):
    lines=['C3DModel','4','1','synthetic LOD declaration',name,'1','1',f'3,{frames},1,9',
           '0,0,0,0,0,fixture.tif']
    for frame in range(frames):
        lines.extend([f'{frame},0,0,0,0,1,0,0',f'{point+frame},0,0,0,0,1,1,0',f'{frame},1,0,0,0,1,0,1'])
    lines.append('0,1,2')
    return ('\r\r\n'.join(lines)+'\r\r\n').encode('ascii')


def trk():
    values={'version':'7','truckName':evo2.DISPLAY_NAME,'truckMake':'Toyota','truckModel':'4Runner',
            'truckClass':'SUV','truckModelYear':'2000','truckModelBaseName':'4RUNNERSR5',
            'tireModelBaseName':'4RUNTIRE','truckLength':'15','truckWidth':'6','truckHeight':'6',
            'truckWheelbase':'8.78','truckFrontTrack':'5','truckRearTrack':'5',
            'numStockParts':'0','numColors':'1'}
    for slot,position in zip(evo2.SLOTS,('2,1,4','-2,1,4','2,1,-4','-2,1,-4')):
        values[slot+'.static_bpos']=position
    return ('\n'.join(f'{key}\n{value}'for key,value in values.items())+
            '\nstockPartList[]\ncolorList[]\n1,1,1,0,0,0,Red\n').encode('ascii')


def tiff(samples, *, spp=3, photo=2, extra=None, endian='<',width=2,height=1):
    """Tiny standards-shaped uncompressed chunky first IFD, no imaging library."""
    values={256:(4,[width]),257:(4,[height]),258:(3,[8]*spp),259:(3,[1]),262:(3,[photo]),
            273:(4,[0]),274:(3,[1]),277:(3,[spp]),278:(4,[height]),279:(4,[len(samples)]),284:(3,[1])}
    if extra is not None:values[338]=(3,[extra])
    if photo==3:
        values[320]=(3,[i*257 for i in range(256)]+[65535-i*257 for i in range(256)]+[12345]*256)
    count=len(values);end=8+2+12*count;data=bytearray(end+4)
    data[:4]=b'II*\0'if endian=='<'else b'MM\0*'
    struct.pack_into(endian+'IH',data,4,8,count)
    for index,(tag,(kind,items))in enumerate(sorted(values.items())):
        at=10+12*index;raw=struct.pack(endian+str(len(items))+('H'if kind==3 else'I'),*items)
        struct.pack_into(endian+'HHI',data,at,tag,kind,len(items))
        if len(raw)<=4:data[at+8:at+8+len(raw)]=raw
        else:struct.pack_into(endian+'I',data,at+8,len(data));data.extend(raw)
    pixel_offset=len(data)
    for index,tag in enumerate(sorted(values)):
        if tag==273:struct.pack_into(endian+'I',data,10+12*index+8,pixel_offset)
    data.extend(samples)
    return bytes(data)


def mutate_tiff(data, tag, *, scalar=None,count=None):
    data=bytearray(data);endian='<'if data[:2]==b'II'else'>'
    total=struct.unpack_from(endian+'H',data,8)[0]
    for index in range(total):
        at=10+12*index
        if struct.unpack_from(endian+'H',data,at)[0]==tag:
            if scalar is not None:struct.pack_into(endian+'I',data,at+8,scalar)
            if count is not None:struct.pack_into(endian+'I',data,at+4,count)
            return bytes(data)
    raise AssertionError('fixture tag not found')


class Evo2WireFormatTests(unittest.TestCase):
    def test_pod_member_identity_ranges_and_original_bytes_are_preserved(self):
        original=pod({'MODELS/body.SMF':smf(),'ART/fixture.tif':b'invented texture'})
        entries=formats.pod2_members(original)
        self.assertEqual([entry.name for entry in entries],['MODELS/body.SMF','ART/fixture.tif'])
        self.assertEqual(formats.member_bytes(original,entries[0]),smf())
        self.assertEqual(entries[0].checksum,456)
        self.assertEqual(original,pod({'MODELS/body.SMF':smf(),'ART/fixture.tif':b'invented texture'}))

    def test_pod_rejects_unsupported_counts_names_and_overlapping_spans(self):
        for data in (b'POD3'+b'\0'*96,pod({'../escape':b'x'}),pod({'A':b'a','a':b'b'})):
            with self.assertRaises(ValueError):formats.pod2_members(data)
        good=pod({'first':b'1234','second':b'5678'})
        for at,value in ((88,100001),(96,999999),(104,0),(100,999999)):
            data=bytearray(good);struct.pack_into('<I',data,at,value)
            with self.assertRaises(ValueError):formats.pod2_members(data)
        data=bytearray(good);first=struct.unpack_from('<I',data,104)[0]
        struct.pack_into('<I',data,124,first)
        with self.assertRaisesRegex(ValueError,'overlap'):formats.pod2_members(data)

    def test_member_budget_is_checked_before_slice(self):
        entry=formats.PodMember('large',0,formats.MAX_MEMBER+1,0,0)
        with self.assertRaisesRegex(ValueError,'limit'):formats.member_bytes(b'x',entry)

    def test_smf_multiple_frames_preserve_original_topology_uv_and_visibility(self):
        result=formats.parse_smf(smf(point=2.,frames=2));obj=result['objects'][0]
        self.assertEqual(obj['vertices_by_frame'][0][1],[2.,0.,0.,0.,0.,1.,1.,0.])
        self.assertEqual(obj['vertices_by_frame'][1][1][0],3.)
        self.assertEqual(obj['faces'],[[0,1,2]]);self.assertEqual(result['vertices_including_frames'],6)
        self.assertEqual(obj['unknown_object_field'],9)
        self.assertEqual(obj['texture'],'fixture.tif')

    def test_smf_rejects_nonfinite_bad_indices_missing_uv_tail_and_count_budgets(self):
        good=smf()
        variants=[good.replace(b'0,1,2',b'0,1,3'),good.replace(b'1.0,0,0,0,0,1,1,0',b'nan,0,0,0,0,1,1,0'),
                  good.replace(b'0,0,0,0,0,1,0,0',b'0,0,0,0,0,1,0'),good+b'junk',
                  good.replace(b'3,1,1,9',b'200001,1,1,9'),good.replace(b'fixture.tif',b'../escape.tif')]
        for data in variants:
            with self.subTest(data=data[-32:]):
                with self.assertRaises(ValueError):formats.parse_smf(data)
        with patch.object(formats,'MAX_VERTICES',5):
            with self.assertRaises(ValueError):formats.parse_smf(smf(frames=2))

    def test_indexed_tiff_unspecified_second_sample_is_preserved_not_used_as_alpha(self):
        raw=b'\x03\x00\xc8\x11';source=tiff(raw,spp=2,photo=3,extra=0)
        meta,rgba,samples,palette=evo2.decode_tiff(source)
        channels=meta['source_channels']
        self.assertEqual(samples,raw);self.assertEqual(len(palette),1536)
        self.assertEqual(rgba[3::4],b'\xff\xff')
        self.assertEqual(rgba[:3],bytes((3,252,(12345+128)//257)))
        self.assertTrue(channels['unknown_extra_sample'])
        self.assertEqual(channels['sample_extrema'][1],[0,17])
        self.assertEqual(channels['raw_samples_sha256'],uvs.sha(raw))
        self.assertEqual(channels['palette_sha256'],uvs.sha(palette))

    def test_rgb_fourth_unspecified_sample_and_explicit_alpha_are_distinct(self):
        raw=bytes((10,20,30,0,40,50,60,17))
        meta,rgba,samples,palette=evo2.decode_tiff(tiff(raw,spp=4,extra=0))
        self.assertEqual(samples,raw);self.assertEqual(palette,b'')
        self.assertEqual(rgba,bytes((10,20,30,255,40,50,60,255)))
        self.assertTrue(meta['source_channels']['unknown_extra_sample'])
        for extra in (1,2):
            meta,rgba,samples,_=evo2.decode_tiff(tiff(raw,spp=4,extra=extra))
            self.assertEqual(rgba,raw);self.assertEqual(samples,raw)
            self.assertEqual(meta['source_channels']['alpha_association'],[extra])

    def test_tiff_both_byte_orders_decode_equal_samples_and_do_not_follow_next_ifd(self):
        pixels=bytes((1,2,3,4,5,6))
        for endian in ('<','>'):
            source=bytearray(tiff(pixels,endian=endian));count=struct.unpack_from(endian+'H',source,8)[0]
            struct.pack_into(endian+'I',source,10+12*count,0xffffffff)
            meta,rgba,samples,_=evo2.decode_tiff(bytes(source))
            self.assertEqual(samples,pixels);self.assertEqual(rgba,bytes((1,2,3,255,4,5,6,255)))
            self.assertEqual(meta['source_channels']['next_ifd_word'],0xffffffff)

    def test_tiff_rejects_bad_dimensions_compression_planar_strip_and_tag_counts(self):
        good=tiff(bytes((1,2,3,4,5,6)))
        for data in (b'II*\0',good[:-1],mutate_tiff(good,256,scalar=4097),mutate_tiff(good,259,scalar=5),
                     mutate_tiff(good,284,scalar=2),mutate_tiff(good,273,scalar=0),
                     mutate_tiff(good,279,scalar=5),mutate_tiff(good,258,count=65537)):
            with self.subTest(data=data[:8]):
                with self.assertRaises(ValueError):evo2.decode_tiff(data)

    def test_trk_catalog_associations_static_wheels_and_original_colors_are_preserved(self):
        result=evo2.parse_trk(trk())
        self.assertEqual(result['records']['truckModelBaseName']['value'],'4RUNNERSR5')
        self.assertEqual(result['wheel_positions']['faxle.rtire'],[2.,1.,4.])
        self.assertEqual(result['color_records'][0]['value'],'1,1,1,0,0,0,Red')

    def test_trk_rejects_missing_duplicate_catalog_swaps_and_ambiguous_wheels(self):
        good=trk()
        variants=[good.replace(b'truckName\n',b'otherName\n'),good+b'\nversion\n7\n',
                  good.replace(b'4RUNNERSR5',b'OTHERBODY'),good.replace(b'2,1,4',b'0,1,4'),
                  good.replace(b'2,1,4',b'nan,1,4'),good.replace(b'numStockParts\n0',b'numStockParts\n1'),
                  good.replace(b'1,1,1,0,0,0,Red',b'1,1,1,Red')]
        for data in variants:
            with self.assertRaises(ValueError):evo2.parse_trk(data)


class Evo2SceneAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name)
        self.collection=self.base/'sources';self.root=self.collection/'Evo2';self.root.mkdir(parents=True)
        self.exe=b'invented executable identity; never executed';(self.root/'4x42.exe').write_bytes(self.exe)
        self.resources={evo2.CATALOG:trk(),evo2.BODY:smf(),
                        'ART/fixture.tif':tiff(bytes((1,2,3,4,5,6)))}
        for detail in ('08','12','16'):
            for side in ('L','R'):
                self.resources[f'MODELS/4RUNTIRE{detail}{side}.SMF']=smf('TIRE',point=float(detail)*(1 if side=='R'else-1))
        self.config=self.base/'roots.json';self.accepted=self.base/'accepted';self.accepted.mkdir()
        self.config.write_text(json.dumps({'schema':'source-garage-roots/1','base':str(self.collection),
            'games':[{'id':'evo2','path':'Evo2'},{'id':'other','path':'Other'}],'protected_roots':[str(self.accepted)]}))
        self.write_pod()

    def write_pod(self):
        self.pod=pod(self.resources);(self.root/'TRUCK.POD').write_bytes(self.pod)

    def pins(self):
        stack=ExitStack()
        for name,value in {'POD_SHA256':uvs.sha(self.pod),'EXE_SHA256':uvs.sha(self.exe),
                           'CATALOG_SHA256':uvs.sha(trk()),'BODY_SHA256':uvs.sha(smf())}.items():
            stack.enter_context(patch.object(evo2,name,value))
        return stack

    def test_qualified_synthetic_pilot_assembles_original_variants_and_reopens_deterministically(self):
        before={path.name:(path.read_bytes(),path.stat().st_mtime_ns)for path in self.root.iterdir()}
        with self.pins():
            catalog=evo2.inspect_source(self.root);first=evo2.create_scene(self.root,self.base/'first',config_path=self.config)
            second=evo2.create_scene(self.root,self.base/'second',config_path=self.config)
        self.assertEqual(catalog['catalog'],evo2.CATALOG);self.assertEqual(first['L2'],'NOT TESTED')
        self.assertEqual(first['Gameplay'],'NOT TESTED');self.assertTrue(first['source_unchanged'])
        self.assertEqual(first['scene_sha256'],second['scene_sha256'])
        scene=uvs.load_scene(self.base/'first/scene.json')
        self.assertEqual(len(scene['wheel_variants']),6)
        wheels=[node for node in scene['nodes']if node.get('role')=='wheel']
        self.assertEqual(len(wheels),4)
        for node in wheels:
            self.assertIsNone(node['source_local_transform'])
            p=node['source_transform_record']['translation']
            self.assertEqual([node['local_transform'][i]for i in (3,7,11)],p)
            self.assertIsNone(node['source_transform_record']['rotation'])
        self.assertEqual(scene['meshes'][0]['positions'][1],[1.,0.,0.])
        self.assertTrue(any(row['id']=='tiff-extra-samples'for row in scene['unknown_semantics']))
        for path in self.root.iterdir():self.assertEqual((path.read_bytes(),path.stat().st_mtime_ns),before[path.name])

    def test_changed_pod_or_executable_identity_rejects_without_output(self):
        with self.pins():
            (self.root/'TRUCK.POD').write_bytes(self.pod+b'changed')
            with self.assertRaisesRegex(ValueError,'SHA256'):evo2.create_scene(self.root,self.base/'bad',config_path=self.config)
            (self.root/'TRUCK.POD').write_bytes(self.pod);(self.root/'4x42.exe').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'executable'):evo2.create_scene(self.root,self.base/'bad',config_path=self.config)
        self.assertFalse((self.base/'bad').exists())

    def test_missing_texture_wheel_and_mismatched_original_body_fail_closed(self):
        for member in ('ART/fixture.tif','MODELS/4RUNTIRE12L.SMF'):
            data=self.resources.pop(member);self.write_pod()
            with self.pins():
                with self.assertRaisesRegex(ValueError,'missing required'):evo2.create_scene(self.root,self.base/'bad',config_path=self.config)
            self.assertFalse((self.base/'bad').exists());self.resources[member]=data
        self.resources[evo2.BODY]=smf(point=2.);self.write_pod()
        with self.pins():
            with self.assertRaisesRegex(ValueError,'body/catalog'):evo2.create_scene(self.root,self.base/'bad',config_path=self.config)

    def test_all_configured_roots_tools_and_existing_accepted_paths_are_protected(self):
        targets=[self.root/'new',self.collection/'Other/new',self.collection.parent/'tools/new',self.accepted/'new',self.collection]
        with self.pins():
            for target in targets:
                with self.assertRaises(ValueError):evo2.create_scene(self.root,target,config_path=self.config)
            with self.assertRaises(ValueError):evo2.create_scene(self.root,self.base/'bad',config_path=self.base/'missing.json')
            with self.assertRaises(ValueError):evo2.create_scene(self.root,self.base/'bad',wheel_detail='32',config_path=self.config)
        self.assertFalse((self.base/'bad').exists())


if __name__=='__main__':unittest.main()
