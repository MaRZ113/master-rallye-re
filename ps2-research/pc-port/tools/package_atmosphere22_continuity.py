"""Reversible ATMOSPHERE2.2 continuity candidate, never deploys into a game."""
import hashlib,json,shutil,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];PORT=ROOT/'ps2-research/pc-port';BASE=ROOT/'.research-output/atmosphere22'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    old=BASE/'candidate-runtime-003';out=BASE/'candidate-runtime-004'
    if out.exists():raise ValueError('fresh output required')
    build=json.loads((PORT/'dist/current/build-report.json').read_text())
    for p,h in build['ps2_source_sha256'].items():
        if sha(PORT/p)!=h:raise ValueError('stale source '+p)
    for p,h in build['patch_sha256'].items():
        if sha(PORT/'overlay/patches'/p)!=h:raise ValueError('stale patch '+p)
    for p,h in json.loads((old/'manifest.json').read_text())['files'].items():
        if sha(old/p)!=h:raise ValueError('previous candidate changed '+p)
    for name in ['runtime-overlay','profiles','sdk','modified-render-configuration']:shutil.copytree(old/name,out/name)
    shutil.copytree(old/'runtime-overlay',out/'rollback-runtime-003')
    runtime=out/'runtime-overlay';shutil.copy2(PORT/'dist/current/ps2-enabled/d3d8.dll',runtime/'d3d8.dll')
    for folder,name,target in [('materials-004b','materials.lsm','Atmosphere21'),('normal-hints-004c','normals.lnh','Atmosphere22'),('body-materials-004','body.blm','Atmosphere22')]:
        shutil.copy2(BASE/folder/name,runtime/target/name)
        prov='metadata-provenance.json' if name=='materials.lsm' else name+'.provenance.json'
        shutil.copy2(BASE/folder/'provenance.json',runtime/target/prov)
    for p in (out/'profiles').glob('*.ini'):
        if p.name.startswith('PS2Port'):continue
        s=p.read_text().replace('Exposure=1.0','Exposure=1.0\nPrelightContrast=0.35')
        p.write_text(s,encoding='utf-8')
    shutil.copy2(out/'profiles/Original.ini',runtime/'Atmosphere.ini')
    shutil.copy2(old/'Verify-Installation.ps1',out/'Verify-Installation.ps1')
    shutil.copy2(PORT/'docs/atmosphere22/FULL_VALIDATION_004_RU.md',out/'FULL_VALIDATION_RU.md')
    shutil.copy2(ROOT/'src/master_rallye/course_lighting.py',out/'sdk/src/master_rallye/course_lighting.py')
    for name in ['atmosphere_body_metadata.py','atmosphere_normal_hints.py','atmosphere_lighting_metadata.py']:
        s=(PORT/'tools'/name).read_text().replace("Path(__file__).resolve().parents[3]/'src'","Path(__file__).resolve().parent/'src'")
        (out/'sdk'/('export_lighting.py' if name=='atmosphere_lighting_metadata.py' else name)).write_text(s,encoding='utf-8')
    shutil.copy2(BASE/'body-selection-004.json',out/'sdk/body-selection.json')
    for name in ['runtime-003-evidence.json']:shutil.copy2(BASE/name,out/name)
    shutil.copy2(BASE/'body-exposure-probe/result.json',out/'isolated-d3d8-exposure.json')
    for name in ['REPORT_004_RU.md','RUN_TEST_004_RU.md','SDK_004_RU.md','validation-004.json']:
        shutil.copy2(PORT/'docs/atmosphere22'/name,out/name.replace('_004','').replace('-004',''))
    (out/'comparison-screenshots').mkdir()
    for name in ['MRallye_Xi3tv9n4gp.jpg','MRallye_MOuNefYYmS.jpg','MRallye_ZNEE4X7Oug.jpg','MRallye_PWkztvNEiR.jpg','MRallye_ZwynKAbcJf.jpg','MRallye_oOlCf4KhPJ.jpg']:
        shutil.copy2(Path('C:/Users/MaRZ/Documents/ShareX/Screenshots/2026-11')/name,out/'comparison-screenshots'/name)
    shutil.copy2(PORT/'dist/current/build-report.json',out/'build-report.json')
    with zipfile.ZipFile(old/'source-changes.zip') as z:entries={n:z.read(n) for n in z.namelist()}
    paths=list((PORT/'renderer').glob('atmosphere*.hpp'))+[PORT/'renderer/scene_resolver.hpp',PORT/'renderer/race_car_fleet_native.hpp',PORT/'tests/atmosphere_tests.cpp',ROOT/'src/master_rallye/course_lighting.py',ROOT/'tests/test_course_lighting_orientation.py',Path(__file__)]
    paths+=list((PORT/'tools').glob('atmosphere*metadata.py'))+[PORT/'tools/atmosphere_normal_hints.py']
    for p in paths:entries[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    with zipfile.ZipFile(out/'source-changes.zip','w',zipfile.ZIP_DEFLATED) as z:
        for n,b in sorted(entries.items()):z.writestr(n,b)
    validation=json.loads((out/'validation.json').read_text());validation['dll_sha256']=sha(runtime/'d3d8.dll')
    (out/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    m={'status':'OFFLINE_VERIFIED_004_RUNTIME_PENDING','dll_sha256':sha(runtime/'d3d8.dll'),'baseline_dll_sha256':build['builds']['baseline']['dll_sha256'],'runtime_installation':'USER_MANUAL_ONLY','files':{p.relative_to(out).as_posix():sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p!=out/'manifest.json'}}
    (out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(out);print(m['dll_sha256'])
if __name__=='__main__':main()
