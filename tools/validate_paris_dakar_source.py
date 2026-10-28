"""Source-qualified local validation. Proprietary evidence stays private."""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import sys
import time
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src'),str(Path(__file__).resolve().parent)]
from master_rallye import universal_vehicle_scene as u
from master_rallye.source_adapters import paris_dakar as a, paris_dakar_formats as f
from master_rallye.source_scene_preview import stage_source_scene, capture_views, preview_cull


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--viewer',type=Path,required=True)
    p.add_argument('--tk',action='store_true');args=p.parse_args();root=args.source_root.absolute()
    out=u.output_directory(args.output,[root,root.parent]);out.mkdir(parents=True)
    originals=[root/'dakar.exe',*[root/'Data'/name for name in a.QUALIFIED]]
    def snapshot():return {str(p):{'sha256':u.sha(u.read_bounded(p,f.MAX_FILE)),'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns}for p in originals}
    before=snapshot();report={'schema':'paris-dakar-source-validation/1','originals':before,'vehicles':{}}
    expected={'PajeroRED.tc':(65,8,56,1376),'PajeroSilver.tc':(65,8,56,1446),'NissanPatrol.tc':(72,11,60,1562)}
    keys=f.executable_keys(u.read_bounded(root/'dakar.exe',4*1024*1024));viewer=args.viewer.absolute()
    for catalog in a.QUALIFIED:
        data=u.read_bounded(root/'Data'/catalog,f.MAX_FILE);tc,desc,models,textures=a.inspect(data,keys)
        actual=(len(tc['entries']),len(models),len(textures),models['MainBody']['triangles'])
        if actual!=expected[catalog]:raise AssertionError('source structural golden differs: '+catalog)
        folder=out/catalog[:-3];one=a.create_scene(root,folder/'scene',catalog);two=a.create_scene(root,folder/'repeat',catalog)
        if one['manifest_sha256']!=two['manifest_sha256']:raise AssertionError('nondeterministic source scene')
        scene=u.load_scene(Path(one['scene']));saved=u.canonical(scene);geometry={}
        signs={'positive':0,'negative':0,'degenerate':0}
        for model in models.values():
            for batch in model['batches']:
                for face in batch['triangles']:
                    ps=[batch['positions'][i]for i in face];ns=[batch['normals'][i]for i in face]
                    v=[ps[1][k]-ps[0][k]for k in range(3)];w=[ps[2][k]-ps[0][k]for k in range(3)]
                    cross=[v[1]*w[2]-v[2]*w[1],v[2]*w[0]-v[0]*w[2],v[0]*w[1]-v[1]*w[0]]
                    dot=sum(cross[k]*sum(n[k]for n in ns)for k in range(3))
                    signs['positive'if dot>1e-10 else'negative'if dot< -1e-10 else'degenerate']+=1
        for basis in ('source','normalized'):
            path=folder/(basis+'.mrpv');staged=stage_source_scene(scene,path,scene_root=Path(one['scene']).parent,basis=basis)
            capture_views(viewer,path,folder/('views-'+basis),basis=basis,cull=preview_cull(scene),
                          provenance=catalog+' | original source | static attach pose | neutral D3D9')
            from validate_source_garage_preview import positions_from_mrpv
            geometry[basis]=positions_from_mrpv(path)
        error=max(abs(u.transform_point(a.NORMALIZATION,p)[k]-n[k])for key,points in geometry['source'].items()
                  for p,n in zip(points,geometry['normalized'][key])for k in range(3))
        if error>2e-6:raise AssertionError('normalization mismatch')
        # Diagnostic copies exercise material IDs and component isolation.
        stage_source_scene(scene,folder/'material-ids.mrpv',scene_root=Path(one['scene']).parent,material_mode='material_ids')
        for role in ('body','wheel','shadow'):
            derived=copy.deepcopy(scene)
            for node in derived['nodes']:node['visible']=node['role']==role
            stage_source_scene(derived,folder/(role+'-only.mrpv'),scene_root=Path(one['scene']).parent)
        if saved!=u.canonical(scene):raise AssertionError('preview mutated original scene')
        report['vehicles'][catalog]={'generation':one,'structural_golden':actual,'source_normal_winding_dot':signs,
                                     'normalization_max_error':error,'deterministic_manifest':True,'immutable_scene':True,
                                     'preview_cull':preview_cull(scene),'donor_runtime_parity':'NOT TESTED'}
    if args.tk:
        import tkinter as tk
        from master_rallye.workshop.gui import WorkshopApp
        from master_rallye.workshop.source_garage_ui import preview_configuration
        from validate_rally_workshop import screenshot
        gui=tk.Tk();errors=[];gui.report_callback_exception=lambda *e:errors.append(str(e))
        repo=Path(__file__).resolve().parents[1];app=WorkshopApp(gui,out/'ui-workspace',repo,viewer)
        app.open_source_garage();window=app.source_garage_window;rows=[]
        try:
            for catalog in a.QUALIFIED:
                scene_path=out/catalog[:-3]/'scene/scene.json';window._open(scene_path);gui.update()
                if not window.action_buttons['Create 4Runner Stable…'].instate(['disabled']):raise AssertionError('native creation not gated')
                if window.settings()['wheel_detail']is not None:raise AssertionError('Evo2 wheel choice leaked into other donor')
                window.preview();deadline=time.monotonic()+60
                while app.busy and time.monotonic()<deadline:gui.update();time.sleep(.02)
                if errors or app.busy or not window.photos:raise AssertionError('actual Source Garage render failed '+str(errors))
                screenshot(window.window,out/(catalog[:-3]+'-workshop.png'));rows.append({'catalog':catalog,'rows':len(window.rows),'rendered':True,'native_disabled':True})
                nodekey=next(iter(window.rows));window.tree.selection_set(nodekey);window.selected();gui.update()
                preview_configuration(window.scene,window.settings())
            report['windows_tk']=rows
        finally:
            gui.after_idle(app.close);gui.mainloop()
    if before!=snapshot():raise AssertionError('original source hash/mtime changed')
    report['source_hash_sizes_mtimes_unchanged']=True;report['status']='PASS'
    (out/'validation.json').write_bytes(u.canonical(report));print(json.dumps({'status':'PASS','output':str(out),'vehicles':list(report['vehicles'])}))


if __name__=='__main__':main()
