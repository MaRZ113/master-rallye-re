"""Exercise the real Qt editor and embedded D3D9 texture cycle, without a game.

Writes fresh evidence only to --output. PNG drawing represents an external
editor saving the exported file; import/reload/save/reopen use the SDK UI.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from PySide6 import QtCore as Q,QtGui as G,QtWidgets as W,QtTest
from master_rallye.workshop.qt_editor import Editor
from unittest.mock import patch


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--viewer',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    out=args.output.resolve()
    if out.exists():raise ValueError('Use a fresh evidence directory')
    out.mkdir(parents=True)
    import faulthandler
    trace=(out/'stacks.txt').open('w');faulthandler.dump_traceback_later(20,repeat=True,file=trace)
    app=W.QApplication([]);window=Editor(out/'workspace',args.viewer.resolve());window.show();studio=window.textures;window.workspaces.setCurrentWidget(studio)
    report={'source':str(args.source),'checks':{},'timings':{}}
    def wait_ready():
        start=time.perf_counter()
        while studio.loading or window.task:
            app.processEvents();time.sleep(.01) # release the GIL for file staging
            if window.last_error:raise RuntimeError(window.last_error)
            if time.perf_counter()-start>45:raise TimeoutError(window.status.text())
        assert studio.viewport.hwnd,window.status.text()
        app.processEvents();QtTest.QTest.qWait(150)
    def state():
        studio.viewport.message(0x8019)
        return json.loads(studio.viewport.state.read_text())
    def capture(label):
        studio.viewport.message(0x8016) # remove selection wire for a fair A/B
        studio.viewport.message(0x8018)
        source=Path(str(studio.viewport.state)+'.bmp');dest=out/(label+'.bmp');dest.write_bytes(source.read_bytes())
        return hashlib.sha256(dest.read_bytes()).hexdigest()
    def select(name):
        iterator=W.QTreeWidgetItemIterator(studio.tree)
        while iterator.value():
            item=iterator.value();data=item.data(0,Q.Qt.ItemDataRole.UserRole)
            if data and data[0]==name and data[1] and data[1]['stage']==0:
                studio.tree.setCurrentItem(item);return
            iterator+=1
        raise ValueError('Texture not found '+name)
    def click(label):
        button=next(b for b in studio.findChildren(W.QPushButton) if b.text()==label)
        QtTest.QTest.mouseClick(button,Q.Qt.MouseButton.LeftButton)
        if window.last_error:raise RuntimeError(window.last_error)
    try:
        before={str(f.relative_to(args.source)):hashlib.sha256(f.read_bytes()).hexdigest() for f in args.source.rglob('*') if f.is_file()}
        with patch.object(W.QFileDialog,'getExistingDirectory',return_value=str(args.source.resolve())):click('Open Vehicle')
        wait_ready();report['timings'].update(studio.metrics)
        assert studio.session.metadata['physical_id']==31
        studio.save_livery(out/'Stock');stock_id=studio.session.metadata['livery_id']
        studio.new_livery('Master Rallye Custom');studio.fields['number'].setText('31');studio.fields['crew'].setText('Master Rallye Custom');studio.fields['source'].setText('V-TEX2 SDK roundtrip demonstration');studio.metadata_changed()
        select('ravside2128-tga.dxt')
        with patch.object(W.QFileDialog,'getSaveFileName',return_value=(str(out/'ravside2128.png'),'PNG (*.png)')):click('Export PNG / Image')
        studio.export_all(out/'png-export');studio.export_uv(out/'ravside2128.uv.png')
        report['checks']['actual_open_export_import_buttons']=True
        stock_hash=capture('stock')
        # External editor stand-in: draw a separate custom sticker on the exact
        # upright atlas, preserving dimensions and avoiding every other resource.
        image=G.QImage(str(out/'ravside2128.png')).convertToFormat(G.QImage.Format.Format_RGBA8888)
        painter=G.QPainter(image);painter.fillRect(10,0,99,18,G.QColor('#183c85'));painter.setPen(G.QColor('#ffffff'));font=G.QFont('Arial',10);font.setBold(True);painter.setFont(font);painter.drawText(Q.QRect(10,0,99,18),Q.Qt.AlignmentFlag.AlignCenter,'MR CUSTOM 31');painter.end();assert image.save(str(out/'ravside2128.png'),'PNG')
        # Exercise camera mouse events against the real child HWND.
        viewport=studio.viewport
        viewport.message(0x201,1,100|(100<<16));viewport.message(0x200,1,150|(125<<16));viewport.message(0x202,0,150|(125<<16))
        viewport.message(0x20a,120<<16,0)
        orbit=state();assert orbit['az']!=.65
        viewport.message(0x207,16,80|(80<<16));viewport.message(0x200,16,110|(100<<16));viewport.message(0x208,0,110|(100<<16))
        camera=state();stock_hash=capture('stock-same-camera')
        with patch.object(W.QFileDialog,'getOpenFileName',return_value=(str(out/'ravside2128.png'),'PNG (*.png)')):click('Import PNG / Image')
        after=state()
        for key in ('az','el','distance','centre','scene_loads','model','selected'):assert after[key]==camera[key],(key,camera,after)
        assert after['texture_updates']==camera['texture_updates']+1,(camera,after)
        modified_hash=capture('modified');assert stock_hash!=modified_hash,'Imported texture did not change rendered pixels'
        original=studio.session.project.baseline/'ravside2128-tga.dxt';changed=studio.session.project.assets/original.name
        assert original.read_bytes()[23::4]==changed.read_bytes()[23::4]
        assert set(studio.session.project.data['edits'])=={'ravside2128-tga.dxt'}
        studio.original.setChecked(True);assert capture('original-toggle')==stock_hash
        studio.original.setChecked(False);assert capture('modified-toggle')==modified_hash
        studio.undo();assert capture('undo')==stock_hash
        studio.redo();assert capture('redo')==modified_hash
        studio.restore();assert capture('restore')==stock_hash
        studio.reload_png();assert capture('reload')==modified_hash
        # Additional scope: common image formats normalize through Pillow into
        # the same codec. Texture selection and the live camera remain stable.
        from PIL import Image,ImageGrab
        rgb=Image.open(out/'ravside2128.png').convert('RGB')
        for extension,fmt in [('jpg','JPEG'),('bmp','BMP'),('webp','WEBP'),('gif','GIF'),('tga','TGA'),('tiff','TIFF')]:
            path=out/('external.'+extension);rgb.save(path,format=fmt);studio.import_png(path)
        studio.import_png(out/'ravside2128.png')
        report['checks']['multiformat_live_import']=True
        def wait_art():
            start=time.perf_counter()
            while window.task:
                app.processEvents();time.sleep(.01)
                if time.perf_counter()-start>30:raise TimeoutError('Artwork timeout')
            if window.last_error:raise RuntimeError(window.last_error)
        art_camera=state();studio.artwork.generate();wait_art();assert 'vehicle_select_art' not in studio.session.artwork;studio.artwork.accept_candidate();studio.artwork.export_png(out/'carsheet.png')
        studio.artwork.role.setCurrentIndex(1);studio.artwork.generate();wait_art();studio.artwork.accept_candidate();studio.artwork.export_png(out/'side.png')
        for entry in studio.session.artwork.values():
            with Image.open(entry['source_png']) as im:
                bounds=im.getchannel('A').point(lambda a:255 if a>20 else 0).getbbox()
                assert 0<bounds[0]<bounds[2]<im.width and 0<bounds[1]<bounds[3]<im.height,bounds
            with Image.open(entry['png']) as im:
                bounds=im.getchannel('A').point(lambda a:255 if a>20 else 0).getbbox()
                assert 0<bounds[0]<bounds[2]<im.width and 0<bounds[1]<bounds[3]<im.height,bounds
        report['checks']['source_and_native_icons_not_clipped']=True
        for key in ('az','el','distance','centre','scene_loads','model','selected'):assert state()[key]==art_camera[key],key
        assert Image.open(out/'carsheet.png').size==(128,128);assert Image.open(out/'side.png').size==(32,16)
        assert Image.open(out/'side.png').getchannel('A').getextrema()[0]==0
        # Qualified synthetic FEED template tests frame conversion without reading/writing a game bank.
        import zlib
        template=out/'side-template.dxt';pixels=bytes(32*16*4);template.write_bytes(__import__('struct').pack('<5I',0xfeed,1,zlib.crc32(pixels),32,16)+pixels)
        studio.artwork.export_native(template,out/'side-generated.dxt')
        import copy
        generated_side=copy.deepcopy(studio.session.artwork['smallcarsheet'])
        studio.artwork.manual(out/'side.png','Custom')
        # Simulate a protected historical selection for the non-overwrite gate.
        # Restore its truthful Reconstruction provenance before packaging.
        studio.session.artwork['smallcarsheet']['historical_original']=True
        historical=studio.session.artwork['smallcarsheet']['sha256']
        studio.artwork.generate();wait_art();assert studio.session.artwork['smallcarsheet']['sha256']==historical
        studio.artwork.accept_candidate();assert studio.session.artwork_archive[-1]['historical_original']
        studio.session.artwork['smallcarsheet']=generated_side
        studio.save_livery(out/'archive-roundtrip')
        from master_rallye.workshop.livery import LiverySession
        archive_check=LiverySession.open_package(out/'archive-roundtrip/livery.json',out/'archive-check')
        assert archive_check.artwork_archive[-1]['historical_original']
        studio.session.artwork_archive=[] # synthetic protection fixture never enters the delivered livery
        report['checks'].update(carsheet_side_live_generation=True,artwork_camera_retained=True,transparent_side=True,native_artwork_frame=True,historical_preferred=True)
        studio.save_livery(out/'Master-Rallye-Custom');livery_id=studio.session.metadata['livery_id'];assert stock_id!=livery_id
        report['checks'].update(live_render_pixels_changed=True,only_one_gpu_texture_updated=True,camera_retained=True,geometry_not_reloaded=True,original_modified=True,undo_redo_restore=True,alpha_preserved=True)
        report['timings'].update(studio.metrics);report['viewport_before']=camera;report['viewport_after']=after
        app.processEvents();time.sleep(.1)
        # QWidget.grab does not include cross-process child HWNDs. Preserve
        # separate captures and an explicitly labelled evidence composition.
        widget=window.grab().toImage();capture('embedded-viewport')
        painter=G.QPainter(widget);point=studio.viewport.mapTo(window,Q.QPoint(0,0))
        painter.drawImage(Q.QRect(point,studio.viewport.size()),G.QImage(str(out/'embedded-viewport.bmp')));painter.end()
        widget.save(str(out/'integrated-sdk-evidence.png'))
        report['capture_method']='Qt widget grab + actual embedded HWND backbuffer, evidence composition only'
        studio.load_vehicle(out/'Master-Rallye-Custom/livery.json',True);wait_ready();assert studio.session.metadata['livery_id']==livery_id;assert studio.session.metadata['physical_id']==31
        assert not studio.session.dirty
        assert set(studio.session.artwork)=={'vehicle_select_art','smallcarsheet'}
        assert (studio.session.project.assets/'ravside2128-tga.dxt').read_bytes()==changed.read_bytes()
        report['checks']['save_reopen']=True
        assert studio.variant.isReadOnly()
        studio.variant.setText('PS2');studio.metadata_changed();assert studio.session.metadata['model_variant']=='PC';studio.fill_metadata()
        duplicate_pixels=(studio.session.project.assets/'ravside2128-tga.dxt').read_bytes();old=studio.session.metadata['livery_id']
        studio.duplicate_livery('Current copy');assert studio.session.metadata['livery_id']!=old
        livery_id=studio.session.metadata['livery_id']
        assert (studio.session.project.assets/'ravside2128-tga.dxt').read_bytes()==duplicate_pixels
        signature=studio.session.full_signature()
        with patch.object(W.QMessageBox,'warning',return_value=W.QMessageBox.StandardButton.Cancel):studio.new_livery('Must not reset')
        assert studio.session.full_signature()==signature
        report['checks'].update(duplicate_current=True,cancel_unsaved_reset=True,model_variant_read_only=True,historical_archive_reopened=True)
        # Presets and model switch remain independent from livery identity.
        for index in range(6):studio.view.setCurrentIndex(index);app.processEvents()
        studio.model.setCurrentIndex(1);assert state()['model']==1;studio.model.setCurrentIndex(0);assert state()['model']==2
        assert studio.session.metadata['livery_id']==livery_id
        report['checks']['presets_and_model_roles']=True
        # Warm repeated upload, bypassing atlas redraw only for driver timing.
        times=[];texture=studio.session.project.texture('ravside2128-tga.dxt')
        for _ in range(20):
            start=time.perf_counter();viewport.packet(1,'ravside2128-tga.dxt',texture);times.append(time.perf_counter()-start)
        report['timings']['gpu_upload_ms_median']=sorted(times)[len(times)//2]*1000
        report['timings']['gpu_upload_ms_max']=max(times)*1000
        QtTest.QTest.qWait(1100);report['viewport_final']=state()
        after_source={str(f.relative_to(args.source)):hashlib.sha256(f.read_bytes()).hexdigest() for f in args.source.rglob('*') if f.is_file()}
        assert before==after_source;report['checks']['source_unchanged']=True
        generic=[]
        for family,physical in [('DefForester',30),('DefTomcat',32)]:
            source=args.source.resolve().parent/family
            if not source.exists():raise FileNotFoundError(source)
            studio.load_vehicle(source);wait_ready();assert studio.session.metadata['physical_id']==physical
            name=next(n for n in studio.session.index() if n in studio.viewport.active and any(u['stage']==0 for u in studio.session.index()[n]))
            select(name);png=out/(family+'.png');studio.export_png(png)
            im=Image.open(png).convert('RGBA');pixel=im.getpixel((0,0));im.putpixel((0,0),((pixel[0]+71)%256,pixel[1],pixel[2],pixel[3]));im.save(png)
            camera=state();studio.import_png(png);changed=state();assert changed['scene_loads']==camera['scene_loads'];assert changed['texture_updates']==camera['texture_updates']+1
            studio.save_livery(out/(family+'-livery'));studio.restore();generic.append({'family':family,'physical_id':physical,'texture':name,'timings':dict(studio.metrics)})
        report['generic_families']=generic
        report['checks']['forester_tomcat_generic_cycle']=True
        report['status']='QT_D3D9_AUTOMATED_CYCLE_PASS; OWNER_VISUAL_REVIEW_PENDING'
    finally:
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');window.close();app.processEvents()
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
