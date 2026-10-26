"""Windows/private-source Audio Import 2.0 acceptance and isolated layer builds.

Only file-picker answers are supplied. No GT assets, native hooks or DSP mocks.
"""
import argparse,copy,json,math,struct,sys,time,tkinter as tk
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.workshop.service import WorkshopProject,write_json
from master_rallye.workshop.audio import LAYERS,sha
from master_rallye.workshop.audio_import import decoder_capabilities,run_decoder
from master_rallye.addon_sdk.audio_profile import canonical_wav
from validate_rally_workshop import screenshot
from validate_workshop_audio import resource_hashes

def prepare(a,name):
    base=WorkshopProject(a.reference);p=WorkshopProject.create(base.working,a.output/name);p.configure_build(base.data['build_settings']);p.audio_state();return p

def codecs(a):
    out=a.output/'media';out.mkdir();p=prepare(a,'codec-project');caps=decoder_capabilities();source=out/'tone.wav'
    samples=[round(12000*math.sin(i*.11)+4500*math.sin(i*.039)) for i in range(48000)];source.write_bytes(canonical_wav(samples));cases=[source]
    if caps['optional_media']:
        for name,codec,extra in [('lossless.flac','flac',[]),('lossy.mp3','libmp3lame',[]),('vorbis.ogg','libvorbis',[]),('opus.ogg','libopus',[]),('float96.wav','pcm_f32le',['-ar','96000','-ac','2'])]:
            target=out/name;run_decoder([caps['tools']['ffmpeg'],'-nostdin','-v','error','-n','-i',str(source),'-c:a',codec,*extra,str(target)]);cases.append(target)
    report={'status':'PASS_LOCAL_MEDIA_CONVERSION','decoder_capabilities':caps,'cases':[]}
    before=p.audio_compile()[0]
    for index,path in enumerate(cases):
        original=path.read_bytes();state=p.audio_state();review=p.audio_prepare_import(path,gain_db=-6,crossfade=128);assert p.audio_state()==state
        layer=LAYERS[index%4];p.audio_apply_import(review,layer);resources,detail=p.audio_compile();expected=detail['resource_path'] if layer=='engine' else detail[layer]['resource_path'];diff=[k for k in before if resources[k]!=before[k]];assert diff==[expected]
        assert path.read_bytes()==original;assert review['compiler']['output_format']['sample_rate']==48000;p.undo();assert p.audio_compile()[0]==before
        report['cases'].append({'file':str(path),'original_sha256':sha(original),'media':review['media'],'native_sha256':review['native_sha256'],'assigned_layer':layer,'only_changed_resource':expected,'preview_root':review['preview_root']})
    write_json(a.output/'codec-validation.json',report);return out/'lossless.flac' if caps['optional_media'] else source

def matrix(a):
    sources=json.loads(a.sources.read_text());base=resource_hashes(a.baseline_runtime/'resource-root');report={'status':'RUNNING','cases':{},'gameplay':'PENDING_OWNER'}
    for case,selected in zip('abcde',[(LAYERS[0],),(LAYERS[1],),(LAYERS[2],),(LAYERS[3],),LAYERS]):
        p=prepare(a,'project-'+case);before,detail=p.audio_compile();expected=[]
        for layer in selected:
            item=sources[layer];review=p.audio_prepare_import(item['wav'],gain_db=-6,use_source_loop=layer!='bov_release',source_evidence=item['evidence']);p.audio_apply_import(review,layer);expected.append(detail['resource_path'] if layer=='engine' else detail[layer]['resource_path'])
        p.audio_save_preset('GT import '+case.upper());p.build(a.output/case,sdk_root=ROOT,log=lambda s:print(case,s,flush=True));target=a.output/case/'candidate'
        current=resource_hashes(target/'runtime/resource-root');diff={k:{'before':base.get(k),'after':current.get(k)} for k in set(base)|set(current) if base.get(k)!=current.get(k)};assert set(diff)==set(expected),list(diff)
        assert (target/'runtime/native-patch-ops.rvp').read_bytes()==(a.baseline_runtime/'native-patch-ops.rvp').read_bytes(),'Source import changed native hook bytes'
        from validate_sdk_roster import validate
        write_json(a.output/case/'roster-validation.json',validate(json.loads((a.output/case/'roster.json').read_text()),target));p.audio_audition(ROOT.parent/'MRallye.exe',a.output/'auditions'/(case+'.wav'),rpms=[900,3500,6000,1800],seconds=.3)
        report['cases'][case]={'layers':selected,'resource_differences':diff,'native_patch_ops_unchanged':True,'project':str(p.root)};write_json(a.output/'matrix-validation.json',report)
    report['status']='PASS_FIVE_INDEPENDENT_GT_AUDIO_BUILDS';write_json(a.output/'matrix-validation.json',report)

