"""Windows/private-input Audio Studio acceptance and five isolated SDK builds.

Generated audition tones are original test signals, not attributed GT samples.
No game is launched; native sound ownership is tested separately by x86 replay.
"""
import argparse,copy,hashlib,json,math,random,sys,time,tkinter as tk
from pathlib import Path
from tkinter import ttk
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.workshop.service import WorkshopProject,write_json
from master_rallye.workshop.audio import LAYERS,sha
from master_rallye.addon_sdk.audio_profile import canonical_wav
from validate_rally_workshop import screenshot,descendants

def tones(output):
    output.mkdir(parents=True,exist_ok=True);rng=random.Random(431)
    result={}
    for key in LAYERS:
        count=16800 if key=='bov_release' else 48000
        samples=[]
        for i in range(count):
            t=i/48000
            if key=='engine':v=1800*math.sin(2*math.pi*160*t)+800*math.sin(2*math.pi*320*t)+400*math.sin(2*math.pi*480*t)
            elif key=='transmission_whine':v=2200*math.sin(2*math.pi*760*t)+500*math.sin(2*math.pi*1520*t)
            elif key=='turbo_spool':v=1800*math.sin(2*math.pi*1900*t)+500*rng.uniform(-1,1)
            else:v=5000*rng.uniform(-1,1)*math.exp(-t*12)*min(1,t*500)
            samples.append(round(v))
        path=output/(key+'.wav');path.write_bytes(canonical_wav(samples));result[key]=path
    return result

def resource_hashes(folder):return {p.relative_to(folder).as_posix():sha(p.read_bytes()) for p in folder.rglob('*') if p.is_file()}

def prepare(source,output,settings):
    p=WorkshopProject.create(source,output);p.configure_build(settings);p.audio_state();return p

def build_matrix(a,signals,settings):
    report={'status':'RUNNING','cases':{},'boundary':'Resource/native package and Windows tests only; future owner gameplay listening required'}
    baseline=WorkshopProject(a.reference)
    # Exact accepted Source Fidelity resource-root, supplied explicitly.
    base_resources=resource_hashes(a.baseline_runtime/'resource-root')
    first=prepare(baseline.working,a.output/'projects/base',settings);base_wavs,base_report=first.audio_compile()
    protected={p.name:sha(p.read_bytes()) for p in first.working.iterdir() if p.is_file() and p.name not in ('audio-profile.json',)}
    for case,selected in zip('abcde',[(LAYERS[0],),(LAYERS[1],),(LAYERS[2],),(LAYERS[3],),LAYERS]):
        print('BEGIN',case,flush=True)
        p=prepare(baseline.working,a.output/'projects'/case,settings)
        for layer in selected:p.audio_import(layer,signals[layer],crossfade=0)
        p.audio_save_preset('Audio Studio '+case.upper())
        wavs,detail=p.audio_compile();diff=[name for name in wavs if base_wavs[name]!=wavs[name]]
        expected=[base_report['resource_path'] if layer=='engine' else base_report[layer]['resource_path'] for layer in selected]
        assert set(diff)==set(expected),(diff,expected)
        assert protected=={f.name:sha(f.read_bytes()) for f in p.working.iterdir() if f.is_file() and f.name not in ('audio-profile.json',)}
        write_json(p.root/'audio-diagnostics.json',p.audio_inspect())
        if a.build:
            p.build(a.output/case,sdk_root=ROOT,log=lambda m:print(case,m,flush=True))
            target=a.output/case/'candidate';root=target/'runtime/resource-root'
            # Actual layout discovered from sealed manifest, never guessed.
            if not root.is_dir():
                roots=list(target.glob('**/resource-root'));assert len(roots)==1;root=roots[0]
            hashes=resource_hashes(root)
            changes={k:{'before':base_resources.get(k),'after':hashes.get(k)} for k in set(hashes)|set(base_resources) if hashes.get(k)!=base_resources.get(k)}
            assert set(changes)==set(expected),list(changes)
            from validate_sdk_roster import validate
            validation=validate(json.loads((a.output/case/'roster.json').read_text()),target)
            write_json(a.output/case/'roster-validation.json',validation)
        else:changes={k:{'before':sha(base_wavs[k]),'after':sha(wavs[k])} for k in diff}
        p.audio_audition(ROOT.parent/'MRallye.exe',a.output/'auditions'/(case+'.wav'),rpms=[900,4000,6000,2000],seconds=.3)
        report['cases'][case]={'selected_layers':selected,'changed_resources':changes,'project':str(p.root),'preset':'Audio Studio '+case.upper()}
        write_json(a.output/'matrix.json',report)
    report['status']='PASS_FIVE_ISOLATED_ROSTER_BUILDS' if a.build else 'PASS_FIVE_LAYER_COMPILATIONS'
    write_json(a.output/'matrix.json',report)

