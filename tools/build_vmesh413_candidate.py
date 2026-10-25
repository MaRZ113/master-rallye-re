"""V4.13 UI-style-only Subaru candidate from a frozen working baseline."""
import argparse,json,shutil,sys,zipfile,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from build_vmesh_impreza_experimental import Runner,dump,sha_file,ADDON_ID
from generate_vehicle_ui_previews import render_sources
from master_rallye.dxt import parse_dxt_bytes,encode_png
from master_rallye.addon_sdk.ui_assets import BANKS,archive_member
from master_rallye.vehicle_packaging import _open_sma_archive
from vmesh_ui_style import audit

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--before',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();before=a.before.resolve();out=a.output.resolve()
    if out.exists():raise ValueError('output exists')
    for name in ('project','dx','tex'):shutil.copytree(before/name,out/name)
    for name in ('reports','review','preview'):(out/name).mkdir()
    family=before/'runtime/resource-root/DataGx/Vehicles/ImprezaProto';render=render_sources(family,out/'render-sources')
    config=json.loads((out/'project/ui-assets.json').read_text())
    for role in BANKS:
        name=role+'.png';shutil.copyfile(out/'render-sources'/name,out/'project/ui'/name)
        config['icons'][role]={'png':'ui/'+name,'sha256':sha_file(out/'project/ui'/name),'presentation':'mr-native-v1'}
    dump(out/'project/ui-assets.json',config)
    spec=json.loads((out/'project/vehicle-project.json').read_text());donor=Path(spec['source_vehicle_dir']);retail=donor.parents[3]
    protected={str(path):sha_file(path) for path in (ROOT.parent/'MRallye.exe',ROOT.parent/'d3d8.dll')}
    run=Runner(out/'reports/commands.log');steps={};args=['--retail-data-sma',retail/'Data.sma','--retail-data-root',retail/'Data.sma_unpacked']
    steps['project_validate']=run.mrtool('addon','project-validate',out/'project',*args)
    steps['project_build']=run.mrtool('addon','project-build',out/'project',*args,'--output',out/'author-build')
    steps['author_verify']=run.mrtool('addon','verify',out/'author-build')
    common=['--manifest',ROOT/'research/vehicles/sdk/examples/mercedes-ml320.json','--manifest',out/'project/addon.json','--project-build',f'{ADDON_ID}={out/"author-build"}']
    steps['runtime_prepare']=run.mrtool('addon','runtime-prepare',*common,'--output',out/'runtime')
    steps['runtime_verify']=run.mrtool('addon','runtime-verify',out/'runtime',*common)
    steps['launcher_build']=run.mrtool('addon','runtime-launcher-build',out/'runtime',*common,'--launcher-output',out/'launcher')
    for flag in ('--verify','--verify-launch-environment'):
        proc=subprocess.run([str(out/'launcher/mr-runtime-launcher.exe'),flag,str(ROOT.parent/'MRallye.exe'),str(out/'runtime')],capture_output=True,text=True)
        if proc.returncode:raise ValueError(proc.stdout+proc.stderr)
        steps[flag]={'exit':0,'output':proc.stdout}
    with zipfile.ZipFile(before/'review'/(before.name+'-candidate.zip')) as z:
        prefix=before.name+'/runtime/resource-root/';base={n[len(prefix):]:z.read(n) for n in z.namelist() if n.startswith(prefix) and not n.endswith('/')}
    current=out/'runtime/resource-root';actual={p.relative_to(current).as_posix():p for p in current.rglob('*') if p.is_file()}
    # Some prior private ZIPs omit the prepared stock dependency. It remains
    # independently pinned by the prior runtime manifest/verified artifact.
    if 'Data.sma' not in base:
        with zipfile.ZipFile(before/'review'/(before.name+'-candidate.zip')) as z:
            prior_manifest=json.loads(z.read(before.name+'/runtime/resource-manifest.json'))
        pinned=next(r['sha256'] for r in prior_manifest['resources'] if r['path']=='Data.sma')
        if sha_file(current/'Data.sma')!=pinned:raise ValueError('prepared archive changed')
        base['Data.sma']=(current/'Data.sma').read_bytes()
    expected=sorted(prefix+f'_{count:03d}_000.dxt' for prefix,count,template,size in BANKS.values())
    if set(base)!=set(actual):raise ValueError('resource file set changed')
    changes=sorted(n for n in base if actual[n].read_bytes()!=base[n])
    if changes!=expected:raise ValueError('non-UI resource changed: '+str(changes))
    for path,h in protected.items():
        if sha_file(Path(path))!=h:raise ValueError('protected file changed')
    corpus=audit(retail/'Data.sma',out/'preview');dump(out/'reports/corpus-summary.json',corpus);dump(out/'reports/render.json',render)
    for role,(prefix,count,template,size) in BANKS.items():
        name=prefix+f'_{count:03d}_000.dxt';(out/'preview'/(role+'-after.png')).write_bytes(encode_png(parse_dxt_bytes(actual[name].read_bytes())))
        (out/'preview'/(role+'-before.png')).write_bytes(encode_png(parse_dxt_bytes(base[name])))
    html='<h1>V4.13 MR-style UI previews</h1><p>Offline approximation. Stock corpus ordered by zero-based frame, 8 per row.</p>'
    for role in BANKS:
        html+=f'<h2>{role}: before / after</h2><img width="256" style="image-rendering:pixelated" src="{role}-before.png"><img width="256" style="image-rendering:pixelated" src="{role}-after.png"><h3>Original MR corpus</h3><img src="{role}-stock-sheet.png">'
    (out/'preview/index.html').write_text(html,encoding='utf-8')
    dump(out/'reports/validation.json',{'status':'PASS_OFFLINE_RUNTIME_TEST_PENDING','steps':steps,'changed_resources':changes,'all_vehicle_assets_byte_identical':True,'protected':protected})
    handoff='''# V4.13 private UI-style candidate

Only the appended Vehicle Select / smallcarsheet images change from V4.12.
Vehicle geometry, wheels, tyres, physics, integration, banks and native patches
remain identical. Source images use separate offline model-render cameras and
mr-native-v1 role composition. Lighting is an authoring approximation.
No game was launched. Check both UI roles, transparency, normal selection and
race/Results presentation in game. GT3 extraction/custom PNG input stays optional.
'''
    (out/'HANDOFF.md').write_text(handoff)
    archive=out/'review'/(out.name+'-candidate.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for folder in ('runtime','launcher'):
            for path in sorted((out/folder).rglob('*')):
                if path.is_file():z.write(path,Path(out.name)/path.relative_to(out))
        z.writestr(out.name+'/HANDOFF.md',handoff)
    with zipfile.ZipFile(archive) as z:
        if z.testzip():raise ValueError('ZIP CRC failure')
    print(json.dumps({'candidate':str(archive),'sha256':sha_file(archive)},indent=2))

if __name__=='__main__':main()
