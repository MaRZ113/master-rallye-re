"""Real Windows Physics/Camera/Presentation authoring and isolated SDK builds.

Requires private, qualified local project/retail inputs. Does not launch the game.
GUI actions, worker threads, renderers, compilers and validators are not mocked.
"""
import argparse,copy,json,sys,time,tkinter as tk
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.workshop.service import WorkshopProject,write_json
from master_rallye.workshop.vehicle_authoring import sha
from master_rallye.workshop.gui import WorkshopApp
from validate_rally_workshop import screenshot

def hashes(root):return {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in root.rglob('*') if p.is_file()}

def prepare(reference,out):
    base=WorkshopProject(reference);p=WorkshopProject.create(base.working,out);p.configure_build(base.data['build_settings']);p.audio_state();p.vehicle_state();return p

def changed(before,after):return {k:{'before':before.get(k),'after':after.get(k)} for k in sorted(set(before)|set(after)) if before.get(k)!=after.get(k)}

def gui(a):
    p=prepare(a.reference,a.output/'project');original_audio=p.audio_compile()[0];audio_state=copy.deepcopy(p.audio_state());assets=hashes(p.assets)
    root=tk.Tk();app=WorkshopApp(root,a.output/'workspace',ROOT,a.viewer);errors=[];captures=[];report={'status':'RUNNING','gameplay':'PENDING_OWNER','project':str(p.root)}
    def check(condition,message):
        if not condition:raise AssertionError(message)
    def capture(label,tab):
        app.vehicle_tabs.select(tab);root.update();screenshot(app.vehicle_window,a.output/(label+'.png'));captures.append(label)
    def select_field(path):
        item=next(k for k,v in app.phys_rows.items() if v['path']==path);app.phys_tree.selection_set(item);app.phys_tree.see(item);app.physics_selected()
    def field(path,value):select_field(path);app.phys_fields[0].set(str(value));app.physics_apply()
    def physics_ready():
        report['physics_source']=app.physics_info
        select_field('Chassis/TotalMass');report['original_mass']=app.phys_selected['value'];capture('physics-original',app.physics_tab)
        field('Engine/RevLimit',next(v['value'] for v in app.phys_rows.values() if v['path']=='Engine/RevLimit')+100)
    def audio_unchanged():check(app.project.audio_compile()[0]==original_audio and app.project.audio_state()==audio_state,'Physics changed Audio sources/presets')
    def mass():field('Chassis/TotalMass',report['original_mass']*1.05)
    def copy_reference():
        select_field('Steering/MaxTurnAngle') if any(v['path']=='Steering/MaxTurnAngle' for v in app.phys_rows.values()) else select_field('Chassis/TotalMass')
        app.physics_copy()
    def physics_capture():audio_unchanged();capture('physics-edited',app.physics_tab)
    def camera_edit():
        report['camera_source']=app.camera_info
        app.camera_fields['car_id'].set('28');app.camera_fields['half_length_m'].set('2.2');app.camera_fields['height_m'].set('1.4');app.camera_apply()
    def camera_capture():capture('camera-edited',app.camera_tab)
    def details():
        values={'manufacturer':'MITSUBISHI','model':'EVO IV WORKSHOP','combined':'MITSUBISHI EVO IV WORKSHOP','display_name':'EVO IV STUDIO','description':'Reversible Physics / Camera / Vehicle Presentation Windows demonstration.'}
        for k,v in values.items():app.details_fields[k].set(v)
        report['display_names']=values;app.details_apply()
    def alias(index,label):
        from master_rallye.dx import parse_dx_bytes
        name='gt4-ad685e510aa08e4ace49-tga.dxt' if index==0 else parse_dx_bytes((app.project.assets/'wheel.dx').read_bytes()).physical_draws[0].texture_tuple[0]+'.dxt'
        check(name in app.project.data['inputs'],'Qualified pilot alias target missing')
        report.setdefault('aliases',[]).append(name);app.alias_search.set('');app.alias_tree.selection_set(name);app.alias_name.set(label);app.alias_apply()
    def aliases_capture():
        app.alias_search.set('Studio');check(len(app.project.texture_search('Studio'))==2,'Alias search failed');capture('vehicle-details',app.details_tab);app.alias_search.set('')
    def generate():
        report['ui_before_apply']=sha((app.project.working/'ui-assets.json').read_bytes());app.art_role.set('both');app.art_model.set('complete.dx');app.art_generate_ui()
    def generated():
        check(sha((app.project.working/'ui-assets.json').read_bytes())==report['ui_before_apply'],'Generation applied art implicitly')
        check(set(app.pending_art)=={'vehicle_select_art','smallcarsheet'},'Missing UI role');report['art']=copy.deepcopy(app.pending_art);capture('art-review-before-apply',app.art_tab)
        app.art_apply_ui()
    def applied():
        check(set(app.project.vehicle_state()['art'])=={'vehicle_select_art','smallcarsheet'},'Art not saved');capture('art-applied',app.art_tab)
        from master_rallye.addon_sdk.ui_assets import decode_rgba_png
        for role,entry in report['art'].items():check(decode_rgba_png(app.project.art_preview_png(role))==decode_rgba_png(Path(entry['png']).read_bytes()),'Compiled bank differs from reviewed art')
    def reopened():
        before=app.project.vehicle_state();app.project=WorkshopProject(p.root);app.project.materialize();check(before==app.project.vehicle_state(),'Vehicle state lost on reopen');audio_unchanged();app.vehicle_loaded()
        check(hashes(app.project.assets)==assets,'Nonvisual authoring changed DX/DXT model assets')
        app.project.vehicle_reset('camera');check(app.project.vehicle_state()['camera'] is None,'Camera reset failed');app.project.undo();check(app.project.vehicle_state()==before,'Camera reset undo changed another category')
        app.project.vehicle_reset('art');check(not app.project.vehicle_state()['art'],'Art reset failed');app.project.undo();check(app.project.vehicle_state()==before,'Art reset undo changed another category')
        app.vehicle_loaded();capture('reopened',app.details_tab)
    def built():
        build=Path(app.project.data['last_build']);from validate_sdk_roster import validate
        result=validate(json.loads((build/'roster.json').read_text()),build/'candidate');write_json(a.output/'roster-validation.json',result)
        baseline=hashes(a.baseline_runtime/'resource-root');current=hashes(build/'candidate/runtime/resource-root');diff=changed(baseline,current)
        check('DataGame/vehicles.xml' in diff,'Physics not compiled')
        check(not any(k.endswith('.wav') or k.endswith('.dx') for k in diff),'Physics/camera/metadata/art changed audio/geometry')
        check(len(diff)==3,'Unexpected resource changes: '+str(list(diff)))
        audio_unchanged();report.update(status='PASS_ACTUAL_WINDOWS_VEHICLE_STUDIOS',captures=captures,build=str(build),resource_differences=diff,geometry_unchanged=True,audio_unchanged=True)
        write_json(a.output/'windows-validation.json',report);app.close()
    def reference_load():app.phys_reference.set('Megane2');app.physics_load()
    def help_capture():
        app.show_help('physics-camera');win=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel) and w.title().endswith('Offline Help'));screenshot(win,a.output/'offline-help.png');win.destroy()
    steps=[lambda:app._opened(p),app.open_vehicle_studios,app.physics_load,physics_ready,audio_unchanged,app.undo,
           reference_load,copy_reference,app.undo,mass,physics_capture,app.camera_load,camera_edit,camera_capture,
           app.undo,app.redo,camera_capture,details,lambda:alias(0,'Body livery atlas Studio'),lambda:alias(1,'Wheel face / tyre atlas Studio'),aliases_capture,
           generate,generated,applied,app.undo,app.redo,app.save,reopened,help_capture,app.validate,app.build,built]
    index=0;idle=0;last=time.monotonic()
    def tick():
        nonlocal index,idle,last
        try:
            if errors:raise ValueError(errors)
            if time.monotonic()-last>480:raise TimeoutError('Windows authoring worker timeout')
            if index==1 and app.project is None:root.after(150,tick);return
            idle=0 if app.busy else idle+1
            if idle>=3:
                print('GUI STEP',index,flush=True);steps[index]();index+=1;idle=0;last=time.monotonic()
            if index<len(steps):root.after(150,tick)
        except Exception as exc:
            import traceback
            report.update(status='FAIL',step=index,error=str(exc),traceback=traceback.format_exc());write_json(a.output/'windows-validation.json',report);app.close()
    root.report_callback_exception=lambda *args:errors.append(str(args))
    with patch('master_rallye.workshop.gui.messagebox.showerror',side_effect=lambda *args,**kw:errors.append(str(args))):root.after(300,tick);root.mainloop()
    if report['status']!='PASS_ACTUAL_WINDOWS_VEHICLE_STUDIOS':raise ValueError({k:report.get(k) for k in ('status','step','error','traceback')})
    return report