def gui(a,signals,settings):
    project=prepare(WorkshopProject(a.reference).working,a.output/'gui-project',settings)
    original=project.audio_compile()[0];model_hashes=resource_hashes(project.assets)
    root=tk.Tk();app=WorkshopApp(root,a.output/'gui-workspace',ROOT,a.viewer);actions=[];errors=[]
    def opened():app._opened(project)
    def tab():
        book=next(w for w in descendants(root) if isinstance(w,ttk.Notebook));book.select(app.audio_tab);app.audio_loaded();root.update()
    def capture(label):screenshot(root,a.output/(label+'.png'));actions.append(label)
    def edit(layer):
        app.audio_layer.set(layer);app.audio_loaded()
        def accept():
            window=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel) and w.title().startswith('Import local'))
            screenshot(window,a.output/('import-'+layer+'.png'))
            button=next(w for w in descendants(window) if isinstance(w,ttk.Button) and w['text']=='Import pinned copy');button.invoke()
        root.after(300,accept)
        with patch('master_rallye.workshop.audio_ui.filedialog.askopenfilename',return_value=str(signals[layer])):app.audio_import_dialog()
    def params(layer):
        app.audio_layer.set(layer);app.audio_loaded();app.audio_fields['gain_db'].set('-2');app.audio_apply()
    def preset():app.audio_preset.set('Windows authored');app.audio_save_named()
    def reopened():
        current=WorkshopProject(project.root);assert current.audio_state()['presets']['Windows authored'];app.project=current;app.audio_loaded()
    def listen(layer):
        for key in LAYERS:app.audio_solo[key].set(layer==key);app.audio_mute[key].set(False)
        app.audio_rpm.set('3500,4500,5500,3500');app.audio_load.set(1.);app.audio_lift.set(True);app.audio_listen()
    def listened(label):
        files=list((app.project.root/'auditions').glob('*.json'));assert files
        detail=json.loads(max(files,key=lambda p:p.stat().st_mtime_ns).read_text())
        assert detail['peak_pcm16']>0
        if label=='bov_release':assert sum(len(m['bov_events']) for m in detail['mix'])==1
        write_json(a.output/('audition-'+label+'.json'),detail);app.audio_stop()
        app.audio_canvas.yview_moveto(1.);root.update();capture('audio-audition-'+label)
    def assign_existing():
        app.audio_assign_dialog();window=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel) and w.title().startswith('Assign Existing'))
        items=next(w for w in descendants(window) if isinstance(w,ttk.Treeview));items.selection_set(items.get_children()[0]);screenshot(window,a.output/'assign-existing.png')
        next(w for w in descendants(window) if isinstance(w,ttk.Button)).invoke()
    steps=[opened,tab,lambda:capture('audio-original')]
    for layer in LAYERS:steps.extend([lambda k=layer:edit(k),lambda k=layer:params(k),lambda k=layer:capture('audio-'+k)])
    steps.extend([preset,app.save,app.audio_diagnostics,app.undo,app.redo,reopened,
                  lambda:app.audio_action('Restore audio',lambda:app.project.audio_reset()),
                  lambda:(_ for _ in ()).throw(AssertionError('Restore changed audio')) if app.project.audio_compile()[0]!=original else None,
                  lambda:app.audio_action('Load preset',lambda:app.project.audio_load_preset('Windows authored')),
                  lambda:capture('audio-preset-reopened'),assign_existing,app.undo,app.validate])
    for layer in (*LAYERS,'combined'):steps.extend([lambda k=layer:listen(k),lambda k=layer:listened(k)])
    index=0;started=time.monotonic()
    def tick():
        nonlocal index
        try:
            if time.monotonic()-started>300:raise TimeoutError('Audio GUI validation timed out')
            if app.busy:root.after(100,tick);return
            if 'ERROR:' in app.log.get('1.0','end'):raise AssertionError(app.log.get('1.0','end')[-1600:])
            if index==1 and app.project is None:root.after(100,tick);return
            if index>=len(steps):
                assert resource_hashes(app.project.assets)==model_hashes
                write_json(a.output/'windows-validation.json',{'status':'PASS_ACTUAL_WINDOWS_AUDIO_STUDIO','actions':actions,'geometry_unchanged':True,'gameplay':'PENDING_OWNER_LISTENING'})
                app.close();return
            step=steps[index];index+=1;step();root.after(200,tick)
        except Exception as exc:
            errors.append(repr(exc));write_json(a.output/'windows-validation.json',{'status':'FAIL','errors':errors,'step':index});app.close()
    root.after(200,tick);root.mainloop()
    if errors:raise RuntimeError(errors)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('reference','baseline-runtime','viewer','output'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--build',action='store_true');p.add_argument('--gui-only',action='store_true');a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    settings=WorkshopProject(a.reference).data['build_settings'];signals=tones(a.output/'original-test-tones')
    if not a.gui_only:build_matrix(a,signals,settings)
    gui(a,signals,settings)

if __name__=='__main__':
    from master_rallye.workshop.gui import WorkshopApp
    main()
