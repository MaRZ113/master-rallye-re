"""Package the verified opt-in atmosphere overlay locally; never deploy it.

Refuses a stale build report or an existing destination. Private sky assets are
included only from an explicitly supplied atmosphere_catalog output.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil

PORT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--catalog',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    report_path=PORT/'dist/current/build-report.json';report=json.loads(report_path.read_text())
    for name,digest in report['ps2_source_sha256'].items():
        if sha(PORT/name)!=digest:raise ValueError(f'stale build report: {name}')
    for name,digest in report['patch_sha256'].items():
        if sha(PORT/'overlay/patches'/name)!=digest:raise ValueError(f'stale integration patch: {name}')
    dll=PORT/'.build/ps2-enabled/Release/d3d8.dll'
    if sha(dll)!=report['builds']['ps2-enabled']['dll_sha256']:raise ValueError('DLL differs from verified build report')
    output=a.output.resolve()
    if output.exists():raise ValueError('new output directory required; nothing overwritten')
    overlay=output/'runtime-overlay';overlay.mkdir(parents=True)
    shutil.copy2(dll,overlay/'d3d8.dll')
    shutil.copy2(PORT/'Atmosphere.ini',overlay/'Atmosphere.ini')
    assets=overlay/'Atmosphere/sets/sunset';assets.mkdir(parents=True)
    for name in ('clouds.dxt','layer.dxt'):shutil.copy2(a.catalog/'sets/sunset'/name,assets/name)
    profiles=output/'profiles';profiles.mkdir()
    stock=(PORT/'Atmosphere.ini').read_text()
    for preset in range(6):
        (profiles/f'sky-{preset}.ini').write_text(stock.replace('Enabled=0','Enabled=1').replace('SkyPreset=Auto',f'SkyPreset={preset}'))
    sunset=stock.replace('Enabled=0','Enabled=1').replace('SkyPreset=Auto','SkyPreset=3').replace('CustomSet=\n','CustomSet=Atmosphere\\sets\\sunset\n')
    (profiles/'sunset-sky-only.ini').write_text(sunset)
    (profiles/'sunset-terrain.ini').write_text(sunset.replace('WorldLighting=0','WorldLighting=1'))
    (profiles/'light-probe.ini').write_text(stock.replace('Enabled=0','Enabled=1').replace('SkyPreset=Auto','SkyPreset=3').replace('LightProbe=0','LightProbe=1'))
    shutil.copy2(report_path,output/'build-report.json')
    (output/'README.md').write_text('''# Atmosphere phase 1 — private experimental overlay

OFFLINE_VALIDATED; game A/B and compatibility acceptance are pending.

Use a separate copy of the accepted game installation and preserve that copy's
current d3d8.dll for rollback. Copy runtime-overlay contents to its game root.
Do not change PS2Port.ini or the installed dinput8.dll. Default Atmosphere.ini
has Enabled=0. Copy one profiles/*.ini to the copied game root as Atmosphere.ini
and restart. SkyPreset alone can then be edited before the next race reload.

For A/B use sky-3.ini as A, then sunset-sky-only.ini, then sunset-terrain.ini.
Keep course, car, camera, render settings, CloudNumber=3 and capture point equal.
Light-probe.ini needs actual road world coordinates in LightX/Y/Z; defaults are
not a promised visible source. LightProbe moves the source along X over time.

Sun and SunFlare are reserved and suppressed: no verified depth visibility yet.
Terrain lighting is a narrow base_noise prototype, not complete world/car lighting.
No gameplay, reset/MSAA or effect-compatibility acceptance is claimed.

Rollback: restore the copied installation's saved DLL; remove the added
Atmosphere.ini / Atmosphere directory. No retail archive was modified.
No launcher, installation or publication is performed by this package.
''',encoding='utf-8')
    manifest={'status':'OFFLINE_VALIDATED_RUNTIME_PENDING','source_head':report['current_head'],
              'files':{p.relative_to(output).as_posix():sha(p) for p in sorted(output.rglob('*')) if p.is_file()}}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Private overlay prepared (not deployed): {output}; DLL {sha(dll)}')
if __name__=='__main__':main()