def isolated(a):
    base=hashes(a.baseline_runtime/'resource-root');result={}
    for case in ('physics','camera'):
        p=prepare(a.reference,a.output/('project-'+case))
        if case=='physics':
            row=next(r for r in p.physics_inspect()['rows'] if r['path']=='Chassis/TotalMass');p.physics_update(row['member'],row['path'],row['value']*1.05)
        else:p.camera_update(2.2,1.4,28)
        out=a.output/case;p.build(out,sdk_root=ROOT,log=lambda s:print(case,s,flush=True))
        diff=changed(base,hashes(out/'candidate/runtime/resource-root'))
        assert set(diff)==({'DataGame/vehicles.xml'} if case=='physics' else set()),list(diff)
        from validate_sdk_roster import validate
        validation=validate(json.loads((out/'roster.json').read_text()),out/'candidate');write_json(out/'validation.json',validation)
        result[case]={'project':str(p.root),'build':str(out),'resource_differences':diff}
        if case=='camera':
            from master_rallye.addon_sdk.camera_profile import bind_camera_profile
            from validate_vehicle_camera_native import validate as native
            binding=bind_camera_profile(p.vehicle_state()['camera'],p.camera_source());write_json(out/'binding.json',binding)
            write_json(out/'native-replay.json',native((ROOT.parent/'MRallye.exe').read_bytes(),binding))
    write_json(a.output/'isolated-validation.json',{'status':'PASS_INDEPENDENT_PHYSICS_CAMERA_BUILDS','cases':result,'gameplay':'PENDING_OWNER'})

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('reference','baseline-runtime','viewer','output'):parser.add_argument('--'+key,type=Path,required=True)
    parser.add_argument('--isolated-only',action='store_true');parser.add_argument('--gui-only',action='store_true');a=parser.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    if not a.gui_only:isolated(a)
    if not a.isolated_only:gui(a)
if __name__=='__main__':main()
