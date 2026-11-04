"""Package the BL1 first-load candidate. Runtime acceptance is recorded separately; never deploys."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil

PORT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    report_path=PORT/'dist/current/build-report.json';report=json.loads(report_path.read_text())
    for name,digest in report['ps2_source_sha256'].items():
        if sha(PORT/name)!=digest:raise ValueError(f'stale source: {name}')
    for name,digest in report['patch_sha256'].items():
        if sha(PORT/'overlay/patches'/name)!=digest:raise ValueError(f'stale patch: {name}')
    dll=PORT/'.build/ps2-enabled/Release/d3d8.dll'
    if sha(dll)!=report['builds']['ps2-enabled']['dll_sha256']:raise ValueError('DLL differs from build report')
    out=a.output.resolve()
    if out.exists():raise ValueError('new output directory required')
    out.mkdir(parents=True)
    shutil.copy2(dll,out/'d3d8.dll');shutil.copy2(report_path,out/'build-report.json')
    stock=(PORT/'Atmosphere.ini').read_text();enabled=stock.replace('Enabled=0','Enabled=1')
    (out/'Atmosphere.ini').write_text(enabled.replace('SkyPreset=Auto','SkyPreset=3'))
    profiles=out/'profiles';profiles.mkdir()
    for preset in (0,3,5):(profiles/f'sky-{preset}.ini').write_text(enabled.replace('SkyPreset=Auto',f'SkyPreset={preset}'))
    (profiles/'auto.ini').write_text(enabled);(profiles/'disabled.ini').write_text(stock)
    (out/'PS2Port-baseline.ini').write_text('''; Diagnostic graphics baseline; save your existing PS2Port.ini before using.
[PS2Port]
Diagnostics=1
RaceLedger=1
Reflection=0
ReflectionCoverage=0
PS2UniformReflection=0
VehicleLighting=0
RaceFleet=0
FrontendModel=0
BrakeGlow=0
Foliage=0
Grass=0
Shrubs=0
CourseObjects=0
GroundDetail=0
PS2Color=0
PS2Output=0
PS2MotionBlur=0
PS2ContentFixes=0
PS2Water=0
RigidProps=0
CollisionDebug=0
''')
    (out/'RUN_TEST_RU.md').write_text('''# BL1: кандидат исправления первой загрузки — RUNTIME_PENDING

1. Полностью закройте игру. В тестовой Atmo-copy сохраните текущие d3d8.dll,
   Atmosphere.ini и PS2Port.ini в отдельную резервную папку.
2. Скопируйте сюда d3d8.dll и Atmosphere.ini из этого пакета. Для чистого
   графического Baseline скопируйте PS2Port-baseline.ini как PS2Port.ini.
   MRRRenderer.ini, dinput8.dll, EXE, архивы и сохранения не менять.
3. Запустите игру новым процессом. France1, тот же автомобиль и камера.
   На ПЕРВОЙ гонке: F10 и скриншот. Ничего не перезагружать до этого захвата.
4. Restart только гонки: F10 и скриншот в той же точке. Затем выйти в меню,
   снова загрузить France1: ещё F10/скриншот. Полностью закрыть игру.
5. Нужны новые session-*.jsonl, frame-*.jsonl и ps2diag-*.jsonl из MRRRenderer/logs.
   Первая новая atmosphere_sky_selection должна показать effective=3 и
   native_null_false_source_with_typed_local_context (либо typed source),
   или точный отказ. atmosphere_sky_draw покажет фактический
   preset/слой и serial. atmosphere_world_fog покажет реальный цвет world pass.

Проверка SkyPreset=0 и 5 отдельными холодными процессами — после разбора основного
кейса 3. profiles/auto.ini и disabled.ini — отдельные контроли, не способ обхода.
CustomSet пуст, WorldLighting/LightProbe/Sun/SunFlare выключены.
PS2-графика включается только позднее, после квалификации первого sky init.

Ранний допуск требует исходный FrontEnd/Network/Browse=false (bool либо точное
нативное null: matching key id, payload=0, tag=12), NumPlayers=1,
NumNetworkPlayers=0, Type=1/2, PlaybackReplay=false и текущий native sky init
в RaceTest job на потоке observer. SyncActive должен быть опубликованным false
либо точно соответствовать пустому native Broker slot (id=0,payload=0,tag=12).
Отсутствие/прочие типы upstream, активная сеть, неизвестный контекст отклоняются.
Native null отдельно проверен по оригинальному bool-getter 0x4D6610..0x4D6627
и PID39180: игра сохраняет Browse tag12 даже после публикации Sync=false.
Нет fog-only подмены, записи в Broker или дополнительной загрузки sky.
Если первый sky опять Cloud0, сохранить логи: runtime fix ещё не подтверждён.

Откат: вернуть сохранённые три файла. Этот упаковщик ничего не устанавливает.
''',encoding='utf-8')
    manifest={'status':'BL1_FIRST_LOAD_CANDIDATE_RUNTIME_PENDING','source_head':report['current_head'],
        'files':{p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file()}}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'First-load candidate package: {out}; DLL {sha(dll)}')
if __name__=='__main__':main()
