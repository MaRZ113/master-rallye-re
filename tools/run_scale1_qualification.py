"""Build a private, pinned SCALE1 capacity canary and perform offline preflight.

Never starts Master Rallye. This intentionally uses stock Navara geometry, not
an invented Lancer. The fixed-base canary is separate from general SDK planning.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
import prepare_sdk_capacity_probe as probe
import build_runtime_launcher as launcher


def run(base,output,count,emulate=False):
    output=probe.runtime._under_research_output(output)
    if output.exists():raise ValueError('output exists')
    rows=json.loads((ROOT/f'research/vehicles/scale1/probe-{count}-rows.json').read_text())
    source=(ROOT.parent/'MRallye.exe').read_bytes()
    storage='existing_cave' if count==29 else 'private_allocation'
    verify=lambda:probe.verify(output/'runtime',base,rows,source,storage=storage)
    report={'schema_version':1,'game_launched':False,'runtime_qualified':False,
            'vehicle_identity':'explicit stock Navara capacity canaries; not Lancer',
            'storage':storage,'record_count':count}
    report['bundle']=probe.prepare(base,rows,output/'runtime',source,storage=storage)
    if emulate:
        from validate_sdk_capacity_emulation import validate
        _,_,context=probe.derive(base,rows,source,storage=storage)
        report['emulation']=validate(source,context['image'],context['extension'],context['rows'])
    report['launcher']=launcher.build_launcher(bundle=output/'runtime',output=output/'launcher',bundle_verifier=verify)
    preflight={}
    modes=['--verify','--verify-launch-environment']
    if storage=='private_allocation':modes.append('--self-test-native-allocation')
    for mode in modes:
        result=subprocess.run([str(output/'launcher/mr-runtime-launcher.exe'),mode,
            str(ROOT.parent/'MRallye.exe'),str(output/'runtime')],capture_output=True,text=True)
        preflight[mode]={'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr}
        if result.returncode:raise ValueError('launcher preflight failed: '+str(preflight[mode]))
    report['preflight']=preflight
    # Immutable base resources may only differ at these explicitly composed
    # shared files; previous individual vehicle families and frames stay exact.
    base_index=json.loads((base/'resource-manifest.json').read_text())
    allowed=set(json.loads((output/'runtime/composition-report.json').read_text())['shared_composed_paths'])
    preserved=[]
    for row in base_index['resources']:
        if row['path'] in allowed or probe.runtime.is_user_editable_resource(row['path']):continue
        if probe.runtime.sha256_file(output/'runtime/resource-root'/row['path'])!=row['sha256']:
            raise ValueError('frozen resource changed outside explicit composition')
        preserved.append(row['path'])
    report['preserved_frozen_immutable_resources']=len(preserved)
    report['composed_shared_paths']=sorted(allowed)
    report['final_verify']=verify()
    (output/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    handoff=f'''# SCALE1 private capacity candidate: {count} records

Offline validated only. Contains unchanged Subaru V-MESH4.13 and Mercedes,
plus {count-28} independently registered stock Navara geometry canaries with
SDK PROBE names. This is not a combined Subaru + GT4 Lancer release.

Run `launcher/mr-runtime-launcher.exe --integrated "D:\\Game\\Master Rallye\\MRallye.exe" "{output/'runtime'}"`.
The launcher modifies only suspended process memory. Original EXE/DLL stay
unchanged. Quit before trying another bundle. Use the separate bundle-local
player state; do not copy an existing campaign save into this experiment.

Check all stock/T1/T2 selections, Subaru and every SDK PROBE, both player
selections, a new Quick Race, AI pool, Results and return/re-entry. Check
reflections on/off. Campaign progression, persisted competitions and network
compatibility remain unqualified. Do not treat a static pass as gameplay proof.

Try the 29-record candidate first; the 30-record candidate tests a separate
fixed private memory block and an additional row. Occupied address fails closed.
Native allocation self-test only writes/verifies RX memory; executes no payload.

Full findings: research/vehicles/scale1/README.md, capacity.md, gt4.md in the repo.
'''
    (output/'HANDOFF.md').write_text(handoff)
    archive=output.parent/(output.name+'-private-candidate.zip')
    if archive.exists():raise ValueError('archive exists')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        for p in sorted(output.rglob('*')):
            if p.is_file():z.write(p,output.name+'/'+p.relative_to(output).as_posix())
    with zipfile.ZipFile(archive) as z:
        if z.testzip():raise ValueError('private archive CRC failure')
    result={'status':'PASS_OFFLINE_READY_FOR_HUMAN_CAPACITY_TEST',
            'candidate':str(output),'archive':str(archive),
            'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
            'runtime_qualified':False,'game_launched':False}
    (output.parent/(output.name+'-archive.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--records',type=int,choices=[29,30],required=True)
    p.add_argument('--emulate',action='store_true',help='requires optional private Unicorn/Capstone dependencies')
    a=p.parse_args();run(a.base,a.output,a.records,a.emulate)
