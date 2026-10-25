"""Private-input Windows checks for wheel staging, fixed camera views and image inspection.

No GT/retail assets are bundled. This validates the Previewer, not MR gameplay.
"""

def main():
    from pathlib import Path
    import sys,json,subprocess,hashlib,tkinter as tk,time
    root=Path(__file__).resolve().parents[1];sys.path[:0]=[str(root/'src'),str(root/'tools')]
    from master_rallye.workshop.service import WorkshopProject,write_json
    from master_rallye.preview_scene import stage_vehicle
    from master_rallye.workshop.gui import WorkshopApp
    from validate_rally_workshop import screenshot
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--library',type=Path,required=True);parser.add_argument('--viewer',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True);viewer=args.viewer.resolve()
    report={'boundary':'Native Previewer diagnostic captures only; no game resources modified','vehicles':[]}
    paths=json.loads(args.library.read_text())
    for i,path in enumerate(paths):
     p=WorkshopProject(path);p.materialize();d=out/str(i);d.mkdir(exist_ok=True);scene=d/'family.mrpv';r=stage_vehicle(p.assets/'car.dx',scene,profile=p.preview_profile_path());before=scene.read_bytes();hashes={n:hashlib.sha256((p.baseline/n).read_bytes()).hexdigest() for n in ('car.dx','complete.dx','wheel.dx')}
     for name,az in [('front-left',-40),('front-right',40),('rear-left',-140),('rear-right',140),('side',90),('opposite',-90)]:
      args=[str(viewer),'--scene',str(scene),'--model','race','--capture',str(d/(name+'.bmp')),'--azimuth',str(az),'--zoom','.75']
      subprocess.run(args,check=True,timeout=25)
     for model,extra in [('raw',['--raw-race']),('frontend',[]),('wheel',[])]:subprocess.run([str(viewer),'--scene',str(scene),'--model','race' if model=='raw' else model,'--capture',str(d/(model+'.bmp')),*extra],check=True,timeout=25)
     assert scene.read_bytes()==before
     q=WorkshopProject(path);q.materialize();assert hashes=={n:hashlib.sha256((q.assets/n).read_bytes()).hexdigest() for n in hashes}
     report['vehicles'].append({'identity':p.data['identity'],'baseline_dx':hashes,'staged_geometry_static_during_orbit':True,'wheel_outside_camera':r['wheel_outside_camera'],'wheel_profile':r['profile'],'embedded_wheels':r['embedded_four_wheel_match'],'wheel_geometry':r['wheel_geometry'],'mirror_corrections':r['instance_handedness']})
     write_json(out/'wheel-validation.json',report)
    # Real Tk texture inspector and persisted preview-only adjustment.
    p=WorkshopProject(paths[0]);original=p.preview_profile();had_preview='preview_only' in p.data;original_saved=p.data.get('preview_only');edited=json.loads(json.dumps(original))
    if len(edited.get('race_wheel_instances',[]))!=4:raise ValueError('First validation project needs a qualified four-wheel preview profile')
    try:
        edited['race_wheel_instances'][0]['translation'][1]+=.01;p.save_preview_profile(edited);assert WorkshopProject(p.root).preview_profile()==edited
    finally:
        if had_preview:p.data['preview_only']=original_saved
        else:p.data.pop('preview_only',None)
        p.save()
    app_root=tk.Tk()
    def tk_error(*args):raise RuntimeError('Tk callback failed: '+str(args))
    app_root.report_callback_exception=tk_error
    app=WorkshopApp(app_root,out/'texture-check-workspace',root,viewer)
    app.project=p;p.materialize();name=max(p.assets.glob('*.dxt'),key=lambda f:f.stat().st_size).name;app.texture_name.set(name);app.show_texture();app.detach_texture()
    for _ in range(12):app_root.update();time.sleep(.1)
    app.detached_view.actual();app.detached_view.channel.set('Alpha')
    for _ in range(10):app_root.update();time.sleep(.1)
    screenshot(app.texture_popup,out/'large-texture-alpha.png');app.detached_view.channel.set('RGBA');app.detached_view.zoom(2)
    for _ in range(10):app_root.update();time.sleep(.1)
    screenshot(app.texture_popup,out/'large-texture-rgba.png');app_root.destroy()
    report['texture']={'name':name,'dimensions':[app.detached_view.texture.width,app.detached_view.texture.height],'fit_actual_zoom_pan_channels':'Real Tk controls exercised; owner interaction pending'};report['preview_config_roundtrip']=True;write_json(out/'wheel-validation.json',report)

if __name__=='__main__':main()
