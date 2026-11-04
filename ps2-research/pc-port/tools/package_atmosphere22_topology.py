"""ATMOSPHERE2.2 paired-topology and opaque-panel candidate; no game installation."""
import hashlib,json,shutil,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];PORT=ROOT/'ps2-research/pc-port';BASE=ROOT/'.research-output/atmosphere22'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    old=BASE/'candidate-runtime-004';out=BASE/'candidate-runtime-005'
    if out.exists():raise ValueError('fresh output required')
    build=json.loads((PORT/'dist/current/build-report.json').read_text())
    for p,h in build['ps2_source_sha256'].items():
        if sha(PORT/p)!=h:raise ValueError('stale source '+p)
    for p,h in build['patch_sha256'].items():
        if sha(PORT/'overlay/patches'/p)!=h:raise ValueError('stale patch '+p)
    for p,h in json.loads((old/'manifest.json').read_text())['files'].items():
        if sha(old/p)!=h:raise ValueError('old package changed '+p)
    for name in ['runtime-overlay','profiles','sdk','modified-render-configuration']:shutil.copytree(old/name,out/name)
    shutil.copytree(old/'runtime-overlay',out/'rollback-runtime-004')
    runtime=out/'runtime-overlay';shutil.copy2(PORT/'dist/current/ps2-enabled/d3d8.dll',runtime/'d3d8.dll')
    shutil.copy2(BASE/'body-materials-005/body.blm',runtime/'Atmosphere22/body.blm')
    shutil.copy2(BASE/'body-materials-005/provenance.json',runtime/'Atmosphere22/body.blm.provenance.json')
    for p in (out/'profiles').glob('*.ini'):
        if p.name.startswith('PS2Port'):continue
        s=p.read_text().replace('PrelightContrast=0.35','PrelightContrast=1\nPrelightVisibility=0')
        p.write_text(s,encoding='utf-8')
    shutil.copy2(out/'profiles/Original.ini',runtime/'Atmosphere.ini')
    shutil.copy2(old/'Verify-Installation.ps1',out/'Verify-Installation.ps1')
    for name in ['REPORT','RUN_TEST','SDK','FULL_VALIDATION']:
        shutil.copy2(PORT/'docs/atmosphere22'/(name+'_005_RU.md'),out/(name+'_RU.md'))
    shutil.copy2(BASE/'runtime-004-evidence.json',out/'runtime-004-evidence.json')
    shutil.copy2(BASE/'body-selection-005.json',out/'sdk/body-selection.json')
    s=(PORT/'tools/atmosphere_body_metadata.py').read_text();(out/'sdk/atmosphere_body_metadata.py').write_text(s,encoding='utf-8')
    shutil.copy2(PORT/'dist/current/build-report.json',out/'build-report.json')
    evidence=out/'topology-evidence';evidence.mkdir()
    for name in ['probe.cpp','generate.py','CMakeLists.txt','result.json','sources.json']:shutil.copy2(BASE/'topology-replay-005'/name,evidence/name)
    screens=out/'comparison-screenshots';screens.mkdir()
    for item in json.loads((BASE/'runtime-004-evidence.json').read_text())['screenshots']:shutil.copy2(Path(item['path']),screens/Path(item['path']).name)
    with zipfile.ZipFile(old/'source-changes.zip') as z:entries={n:z.read(n) for n in z.namelist()}
    paths=list((PORT/'renderer').glob('atmosphere*.hpp'))+[PORT/'renderer/scene_resolver.hpp',PORT/'renderer/race_car_fleet_native.hpp',PORT/'tests/atmosphere_tests.cpp',PORT/'tools/atmosphere_body_metadata.py',Path(__file__).resolve()]
    for p in paths:entries[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    with zipfile.ZipFile(out/'source-changes.zip','w',zipfile.ZIP_DEFLATED) as z:
        for n,b in sorted(entries.items()):z.writestr(n,b)
    validation=json.loads((PORT/'docs/atmosphere22/validation-005.json').read_text());validation['dll_sha256']=sha(runtime/'d3d8.dll')
    (out/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    m={'status':'OFFLINE_VERIFIED_005_RUNTIME_PENDING','dll_sha256':sha(runtime/'d3d8.dll'),'baseline_dll_sha256':build['builds']['baseline']['dll_sha256'],'runtime_installation':'USER_MANUAL_ONLY','files':{p.relative_to(out).as_posix():sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p!=out/'manifest.json'}}
    (out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(out);print(m['dll_sha256'])
if __name__=='__main__':main()
