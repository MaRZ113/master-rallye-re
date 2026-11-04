"""One reversible ATMOSPHERE2.2 candidate; never deploys into a game root."""
import argparse
import configparser
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

PORT=Path(__file__).resolve().parents[1];ROOT=PORT.parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
    if out.exists():raise ValueError('fresh output required')
    report=json.loads((PORT/'dist/current/build-report.json').read_text())
    for path,digest in report['ps2_source_sha256'].items():
        if sha(PORT/path)!=digest:raise ValueError('stale source '+path)
    for path,digest in report['patch_sha256'].items():
        if sha(PORT/'overlay/patches'/path)!=digest:raise ValueError('stale patch '+path)
    dll=PORT/'dist/current/ps2-enabled/d3d8.dll'
    if sha(dll)!=report['builds']['ps2-enabled']['dll_sha256']:raise ValueError('stale DLL')
    old=ROOT/'.research-output/atmosphere21/candidate-runtime-001'
    if sha(old/'runtime-overlay/d3d8.dll')!='40e630dbee5163fbeea89de626cdee4e8b9b35a30d3d36b6961bd6c1cdd00885':raise ValueError('rollback identity')
    out.mkdir(parents=True);runtime=out/'runtime-overlay';shutil.copytree(old/'runtime-overlay',runtime);shutil.copy2(dll,runtime/'d3d8.dll')
    metadata=runtime/'Atmosphere22';metadata.mkdir()
    for folder,filename in [('normal-hints-pc-ps2','normals.lnh'),('body-materials','body.blm')]:
        source=ROOT/'.research-output/atmosphere22'/folder;provenance=json.loads((source/'provenance.json').read_text())
        if sha(source/filename)!=provenance['sha256']:raise ValueError('metadata drift')
        shutil.copy2(source/filename,metadata/filename);shutil.copy2(source/'provenance.json',metadata/(filename+'.provenance.json'))
    profiles=out/'profiles';profiles.mkdir();config=configparser.ConfigParser();config.optionxform=str;config.read(old/'profiles/golden-hour.ini')
    common=dict(config['Atmosphere'])|{'BodyPrototype':'Materials','NormalHints':'Atmosphere22/normals.lnh','BodyMaterials':'Atmosphere22/body.blm',
        'WorldBrightness':'0.68','Exposure':'1.0','AmbientStrength':'0.95','AmbientR':'0.67','AmbientG':'0.74','AmbientB':'0.90',
        'SunlightStrength':'0.58','SunlightR':'1.25','SunlightG':'0.86','SunlightB':'0.45','SeamDebug':'0','BodyDebug':'0'}
    def profile(name,changes):
        (profiles/name).write_text('; ATMOSPHERE2.2 private candidate; read at process start.\n[Atmosphere]\n'+''.join(f'{k}={v}\n' for k,v in (common|changes).items()),encoding='utf-8')
    profile('GoldenHour.ini',{})
    profile('Original.ini',{'WorldLighting':'0','LightingPreset':'Original','BodyPrototype':'Off','FogEnabled':'0','CustomSet':'','CustomSkyUScale':'1'})
    profile('Seam-Debug.ini',{'SeamDebug':'1','BodyPrototype':'Off'})
    profile('Body-Debug.ini',{'BodyDebug':'1'})
    profile('Sun-Debug.ini',{'SunDisk':'1','SunHalo':'1','SunFlare':'0'})
    profile('GoldenHour-WorldOnly.ini',{'BodyPrototype':'Off'})
    profile('Seam-Geometric-Debug.ini',{'SeamDebug':'1','BodyPrototype':'Off','NormalHints':'Atmosphere22/absent.lnh'})
    shutil.copy2(profiles/'Original.ini',runtime/'Atmosphere.ini')
    for name in ['PS2Port-baseline.ini','PS2Port-accepted-compat.ini']:shutil.copy2(old/'profiles'/name,profiles/name)
    shutil.copytree(old/'runtime-overlay',out/'rollback-atmosphere21')
    shutil.copytree(old/'modified-render-configuration',out/'modified-render-configuration')
    shutil.copy2(old/'Verify-Installation.ps1',out/'Verify-Installation.ps1')
    sdk=out/'sdk';shutil.copytree(old/'sdk',sdk,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    for name in ['atmosphere_normal_hints.py','atmosphere_body_metadata.py']:
        script=(PORT/'tools'/name).read_text().replace("Path(__file__).resolve().parents[3]/'src'","Path(__file__).resolve().parent/'src'")
        (sdk/name).write_text(script,encoding='utf-8')
    shutil.copy2(ROOT/'.research-output/atmosphere22/body-selection.json',sdk/'body-selection.json')
    for name in ['previous-runtime-evidence.json','offline-seam-evidence.json','metadata-checks.json']:
        shutil.copy2(ROOT/'.research-output/atmosphere22'/name,out/name)
    for name in ['RUN_TEST_RU.md','REPORT_RU.md','SDK_RU.md','validation.json']:shutil.copy2(PORT/'docs/atmosphere22'/name,out/name)
    shutil.copy2(PORT/'dist/current/build-report.json',out/'build-report.json')
    with zipfile.ZipFile(out/'source-changes.zip','w',zipfile.ZIP_DEFLATED) as z:
        sources=list((PORT/'renderer').glob('atmosphere*.hpp'))+[PORT/'renderer/scene_resolver.hpp',PORT/'renderer/race_car_fleet_native.hpp',PORT/'renderer/ps2_port_extension.cpp',PORT/'tests/atmosphere_tests.cpp',PORT/'overlay/patches/0001-renderer-integration.patch',PORT/'overlay/baseline-lock.json']+list((PORT/'tools').glob('*atmosphere22*.py'))+[PORT/'tools/atmosphere_normal_hints.py',PORT/'tools/atmosphere_body_metadata.py']
        for source in sources:z.write(source,source.relative_to(ROOT).as_posix())
    manifest={'status':'OFFLINE_VALIDATED_RUNTIME_PENDING','dll_sha256':sha(dll),'baseline_dll_sha256':report['builds']['baseline']['dll_sha256'],
              'normal_hints_sha256':sha(metadata/'normals.lnh'),'body_metadata_sha256':sha(metadata/'body.blm'),
              'sun':'SUPPRESSED_PENDING_WORLD_BODY_STABILITY_AND_CURRENT_FRAME_OCCLUSION_PROOF','runtime_installation':'USER_MANUAL_ONLY',
              'files':{f.relative_to(out).as_posix():sha(f) for f in sorted(out.rglob('*')) if f.is_file()}}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(str(out)+'\n'+sha(dll))

if __name__=='__main__':main()
