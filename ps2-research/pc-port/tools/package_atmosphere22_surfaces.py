"""One reversible typed-body/signage candidate; never installs into a game."""
import hashlib,json,shutil,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];PORT=ROOT/'ps2-research/pc-port';BASE=ROOT/'.research-output/atmosphere22'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    out=BASE/'candidate-runtime-003';old=BASE/'candidate-runtime-002'
    if out.exists():raise ValueError('fresh output required')
    report=json.loads((PORT/'dist/current/build-report.json').read_text())
    for p,h in report['ps2_source_sha256'].items():
        if sha(PORT/p)!=h:raise ValueError('stale source '+p)
    for p,h in report['patch_sha256'].items():
        if sha(PORT/'overlay/patches'/p)!=h:raise ValueError('stale patch '+p)
    old_manifest=json.loads((old/'manifest.json').read_text())
    for p,h in old_manifest['files'].items():
        if sha(old/p)!=h:raise ValueError('template changed '+p)
    shutil.copytree(old,out);runtime=out/'runtime-overlay'
    shutil.copytree(old/'runtime-overlay',out/'rollback-runtime-002')
    shutil.copy2(PORT/'dist/current/ps2-enabled/d3d8.dll',runtime/'d3d8.dll')
    for folder,name,target in [('materials-003','materials.lsm','Atmosphere21'),('normal-hints-003','normals.lnh','Atmosphere22'),('body-materials-003','body.blm','Atmosphere22')]:
        shutil.copy2(BASE/folder/name,runtime/target/name)
        prov='metadata-provenance.json' if name=='materials.lsm' else name+'.provenance.json'
        shutil.copy2(BASE/folder/'provenance.json',runtime/target/prov)
    shutil.copy2(ROOT/'src/master_rallye/course_lighting.py',out/'sdk/src/master_rallye/course_lighting.py')
    for name in ['atmosphere_body_metadata.py','atmosphere_lighting_metadata.py']:
        script=(PORT/'tools'/name).read_text().replace("Path(__file__).resolve().parents[3]/'src'","Path(__file__).resolve().parent/'src'")
        target='export_lighting.py' if name=='atmosphere_lighting_metadata.py' else name;(out/'sdk'/target).write_text(script,encoding='utf-8')
    shutil.copy2(BASE/'signage-roles.json',out/'sdk/signage-roles.json');shutil.copy2(BASE/'body-selection-003.json',out/'sdk/body-selection.json')
    p=out/'profiles/Body-Debug.ini';s=p.read_text().replace('SeamDebug=0','SeamDebug=1');(out/'profiles/Surfaces-Debug.ini').write_text(s)
    shutil.copy2(out/'REPORT_RU.md',out/'REPORT_METADATA_002_RU.md');shutil.copy2(PORT/'docs/atmosphere22/RUNTIME_BODY_SIGNAGE_RU.md',out/'REPORT_RU.md')
    (out/'RUN_TEST_RU.md').write_text('''# Candidate-runtime-003 — body surfaces + signage

Нужна НОВАЯ DLL из этого пакета (5b219cc7…). Полностью закрыть игру, сохранить
текущие DLL/INI, скопировать содержимое runtime-overlay в Atmo-copy.
Важны все Atmosphere21/Atmosphere22 файлы: body.blm теперь BLM2, старой DLL
aaa84583… для него недостаточно. Проверить Verify-Installation.ps1.
Прежний работающий состав — rollback-runtime-002. Original по умолчанию.

1. profiles/Surfaces-Debug.ini как Atmosphere.ini. Новый процесс France1/Patrol:
   F10+скриншот сбоку, чтобы видеть расширители крыльев и баннер. Ctrl+Alt+L →
   F10+скриншот с той же камерой: меняется свет мира/баннера, кузов остаётся lit.
   Вернуть Ctrl+Alt+L. Меню → Tata/France1: F10+скриншот сбоку (пластик),
   Restart → F10. Закрыть. Не использовать Seam-Debug для проверки кузова.
2. Отдельная PS2-on проверка: сохранить текущий PS2Port.ini и скопировать
   profiles/PS2Port-accepted-compat.ini как PS2Port.ini. Сохранить Reflection=4,
   VehicleLighting=1 и прежнюю ориентацию, PS2Vehicles не менять. Body-Debug.ini.
   Новый France1/Patrol F10+скриншот → Restart/F10 → меню/Tata/France1/F10+
   скриншот → меню/Turkey2/F10 → меню/Turkey3/F10 → закрыть.
3. Для отдельных loose PS2 трасс каталог должен называться DataGx/Course,
   сейчас он был переименован пользователем в Course1. Renderer PS2-on и loose
   PS2 course — разные условия. Записать, какое расположение использовано;
   для полной матрицы повторить проход на loose PS2, сохраняя оригинальные DX.

Написать «Сделал». Колёса/шины/диски, lamp/glass/sticker passes намеренно native.
Дополнительные кузовные поверхности и баннеры пока только OFFLINE_VERIFIED.
Full Reset/FreeCam/HUD/water/physics/collision/standalone/FPS/edited-layout
матрица остаётся отдельной FULL_VALIDATION_RU.md. Sun по-прежнему suppression-only.
''',encoding='utf-8')
    for name in ['runtime-35932-11964-evidence.json','metadata-003-diff.json']:shutil.copy2(BASE/name,out/name)
    for name in ['MRallye_tlAUQT9MuA.jpg','MRallye_rMaRM33S32.jpg','MRallye_9SzPiRRw1X.jpg','MRallye_QusIlH2jOx.jpg','MRallye_8Ej5JjxqP6.jpg','MRallye_h1xfA0ENRT.jpg']:
        shutil.copy2(Path('C:/Users/MaRZ/Documents/ShareX/Screenshots/2026-11')/name,out/'comparison-screenshots'/name)
    shutil.copy2(PORT/'dist/current/build-report.json',out/'build-report.json')
    with zipfile.ZipFile(out/'source-changes.zip') as z:entries={n:z.read(n) for n in z.namelist()}
    files=list((PORT/'renderer').glob('atmosphere*.hpp'))+[PORT/'tests/atmosphere_tests.cpp',PORT/'tools/atmosphere_body_metadata.py',ROOT/'src/master_rallye/course_lighting.py',ROOT/'tests/test_course_lighting_orientation.py',Path(__file__)]
    for p in files:entries[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    with zipfile.ZipFile(out/'source-changes.zip','w',zipfile.ZIP_DEFLATED) as z:
        for n,b in entries.items():z.writestr(n,b)
    m={'status':'PREVIOUS_BODY_RUNTIME_CONFIRMED_NEW_SURFACES_PENDING','dll_sha256':sha(runtime/'d3d8.dll'),
       'baseline_dll_sha256':report['builds']['baseline']['dll_sha256'],'metadata_version':'003','body_metadata_format':'BLM2',
       'runtime_installation':'USER_MANUAL_ONLY','new_surface_runtime':'PENDING','sun':'SUPPRESSED',
       'files':{p.relative_to(out).as_posix():sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p!=out/'manifest.json'}}
    (out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(str(out));print(m['dll_sha256'])

if __name__=='__main__':main()