def gui(a,media):
    from master_rallye.workshop.gui import WorkshopApp
    gt=WorkshopProject(a.gt_project);configs={k:v['config'] for k,v in gt.audio_state()['gt_sources'].items()};p=prepare(a,'gui-project');original=p.audio_compile()[0];models=resource_hashes(p.assets)
    root=tk.Tk();app=WorkshopApp(root,a.output/'workspace',ROOT,a.viewer);errors=[];report={'status':'RUNNING','captures':[],'gameplay':'PENDING_OWNER'}
    def capture(label,window=None):screenshot(window or app.root,a.output/(label+'.png'));report['captures'].append(label)
    def audio_tab():
        from tkinter import ttk
        next(w for w in app.audio_tab.master.winfo_children() if w==app.audio_tab) # Real tab exists.
        app.audio_tab.master.select(app.audio_tab);app.audio_loaded();root.update()
    def open_import():
        with patch('master_rallye.workshop.audio_ui.filedialog.askopenfilename',return_value=str(media)):app.audio_import2_dialog()
        app.audio_import2_window.prepare()
        app.audio_import2_window.fields['gain_db'].set('-4')
    def stale_rejected():
        d=app.audio_import2_window;assert d.report is None and 'Settings changed' in d.status.get();d.prepare()
    def reviewed(label):
        d=app.audio_import2_window;assert d.report,d.status.get();capture(label,d.window);d.listen('original-preview.wav');d.listen('converted.wav')
    def gain():app.audio_import2_window.fields['gain_db'].set('-9');assert app.audio_import2_window.report is None;app.audio_import2_window.prepare()
    def applied_ordinary():
        resources,detail=app.project.audio_compile();assert [k for k in original if resources[k]!=original[k]]==[detail['resource_path']];app.audio_preset.set('Ordinary local audio');app.audio_save_named()
    def gt_open():app.audio_gt_dialog()
    def configure(game):
        w=app.gt_sound_window;w.game.set(game);w.load_settings()
        for key,var in w.fields.items():var.set(configs[game].get(key,''))
        w.configure()
    def find():app.gt_sound_window.query.set('mits0015');app.gt_sound_window.find()
    def found():
        w=app.gt_sound_window;assert w.adapter.vehicle['sound_id']==22601 and len(w.adapter.vehicle['engine_rows_sharing_sound'])==11;capture('gt4-lancer-source',w.window);w.bank.set('carsound/engine/22601');w.inspect()
    def bands():
        w=app.gt_sound_window;assert len(w.inspection['entries'])==8;w.entries.selection_set('4');w.entry_selected();capture('gt4-eight-rpm-bands',w.window);w.bank.set('carsound/normal3/22601');w.inspect()
    def alternate():
        w=app.gt_sound_window;w.entries.selection_set('2');w.entry_selected();w.rate_mode.set('native');capture('gt4-alternate-tuning',w.window);w.export()
    def export_ready(layer):
        w=app.gt_sound_window;assert w.exported;app.audio_layer.set(layer);app.audio_loaded();w.use();d=app.audio_import2_window;d.layer.set(layer);d.fields['gain_db'].set('-6');d.loop.set(layer!='bov_release');d.prepare()
    def event(name,mode='nominal'):
        w=app.gt_sound_window;w.event.set(name);w.rate_mode.set(mode);w.event_inspect()
    def routed(label):
        w=app.gt_sound_window;assert w.route;capture(label,w.window);w.export()
    def preset():app.audio_preset.set('GT Audio Import 2.0');app.audio_save_named()
    def reopen():
        before=app.project.audio_state();app.project=WorkshopProject(p.root);assert app.project.audio_state()==before;app.audio_loaded();assert len([k for k,v in app.project.audio_compile()[0].items() if v!=original[k]])==4
        app.project.audio_reset();assert app.project.audio_compile()[0]==original;app.project.audio_load_preset('GT Audio Import 2.0');assert resource_hashes(app.project.assets)==models
        report['preset_persistence']=True;capture('four-layer-preset-reopened')
    def built():
        build=Path(app.project.data['last_build']);current=resource_hashes(build/'candidate/runtime/resource-root');base=resource_hashes(a.baseline_runtime/'resource-root');diff={k:{'before':base.get(k),'after':current.get(k)} for k in set(base)|set(current) if base.get(k)!=current.get(k)}
        assert len(diff)==4 and all(k.endswith('.wav') and '/lancer_evo4/' in k for k in diff),diff
        assert (build/'candidate/runtime/native-patch-ops.rvp').read_bytes()==(a.baseline_runtime/'native-patch-ops.rvp').read_bytes()
        report.update(status='PASS_WINDOWS_AUDIO_IMPORT2_GT_ADAPTER',build=str(build),resource_differences=diff,geometry_unchanged=True,native_hooks_unchanged=True,project=str(p.root));write_json(a.output/'windows-validation.json',report);app.gt_sound_window.close();app.close()
    steps=[lambda:app._opened(p),audio_tab,open_import,stale_rejected,lambda:reviewed('ordinary-original-converted'),gain,lambda:reviewed('ordinary-gain-changed'),lambda:app.audio_import2_window.accept(),applied_ordinary,gt_open,lambda:configure('gt4'),find,found,bands,alternate,
           lambda:export_ready('engine'),lambda:reviewed('gt4-engine-loop-converted'),lambda:app.audio_import2_window.accept(),lambda:event('turbine2'),lambda:routed('gt4-drivetrain-source'),lambda:export_ready('transmission_whine'),lambda:reviewed('gt4-whine-converted'),lambda:app.audio_import2_window.accept(),
           lambda:event('turbine'),lambda:routed('gt4-spool-source'),lambda:export_ready('turbo_spool'),lambda:reviewed('gt4-spool-converted'),lambda:app.audio_import2_window.accept(),lambda:configure('gt3'),lambda:event('b_off','native'),lambda:routed('gt3-bov-native-leaf'),lambda:export_ready('bov_release'),lambda:reviewed('gt3-bov-one-shot-converted'),lambda:app.audio_import2_window.accept(),preset,app.save,app.undo,app.redo,reopen,app.validate,app.build,built]
    index=0;idle=0;last=time.monotonic()
    def tick():
        nonlocal index,idle,last
        try:
            if errors:raise ValueError(errors)
            if time.monotonic()-last>480:raise TimeoutError('Import/GT GUI worker timeout')
            importing=getattr(app,'audio_import2_window',None);waiting=app.busy or (importing is not None and importing.window.winfo_exists() and importing.busy)
            if index==1 and app.project is None:waiting=True
            idle=0 if waiting else idle+1
            if idle>=3:print('GUI STEP',index,flush=True);steps[index]();index+=1;idle=0;last=time.monotonic()
            if index<len(steps):root.after(150,tick)
        except Exception as exc:
            import traceback
            report.update(status='FAIL',step=index,error=str(exc),traceback=traceback.format_exc());write_json(a.output/'windows-validation.json',report);root.destroy()
    root.report_callback_exception=lambda *args:errors.append(str(args))
    with patch('master_rallye.workshop.gui.messagebox.showerror',side_effect=lambda *args,**kw:errors.append(str(args))):root.after(300,tick);root.mainloop()
    if report['status']!='PASS_WINDOWS_AUDIO_IMPORT2_GT_ADAPTER':raise ValueError(report)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('reference','baseline-runtime','gt-project','sources','viewer','output'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--mode',choices=['all','gui','builds','codecs'],default='all');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    media=codecs(a) if a.mode in ('all','gui','codecs') else None
    if a.mode in ('all','builds'):matrix(a)
    if a.mode in ('all','gui'):gui(a,media)
if __name__=='__main__':main()
