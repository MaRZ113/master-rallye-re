"""Package corrected material/normal metadata with the SAME validated DLL."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[3];PORT=ROOT/'ps2-research/pc-port';BASE=ROOT/'.research-output/atmosphere22'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    source=BASE/'candidate-runtime-001';out=BASE/'candidate-runtime-002'
    if out.exists():raise ValueError('fresh output required')
    old=json.loads((source/'manifest.json').read_text())
    for name,digest in old['files'].items():
        if sha(source/name)!=digest:raise ValueError('template changed '+name)
    shutil.copytree(source,out)
    runtime=out/'runtime-overlay';rollback=out/'rollback-metadata-001'
    for relative,folder,filename in [('Atmosphere21','materials-002','materials.lsm'),('Atmosphere22','normal-hints-002','normals.lnh')]:
        backup=rollback/relative;backup.mkdir(parents=True)
        shutil.copy2(runtime/relative/filename,backup/filename)
        shutil.copy2(BASE/folder/filename,runtime/relative/filename)
        prov='metadata-provenance.json' if relative=='Atmosphere21' else 'normals.lnh.provenance.json'
        shutil.copy2(runtime/relative/prov,backup/prov);shutil.copy2(BASE/folder/'provenance.json',runtime/relative/prov)
    if sha(runtime/'d3d8.dll')!='aaa845833237531e177fbfce621493002356a46d11b647bc7a87aa2ce2138640':raise ValueError('DLL identity')
    shutil.copy2(ROOT/'src/master_rallye/course_lighting.py',out/'sdk/src/master_rallye/course_lighting.py')
    shutil.copy2(out/'RUN_TEST_RU.md',out/'FULL_VALIDATION_RU.md')
    (out/'RUN_TEST_RU.md').write_text('''# Metadata-002: та же DLL aaa84583…

Полностью закрыть Atmo-copy. DLL, PS2Port.ini, трассы и PS2Vehicles не менять.
Из runtime-overlay заменить только четыре файла:
- Atmosphere21/materials.lsm и metadata-provenance.json;
- Atmosphere22/normals.lnh и normals.lnh.provenance.json.
Откат этих файлов — rollback-metadata-001. Полный откат ATM2.1 также сохранён.
Verify-Installation.ps1 проверяет всё с учётом новой версии metadata.

1. Seam-Debug.ini как Atmosphere.ini. France1 — та же проблемная скала:
   F10 + скриншот со светом; Ctrl+Alt+L без движения → F10 + скриншот без света.
   Закрыть игру. Проверяется восстановленный допуск rock/transition, не новая DLL.
2. Body-Debug.ini как Atmosphere.ini. Новый процесс, France1/Patrol:
   F10 + скриншот кузова (лучше вид сбоку/спереди). Restart → F10.
   Меню → выбрать Tata → France1 → F10 + скриншот кузова. Закрыть игру.
3. Написать «Сделал». Логи/скриншоты читаются из тех же известных папок.

Body-Debug включает новый свет кузова; Seam-Debug его намеренно отключает.
PS2-on/R4/VL1 и остальная матрица — следующий отдельный этап FULL_VALIDATION_RU.md.
Sun-Debug всё ещё suppression-only; видимого disk/halo/flare в этой версии нет.
''',encoding='utf-8')
    shutil.copy2(out/'REPORT_RU.md',out/'REPORT_INITIAL_RU.md')
    shutil.copy2(PORT/'docs/atmosphere22/RUNTIME_44172_RU.md',out/'REPORT_RU.md')
    shutil.copy2(PORT/'docs/atmosphere22/validation.json',out/'validation.json')
    for name in ['runtime-44172-evidence.json','metadata-002-diff.json','rock-screen-localization-44172.json']:shutil.copy2(BASE/name,out/name)
    shots=out/'comparison-screenshots';shots.mkdir()
    for name in ['MRallye_ETlYqeY1D8.jpg','MRallye_VGmbCOwlMm.jpg','MRallye_ikIkmkJtfR.jpg','MRallye_27Do4YXFWF.jpg']:
        shutil.copy2(Path('C:/Users/MaRZ/Documents/ShareX/Screenshots/2026-11')/name,shots/name)
    archive=out/'source-changes.zip'
    with zipfile.ZipFile(archive) as z:entries={n:z.read(n) for n in z.namelist()}
    for f in [ROOT/'src/master_rallye/course_lighting.py',ROOT/'tests/test_course_lighting_orientation.py',Path(__file__)]:entries[f.relative_to(ROOT).as_posix()]=f.read_bytes()
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in entries.items():z.writestr(name,data)
    old.update(status='PARTIAL_RUNTIME_VERIFIED_METADATA_002_PENDING',metadata_version='002',dll_unchanged=True,
               material_metadata_sha256=sha(runtime/'Atmosphere21/materials.lsm'),normal_hints_sha256=sha(runtime/'Atmosphere22/normals.lnh'),
               runtime_evidence='PID44172 tested initial metadata only; metadata-002 and body pending')
    old['files']={p.relative_to(out).as_posix():sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p!=out/'manifest.json'}
    (out/'manifest.json').write_text(json.dumps(old,indent=2)+'\n');print(str(out));print(old['dll_sha256'])

if __name__=='__main__':main()
