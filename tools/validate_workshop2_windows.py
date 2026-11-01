"""Actual Qt Widgets/D3D9 acceptance for one source scene and a GT-native snapshot.

Run with optional PySide6 requirements. Captures remain owner-private. Dialog
answers are supplied deterministically; actual editor controls and workers run.
No game, CarID, installer, original source write or accepted project edit.
"""
from pathlib import Path
import argparse
import json
import sys
import time
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))


def run(sources,template,stock_reference,output,viewer):
    qt_start=time.perf_counter()
    from PySide6 import QtWidgets as W,QtCore,QtTest
    from master_rallye import universal_vehicle_scene as u
    from master_rallye.editable_vehicle import EditableVehicle,build_fixture
    from master_rallye.workshop.qt_editor import Editor
    sources=[Path(p).absolute()for p in sources]
    output=u.output_directory(Path(output),[p.parent for p in sources]);output.mkdir()
    app=W.QApplication.instance()or W.QApplication([]);app.setStyle('Fusion');results=[];qt_startup=time.perf_counter()-qt_start
    template_raw=u.read_bounded(Path(template),128*1024*1024)
    def inventory(root):return {str(p.relative_to(root)):u.sha(p.read_bytes())for p in root.rglob('*')if p.is_file()}
    for number,path in enumerate(sources):
        before=inventory(path.parent);folder=output/str(number);folder.mkdir();window=Editor(folder/'workspace',viewer);window.show();timings=[]
        def settle():
            deadline=time.monotonic()+90
            while window.task and time.monotonic()<deadline:app.processEvents();time.sleep(.01)
            app.processEvents()
            if window.task:raise AssertionError('Actual Qt worker timeout')
        def timed(label,fn):
            start=time.perf_counter();fn();settle()
            if window.last_error:raise AssertionError(label+': '+window.last_error)
            timings.append({'stage':label,'seconds':time.perf_counter()-start,'status':window.status.text()})
        try:
            timed('cold open',lambda:window.load_path(path));assert window.project,window.status.text()
            window.grab().save(str(folder/'source.png'))
            timed('warm reopen',lambda:window.load_path(path))
            window.mode.setCurrentText('MR Classic')
            original_meshes=len(window.project.evaluate()['meshes'])
            window.xyz[0].setValue(window.xyz[0].value()+.01);window.move_vertex()
            window.xyz[1].setValue(window.xyz[1].value()+.02);window.add_vertex();window.uv[0].setValue(.25)
            added=len(window.mesh()['positions'])-1;window.triangle.setText('0,1,'+str(added))
            add_face=next(b for b in window.findChildren(W.QPushButton)if b.text()=='Add face');QtTest.QTest.mouseClick(add_face,QtCore.Qt.MouseButton.LeftButton)
            assert any(op['op']=='add_face'for op in window.project.document['operations'])
            scene=window.project.evaluate();wheel=next(n for n in scene['nodes']if n.get('role')=='wheel')
            index=next(i for i,m in enumerate(scene['meshes'])if m['id']==wheel['mesh_ids'][0]);window.meshes.setCurrentRow(index)
            with patch.object(W.QInputDialog,'getItem',return_value=(wheel['id'],True)):window.duplicate()
            assert len(window.project.evaluate()['meshes'])==original_meshes+1
            window.meshes.setCurrentRow(window.meshes.count()-1);window.xyz[0].setValue(.1);window.xyz[1].setValue(.1);window.xyz[2].setValue(-.3);window.translate();window.backing()
            # Explicit geometry adaptation, never source-decoder repair.
            button=next(b for b in window.findChildren(W.QPushButton)if b.text()=='Orient all derived groups to normals')
            QtTest.QTest.mouseClick(button,QtCore.Qt.MouseButton.LeftButton)
            window.role.setCurrentText('opaque_body');window.coverage.setCurrentText('opaque');window.assign_all()
            window.meshes.setCurrentRow(0);window.faces.selectAll();window.role.setCurrentText('reflective_paint')
            with patch.object(W.QFileDialog,'getOpenFileName',return_value=(str(stock_reference),'')),patch.object(W.QInputDialog,'getInt',return_value=(1,True)):
                window.copy_stock()
            assert any(m.get('authored_rule',{}).get('environment_reference')for m in window.project.evaluate()['materials']),window.status.text()
            window.faces.clearSelection();window.faces.item(0).setSelected(True);window.color.setText('255,32,12,255');window.trigger.setCurrentText('brake');window.glow()
            window.path=folder/'vehicle.edit.json';window.save();reopened=EditableVehicle.open(window.path);assert reopened.document==window.project.document
            before_undo=u.sha(u.canonical(window.project.evaluate()));window.undo();window.redo();assert u.sha(u.canonical(window.project.evaluate()))==before_undo
            window.grab().save(str(folder/'material.png'))
            timed('cold preview',window.preview);assert window.preview_path,window.status.text();window.grab().save(str(folder/'edited.png'))
            timed('warm preview',window.preview)
            first=build_fixture(reopened,folder/'native',template_raw,scale=1,references=window.references)
            second=build_fixture(reopened,folder/'native-repeat',template_raw,scale=1,references=window.references);assert first==second
            window.native_preview_root=folder/'native/native';window.brake.setChecked(False);timed('native OFF',window.native_preview);window.grab().save(str(folder/'native-off.png'))
            window.brake.setChecked(True);timed('native ON',window.native_preview);window.grab().save(str(folder/'native-on.png'))
            # A cache hit is still cancellable and cannot replace newer UI state.
            window.preview();window.cancel();settle();assert window.task is None
            window.resize(1200,760);app.processEvents();window.grab().save(str(folder/'resized.png'))
            # New editor/cache instance: disk hits survive a window/application
            # session boundary. Separate-process proof is benchmarked separately.
            window.close();app.processEvents();window=Editor(folder/'workspace',viewer);window.show();window.project=reopened;window.refresh();timed('persistent preview',window.preview)
            assert before==inventory(path.parent)
            results.append({'source':str(path),'source_sha256':u.sha(path.read_bytes()),'timings':timings,
                            'source_tree_unchanged':True,'stable_save_reopen_undo':True,'native_deterministic':True,
                            'native_files':first['files'],'cache':window.cache.stats,'gameplay':'NOT TESTED'})
        finally:window.close();app.processEvents()
    result={'schema':'workshop2-windows-acceptance/1','status':'PASS_ACTUAL_QT_AND_D3D9','vehicles':results,
            'qt_import_and_application_startup_seconds':qt_startup,
            'qt_version':QtCore.qVersion(),'embedding':'External viewer boundary; no embedding/high-DPI device-loss equivalence claimed',
            'native_boundary':'Derived geometry/material fixtures only; no CarID, physics, fitted collision or game installation'}
    (output/'validation.json').write_bytes(u.canonical(result));return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--scene',type=Path,action='append',required=True)
    p.add_argument('--template',type=Path,required=True);p.add_argument('--stock-reference',type=Path,required=True)
    p.add_argument('--viewer',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=run(a.scene,a.template,a.stock_reference,a.output,a.viewer);print(r['status'],r['qt_version'],len(r['vehicles']))
