"""Prove a custom engine candidate adds one owned WAV and exact native binding.

Baseline must have identical physics, visual resources and existing extensions.
This validator never launches the game or claims audible gameplay behavior.
"""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.addon_sdk.audio_profile import decode_pcm,engine_resource,validate_profile
from vehicle_audio_native import append_audio
import j2_frontend_reentry as j2
MUTABLE={'datagame/options.xml','datagame/options.xml#','datagame/playerstate.xml','datagame/playerstate.xml#'}

def validate(baseline,candidate,profile,exe):
    validate_profile(profile)
    def tree(root):return {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file() and p.relative_to(root).as_posix().casefold() not in MUTABLE}
    before=tree(baseline/'resource-root');after=tree(candidate/'resource-root');member='DataAudio/'+engine_resource(profile)+'.wav'
    if member in before or set(after)-set(before)!={member} or set(before)-set(after):raise ValueError('audio candidate changes the immutable resource set outside its new namespace')
    if any(before[k]!=after[k] for k in before):raise ValueError('audio candidate changed physics, geometry, stock audio or UI')
    samples,fmt=decode_pcm(after[member])
    if (fmt['channels'],fmt['bits_per_sample'],fmt['sample_rate'])!=(1,16,48000) or len(after[member])!=44+len(samples)*2:raise ValueError('unsupported engine format')
    for name in ('addon-plan.json','frontend-overlay.plan.json'):
        if (baseline/name).read_bytes()!=(candidate/name).read_bytes():raise ValueError('audio candidate changed identity or frontend')
    source=exe.read_bytes();old=j2._parse_and_reconstruct(source,(baseline/'native-patch-ops.rvp').read_bytes())[1]
    new=j2._parse_and_reconstruct(source,(candidate/'native-patch-ops.rvp').read_bytes())[1]
    ext=json.loads((baseline/'runtime-profile.json').read_text())['native_extension']
    expected,blob,report=append_audio(source,old,(baseline/'native-extension.bin').read_bytes(),ext['address'],[profile],ext['allocation_size'])
    if new!=expected or blob!=(candidate/'native-extension.bin').read_bytes():raise ValueError('audio candidate native changes exceed exact source binding')
    policy=json.loads((baseline/'damage-alpha-policy.json').read_text());policy['independent_engine_audio']={k:v for k,v in report.items() if k!='operations'}
    if policy!=json.loads((candidate/'damage-alpha-policy.json').read_text()):raise ValueError('audio candidate changed damage/ride policy')
    return {'status':'PASS_INDEPENDENT_AUDIO_REVISION','unchanged_resource_count':len(before),'new_resource':member,
        'new_resource_sha256':hashlib.sha256(after[member]).hexdigest(),'source_format':fmt,'native_binding':report,
        'runtime_qualified':False,'boundary':'exact resource and process-code comparison, no DirectSound playback/race confirmation'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--profile',type=Path,required=True);p.add_argument('--exe',type=Path,default=ROOT.parent/'MRallye.exe');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=validate(a.baseline,a.candidate,json.loads(a.profile.read_text()),a.exe);a.output.write_text(json.dumps(r,indent=2)+'\n');print(r['status'])
