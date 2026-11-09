"""Texture/livery acceptance boundaries, using tiny native synthetic resources."""
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib
from PIL import Image
from master_rallye.workshop.livery import LiverySession,relative_file
from master_rallye.workshop.texture_images import load_image
from master_rallye.workshop.livery_artwork import export_resource
from tests.synthetic.test_workshop import family


class LiveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.original=family(self.root/'family');self.session=LiverySession.create(self.root/'family',self.root/'work')
    def edited(self,name='edit.png',alpha=255):
        path=self.root/name;Image.new('RGBA',(2,2),(30,40,50,alpha)).save(path);return path
    def test_preserve_and_explicit_alpha_header_crc_geometry(self):
        s=self.session;raw=(s.project.assets/'car.dx').read_bytes();s.import_png('base-tga.dxt',self.edited())
        edited=(s.project.assets/'base-tga.dxt').read_bytes()
        self.assertEqual(edited[23::4],self.original[23::4]);self.assertEqual(edited[:8]+edited[12:20],self.original[:8]+self.original[12:20])
        self.assertEqual(struct.unpack_from('<I',edited,8)[0],zlib.crc32(edited[20:]))
        self.assertEqual((s.project.assets/'car.dx').read_bytes(),raw)
        s.import_png('base-tga.dxt',self.edited(alpha=12),False);self.assertEqual(s.project.texture('base-tga.dxt').bgra[3::4],bytes([12]*4))
        self.assertEqual((self.root/'family/base-tga.dxt').read_bytes(),self.original)
    def test_same_pixels_recompressed_png_is_noop(self):
        s=self.session;s.export_png('base-tga.dxt',self.root/'roundtrip.png')
        im=Image.open(self.root/'roundtrip.png');im.save(self.root/'other.png',compress_level=0)
        s.import_png('base-tga.dxt',self.root/'other.png');self.assertEqual(s.project.data['edits'],{})
        self.assertEqual((s.project.assets/'base-tga.dxt').read_bytes(),self.original)
    def test_manifest_atomic_validation_identity_paths(self):
        s=self.session;path=s.export_all(self.root/'exports');doc=json.loads(path.read_text());png=path.parent/doc['entries'][0]['png']
        Image.new('RGBA',(3,2),'red').save(png)
        with self.assertRaises(ValueError):s.import_manifest(path)
        self.assertEqual(s.project.data['edits'],{})
        doc['entries'][0]['png']='../edit.png';path.write_text(json.dumps(doc))
        with self.assertRaises(ValueError):s.import_manifest(path)
        doc['model_variant']='PS2';path.write_text(json.dumps(doc))
        with self.assertRaises(ValueError):s.import_manifest(path)
    def test_batch_undo_and_all_untouched_noop(self):
        s=self.session;path=s.export_all(self.root/'exports');self.assertEqual(s.import_manifest(path),[])
        png=path.parent/'base-tga.dxt.png';Image.new('RGBA',(2,2),'red').save(png)
        self.assertEqual(s.import_manifest(path),['base-tga.dxt']);s.project.undo()
        self.assertEqual((s.project.assets/'base-tga.dxt').read_bytes(),self.original);s.project.redo();self.assertTrue(s.project.data['edits'])
    def test_relocation_reopen_stable_id_and_original(self):
        import shutil
        s=self.session;s.new_livery('Custom 31');s.import_png('base-tga.dxt',self.edited());path=s.save_package(self.root/'package')
        self.assertFalse(s.dirty);shutil.copytree(path.parent,self.root/'relocated')
        q=LiverySession.open_package(self.root/'relocated/livery.json',self.root/'reopened')
        self.assertEqual(q.metadata,s.metadata);self.assertFalse(q.dirty)
        self.assertEqual((q.project.assets/'base-tga.dxt').read_bytes(),(s.project.assets/'base-tga.dxt').read_bytes())
        q.project.restore('base-tga.dxt');self.assertEqual((q.project.assets/'base-tga.dxt').read_bytes(),self.original)
        manifest=json.loads(path.read_text());self.assertTrue(all(not Path(e['path']).is_absolute() for e in manifest['baseline']+manifest['textures']))
    def test_corrupt_or_incomplete_package_rejected(self):
        s=self.session;p=s.save_package(self.root/'package');doc=json.loads(p.read_text());doc['textures']=[];p.write_text(json.dumps(doc))
        with self.assertRaises(ValueError):LiverySession.open_package(p,self.root/'bad')
    def test_external_package_pixels_are_editable_but_baseline_stays_pinned(self):
        s=self.session;p=s.save_package(self.root/'package');doc=json.loads(p.read_text())
        name=doc['textures'][0]['path'];target=p.parent/name
        raw=bytearray(target.read_bytes());raw[20]^=127
        struct.pack_into('<I',raw,8,zlib.crc32(raw[20:]));target.write_bytes(raw)
        q=LiverySession.open_package(p,self.root/'reopen-edited')
        self.assertEqual(q.project.texture('base-tga.dxt').bgra,bytes(raw[20:]))
        self.assertTrue(any('Externally edited texture' in w for w in q.warnings))
        base=p.parent/'baseline/car.dx';base.write_bytes(base.read_bytes()+b'x')
        with self.assertRaisesRegex(ValueError,'Package hash'):LiverySession.open_package(p,self.root/'bad-baseline')

    def test_external_historical_art_is_reclassified_without_hash_lock(self):
        from master_rallye.workshop.service import sha
        raw=self.edited().read_bytes()
        entry={'role':'smallcarsheet','sha256':sha(raw),'origin':'Historical','historical_original':True}
        native=self.root/'native.png';Image.new('RGBA',(32,16),'red').save(native)
        result=LiverySession.refresh_artwork(entry,native.read_bytes())
        self.assertEqual(result['origin'],'Custom');self.assertFalse(result['historical_original'])
        with self.assertRaisesRegex(ValueError,'dimensions'):LiverySession.refresh_artwork(entry,raw)

    def test_all_image_formats_and_animation_warning(self):
        s=self.session
        for fmt,ext in [('JPEG','jpg'),('BMP','bmp'),('WEBP','webp'),('GIF','gif'),('TGA','tga'),('TIFF','tiff'),('PNG','png')]:
            path=self.root/('input.'+ext);Image.new('RGB',(2,2),(32,64,128)).save(path,format=fmt)
            s.import_png('base-tga.dxt',path);self.assertEqual(s.project.texture('base-tga.dxt').bgra[3::4],self.original[23::4])
        path=self.root/'animated.gif';Image.new('RGB',(2,2),'red').save(path,save_all=True,append_images=[Image.new('RGB',(2,2),'blue')],duration=100,loop=0)
        self.assertIn('frame 0',load_image(path)[3][0])
    def test_exports_and_protected_paths(self):
        s=self.session
        for ext in ('png','jpg','bmp','webp'):
            path=self.root/('output.'+ext);s.export_png('base-tga.dxt',path)
            with Image.open(path) as im:self.assertEqual(im.size,(2,2))
        for folder in (s.project.assets,s.project.baseline,self.root/'family'):
            with self.assertRaises(ValueError):s.export_png('base-tga.dxt',folder/'new.png')
        for name in ('/x','../x','C:/x','a\\b'):
            with self.assertRaises(ValueError):relative_file(self.root,name)
    def test_native_artwork_uses_template_dimensions_and_crc(self):
        png=self.edited();template=self.root/'template.dxt';template.write_bytes(self.original);out=self.root/'new.dxt'
        export_resource({'png':str(png)},template,out);raw=out.read_bytes();self.assertEqual(raw[:8]+raw[12:20],self.original[:8]+self.original[12:20]);self.assertEqual(zlib.crc32(raw[20:]),struct.unpack_from('<I',raw,8)[0])
        Image.new('RGBA',(4,4),'blue').save(png)
        with self.assertRaises(ValueError):export_resource({'png':str(png)},template,out)

    def test_original_workshop_edits_and_restore_survive_snapshot(self):
        s=self.session;s.import_png('base-tga.dxt',self.edited())
        source_before=(s.project.root/'workshop-project.json').read_bytes()
        q=LiverySession.create(s.project.root,self.root/'snapshot')
        self.assertEqual(q.project.texture('base-tga.dxt').bgra,s.project.texture('base-tga.dxt').bgra)
        q.project.restore('base-tga.dxt');self.assertEqual((q.project.assets/'base-tga.dxt').read_bytes(),self.original)
        self.assertEqual((s.project.root/'workshop-project.json').read_bytes(),source_before)

    def test_orientation_and_model_variant_independence(self):
        s=self.session;image=Image.new('RGBA',(2,2));image.putdata([(255,0,0,255),(0,255,0,255),(0,0,255,255),(255,255,0,255)])
        path=self.root/'orientation.png';image.save(path);s.import_png('base-tga.dxt',path,False)
        self.assertEqual(s.project.texture('base-tga.dxt').bgra[:4],bytes([255,0,0,255])) # bottom-left blue, native BGRA
        s.export_png('base-tga.dxt',self.root/'oriented.png')
        with Image.open(self.root/'oriented.png') as result:self.assertEqual(result.tobytes(),image.tobytes())
        s.metadata['model_variant']='PS2-converted'
        with self.assertRaisesRegex(ValueError,'fixed by the loaded source'):s.new_livery('Variant livery')
        with self.assertRaises(ValueError):s.save_package(self.root/'false-variant')

    def test_duplicate_retains_current_textures_but_uses_new_stable_identity(self):
        s=self.session;s.import_png('base-tga.dxt',self.edited());old=s.metadata['livery_id'];pixels=s.project.texture('base-tga.dxt').bgra
        s.metadata['origin']='Reconstructed';s.duplicate_current('Reconstructed Copy')
        self.assertNotEqual(old,s.metadata['livery_id']);self.assertEqual(s.metadata['parent_livery_id'],old);self.assertEqual(s.metadata['origin'],'Reconstructed')
        self.assertEqual(s.project.texture('base-tga.dxt').bgra,pixels)
        s.save_package(self.root/'reconstructed')

    def test_old_defaults_upgrade_and_custom_camera_retained(self):
        from master_rallye.workshop.livery_artwork import normalize_presets
        defaults={'vehicle_select_art':dict(azimuth=138.,elevation=10.,zoom=.7,pan_x=0.,pan_y=0.),'smallcarsheet':dict(azimuth=-90.,elevation=0.,zoom=.7,pan_x=0.,pan_y=0.)}
        migrated=normalize_presets(defaults)
        self.assertEqual(migrated['vehicle_select_art']['azimuth'],42.);self.assertEqual(migrated['smallcarsheet']['frame_scale'],1.)
        defaults['vehicle_select_art']['azimuth']=22.
        self.assertEqual(normalize_presets(defaults)['vehicle_select_art']['azimuth'],22.)

    def test_frame_scale_changes_only_composition_and_cannot_cut_off_silhouette(self):
        from master_rallye.workshop.livery_artwork import compose_live,default_presets
        black=Image.new('RGB',(128,80),'black');white=Image.new('RGB',(128,80),'white')
        for im in (black,white):
            from PIL import ImageDraw
            ImageDraw.Draw(im).rectangle((20,20,108,60),fill=(130,40,30))
        a=self.root/'black.bmp';b=self.root/'white.bmp';black.save(a);white.save(b)
        preset=default_presets()['vehicle_select_art']
        first=compose_live(self.session,'vehicle_select_art',a,b,preset,self.root/'frame-one')
        second=compose_live(self.session,'vehicle_select_art',a,b,{**preset,'frame_scale':4.,'pan_x':2.,'pan_y':-2.},self.root/'frame-two')
        self.assertEqual(first['source_sha256'],second['source_sha256']);self.assertNotEqual(first['sha256'],second['sha256'])
        with Image.open(second['png']) as im:
            x0,y0,x1,y1=im.getchannel('A').point(lambda a:255 if a>20 else 0).getbbox()
            self.assertTrue(0<x0<x1<im.width and 0<y0<y1<im.height)

    def test_manual_historical_source_retained_when_explicitly_scaled(self):
        from master_rallye.workshop.livery_artwork import import_manual
        path=self.root/'historical.png';Image.new('RGBA',(64,32),(50,100,200,128)).save(path)
        with self.assertRaises(ValueError):import_manual(self.session,'smallcarsheet',path,'Historical',self.root/'not-written')
        entry=import_manual(self.session,'smallcarsheet',path,'Historical',self.root/'scaled',scale_to_native=True)
        self.assertEqual(entry['dimensions'],[32,16]);self.assertEqual(entry['source_dimensions'],[64,32]);self.assertTrue(entry['historical_original'])
        with Image.open(entry['source_png']) as im:self.assertEqual(im.size,(64,32))

    def test_main_workshop_opens_same_qt_editor_with_current_vehicle(self):
        from types import SimpleNamespace
        from unittest.mock import Mock,patch
        from master_rallye.workshop.gui import WorkshopApp
        root=self.root/'sdk'
        for relative in ('.research-output/vehicles/workshop2/qt-env/Scripts/python.exe','.research-output/vehicles/v-tex2/viewer-build/Release/mr-vehicle-previewer.exe','tools/rally_workshop2.py'):
            path=root/relative;path.parent.mkdir(parents=True,exist_ok=True);path.touch()
        app=object.__new__(WorkshopApp);app.busy=False;app.project=self.session.project;app.sdk_root=root;app.workspace=self.root/'workspace';app.status=Mock()
        with patch('master_rallye.workshop.gui.subprocess.Popen') as launch:
            app.open_live_texture_studio();args=launch.call_args.args[0]
            self.assertEqual(args[-2:],['--vehicle',str(self.session.project.root)])
            self.assertIn(str(root/'tools/rally_workshop2.py'),args)

if __name__=='__main__':unittest.main()
