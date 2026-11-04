"""Private ATMOSPHERE2.1 package, independent metadata and reversible comparisons.

Creates a fresh candidate directory only. Does not deploy or launch the game.
"""
import argparse
import configparser
import hashlib
import json
from pathlib import Path
import shutil
import struct

PORT=Path(__file__).resolve().parents[1]
ROOT=PORT.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ['metadata','sky','variant','output']:ap.add_argument('--'+name,type=Path,required=True)
    a=ap.parse_args();out=a.output.resolve()
    if out.exists():raise ValueError('fresh output required')
    report=json.loads((PORT/'dist/current/build-report.json').read_text())
    for path,digest in report['ps2_source_sha256'].items():
        if sha(PORT/path)!=digest:raise ValueError('stale build source '+path)
    for path,digest in report['patch_sha256'].items():
        if sha(PORT/'overlay/patches'/path)!=digest:raise ValueError('stale build patch '+path)
    dll=PORT/'dist/current/ps2-enabled/d3d8.dll'
    if sha(dll)!=report['builds']['ps2-enabled']['dll_sha256']:raise ValueError('stale DLL')
    meta=json.loads((a.metadata/'provenance.json').read_text());data=(a.metadata/'materials.lsm').read_bytes()
    if sha(a.metadata/'materials.lsm')!=meta['metadata_sha256'] or data[12:76]!=hashlib.sha256(data[76:]).hexdigest().encode():raise ValueError('metadata integrity')
    sky=json.loads((a.sky/'provenance.json').read_text());variant=json.loads((a.variant/'provenance.json').read_text())
    variant_file=a.variant/'DataGx/Course/France1/france1.dx'
    if sha(variant_file)!=variant['variant_sha256']:raise ValueError('variant integrity')
    out.mkdir(parents=True);runtime=out/'runtime-overlay';runtime.mkdir();shutil.copy2(dll,runtime/'d3d8.dll')
    materials=runtime/'Atmosphere21';materials.mkdir();shutil.copy2(a.metadata/'materials.lsm',materials/'materials.lsm');shutil.copy2(a.metadata/'provenance.json',materials/'metadata-provenance.json')
    (materials/'empty.lsm').write_bytes(struct.pack('<4sII',b'LSM1',1,0)+hashlib.sha256(b'').hexdigest().encode())
    sets=runtime/'Atmosphere2/sets'
    for course in sky['courses']:
        dest=sets/course['course'];dest.mkdir(parents=True)
        for item in course['resources']:
            source=a.sky/'sets'/course['course']/(item['name']+'.dxt')
            if sha(source)!=item['sha256']:raise ValueError('sky asset drift')
            shutil.copy2(source,dest/source.name)
    profiles=out/'profiles';profiles.mkdir()
    common={'Enabled':'1','SkyPreset':'3','WorldLighting':'1','SceneResolver':'Universal','AutoGround':'1','LightingMetadata':'Atmosphere21/materials.lsm',
            'LightingPreset':'GoldenHour','LightingStrength':'1','WorldBrightness':'0.72','Exposure':'1.05','AmbientStrength':'0.60',
            'AmbientR':'0.60','AmbientG':'0.70','AmbientB':'0.94','SunlightStrength':'1.10','SunlightR':'1.50','SunlightG':'1.00','SunlightB':'0.55',
            'SunDirX':'-0.65','SunDirY':'0.45','SunDirZ':'0.61','FogEnabled':'1','FogStrength':'1','FogColor':'0x98765d',
            'CustomSet':'Atmosphere2/sets/r_deepforest','CustomBase':'3','CustomSkyUScale':'0.5','BodyPrototype':'Off','LightProbe':'0',
            'Sun':'0','SunDisk':'0','SunHalo':'0','SunFlare':'0','SceneDiagnostics':'0'}
    def profile(name,changes):
        values=common|changes
        (profiles/name).write_text('; ATMOSPHERE2.1 private candidate. Read at process start; no Extra Options dependency.\n[Atmosphere]\n'+''.join(f'{k}={v}\n' for k,v in values.items()),encoding='utf-8')
    profile('golden-hour.ini',{})
    profile('golden-hour-darker.ini',{'WorldBrightness':'0.58'})
    profile('grand-valley.ini',{'CustomSet':'Atmosphere2/sets/r_grandvalley','FogColor':'0x675b68'})
    profile('original.ini',{'WorldLighting':'0','LightingPreset':'Original','WorldBrightness':'1','CustomSet':'','CustomSkyUScale':'1','FogEnabled':'0'})
    profile('day.ini',{'CustomSet':'','CustomSkyUScale':'1','LightingPreset':'Day','WorldBrightness':'1','Exposure':'1','AmbientStrength':'1','AmbientR':'0.9','AmbientG':'0.94','AmbientB':'1','SunlightStrength':'0.35','SunlightR':'0.3','SunlightG':'0.28','SunlightB':'0.24','FogEnabled':'0'})
    profile('sky-only.ini',{'WorldLighting':'0'})
    profile('world-only.ini',{'CustomSet':'','CustomSkyUScale':'1'})
    profile('resolver-comparison.ini',{'WorldBrightness':'1','AmbientStrength':'0.8','AmbientR':'0.62','AmbientG':'0.70','AmbientB':'0.88','SunlightStrength':'0.95','SunlightR':'1.4','SunlightG':'1.02','SunlightB':'0.64'})
    profile('auto-ground-only.ini',{'LightingMetadata':'Atmosphere21/empty.lsm'})
    profile('body-tata-bonnet.ini',{'BodyPrototype':'TataBonnet'})
    profile('body-tata-only.ini',{'BodyPrototype':'TataBonnet','WorldLighting':'0','CustomSet':'','CustomSkyUScale':'1','FogEnabled':'0'})
    shutil.copy2(profiles/'original.ini',runtime/'Atmosphere.ini')
    # Snapshot actual known user configurations for a separate compatibility
    # phase. They are supplied, never automatically installed or weakened.
    configs={}
    for name,source in [('PS2Port-baseline.ini',Path(r'D:\Game\Master Rallye Atmo-copy\PS2Port.ini')),('PS2Port-accepted-compat.ini',Path(r'D:\Game\Master Rallye Pristine\PS2Port.ini'))]:
        if not source.exists():raise ValueError('missing known comparison configuration '+str(source))
        shutil.copy2(source,profiles/name);configs[name]={'source':str(source),'sha256':sha(source)}
    on=configparser.ConfigParser(strict=False);on.read(profiles/'PS2Port-accepted-compat.ini')
    if on.getint('PS2Port','Reflection')!=4 or on.getint('PS2Port','VehicleLighting')!=1:raise ValueError('accepted compatibility profile is not Reflection4/VehicleLighting1')
    rollback=out/'rollback-runtime-003';rollback.mkdir();old=ROOT/'.research-output/atmosphere2/candidate-runtime-003/runtime-overlay'
    if sha(old/'d3d8.dll')!='f0563ed1656fe864b6c3403e7c15dc3dc5341f6c7cabadeda092796b76a02d1a':raise ValueError('rollback DLL drift')
    shutil.copy2(old/'d3d8.dll',rollback/'d3d8.dll');shutil.copytree(old/'Atmosphere2',rollback/'Atmosphere2');shutil.copy2(old/'Atmosphere.ini',rollback/'Atmosphere.ini')
    shutil.copytree(a.variant,out/'modified-render-configuration')
    sdk=out/'sdk';sdk.mkdir();shutil.copytree(ROOT/'src/master_rallye',sdk/'src/master_rallye',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    script=(PORT/'tools/atmosphere_lighting_metadata.py').read_text().replace("Path(__file__).resolve().parents[3]/'src'","Path(__file__).resolve().parent/'src'")
    (sdk/'export_lighting.py').write_text(script,encoding='utf-8')
    (sdk/'roles-example.json').write_text(json.dumps({'MyLayout':{'my_road-tga':'road','my_rock-tga':'terrain','my_leaves-tga':'vegetation','my_house-tga':'static','my_water-tga':'exclude'}},indent=2)+'\n')
    (sdk/'README_RU.md').write_text('''# Lighting Metadata для новых layout

Штатный runtime не требует Python, SDK или Blender. Для авторинга новой трассы:

python export_lighting.py --source "E:\\MyCourses" --course MyLayout --base "D:\\Game\\Master Rallye Atmo-copy\\Atmosphere21\\materials.lsm" --roles roles-example.json --output "E:\\MyLightingOutput"

Ожидается MyCourses/MyLayout/mylayout.dx и DXT-текстуры. Course SDK читает
валидированный revision-135 DX; неизвестные shader/material комбинации исключает.
--roles необязателен для понятных имён/подтверждённого base_noise грунта;
для нового неоднозначного plain-материала задайте exact имя и роль явно.
Вода/glass/glow/lamp/reflective secondary не могут стать static через override.
--base сохраняет материалы уже поддержанных трасс без чтения их исходников SDK.

Закройте игру, сохраните прежний materials.lsm, замените файл новым. DLL менять
не требуется. Метаданные читаются при новом процессе. Курс должен иметь валидный
RaceTest lifecycle/scene в самой игре; exporter не создаёт меню, маршрут или collision.
LSM1 хранит классы материалов/texture identity/winding, не список геометрии объектов.
Изменение вершин/UV/топологии/числа экземпляров при том же материале не требует
обновлять LSM1. Геометрические нормали и prelight кешируются из текущих буферов.
Совпадение текстуры с разными классами исключается как неоднозначное.

Если нет метаданных, AutoGround=1 допускает только непрозрачную static identity
геометрию, прошедшую полный нативный base_noise контракт и ground-normal проверку.
Это общий грунт (terrain), не доказанная семантическая road-классификация.
Неизвестная растительность/props/special passes остаются native.
''',encoding='utf-8')
    (out/'Verify-Installation.ps1').write_text('''param([Parameter(Mandatory=$true)][string]$GameRoot)
$ErrorActionPreference = 'Stop'
$targetRoot = (Resolve-Path -LiteralPath $GameRoot).ProviderPath.TrimEnd('\\')
$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'manifest.json') -Raw | ConvertFrom-Json
$checked = 0
foreach ($entry in $manifest.files.PSObject.Properties) {
    if (-not $entry.Name.StartsWith('runtime-overlay/')) { continue }
    $relative = $entry.Name.Substring('runtime-overlay/'.Length)
    if ($relative -eq 'Atmosphere.ini') { continue }
    $target = [IO.Path]::GetFullPath((Join-Path $targetRoot $relative))
    if (-not $target.StartsWith($targetRoot + '\\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Path escaped selected test root' }
    if (-not (Test-Path -LiteralPath $target -PathType Leaf)) { throw "Missing candidate file: $relative" }
    $stream = [IO.File]::OpenRead($target)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try { $actual = [BitConverter]::ToString($algorithm.ComputeHash($stream)).Replace('-', '').ToLowerInvariant() }
    finally { $algorithm.Dispose(); $stream.Dispose() }
    if ($actual -ne $entry.Value) { throw "Candidate file mismatch: $relative" }
    $checked++
}
Write-Output "Verified $checked installed candidate files. INI profile is intentionally user-selectable."
''',encoding='utf-8')
    shutil.copy2(PORT/'dist/current/build-report.json',out/'build-report.json')
    manifest={'status':'OFFLINE_VALIDATED_RUNTIME_PENDING','dll_sha256':sha(dll),'metadata_sha256':sha(materials/'materials.lsm'),
              'metadata_records':meta['records'],'runtime_geometry_atlas_bundled':False,'rollback_contains_legacy_atlas':True,'sky_assets':'Byte-identical to ATMOSPHERE2 validated pairs',
              'comparison_configs':configs,'sdk_lighting_source_sha256':sha(ROOT/'src/master_rallye/course_lighting.py'),
              'runtime_installation':'USER_MANUAL_ONLY','body_prototype':'OPT_IN_ORIGINAL_HEALTHY_TATA_BONNET_ONLY_RUNTIME_PENDING',
              'files':{p.relative_to(out).as_posix():sha(p) for p in sorted(out.rglob('*')) if p.is_file()}}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(out,manifest['dll_sha256'])

if __name__=='__main__':main()
