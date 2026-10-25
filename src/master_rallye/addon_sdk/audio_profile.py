"""Independent native MR engine and optional SFX authoring; no bundled audio.

MR's wsDsFxRevs synthesizer consumes one mono source waveform plus stock control
tables. This schema deliberately does not promise arbitrary RPM layers or GT4's
original multi-bank playback. Limits are SDK guards, not engine maxima.
"""
from __future__ import annotations
import copy, hashlib, math, os, re, struct
from pathlib import Path, PurePosixPath
from .manifest import AddonValidationError

NAMESPACE = re.compile(r'^[a-z][a-z0-9_]{1,31}$')
MAX_SOURCE_BYTES = 8 * 1024 * 1024
RATE = 48000

def _fail(message):
    raise AddonValidationError(message)

def validate_profile(profile):
    keys={'audio_profile_version','policy','physical_car_id','stock_audio_profile_id','namespace','engine','notes'}
    if not isinstance(profile,dict) or (set(profile)-{'transmission_whine','turbo_spool','bov_release'}!=keys): _fail('audio profile keys are invalid')
    if type(profile['audio_profile_version']) is not int or profile['audio_profile_version']!=1: _fail('unsupported audio profile version')
    if profile['policy']!='native_custom_engine': _fail('unsupported custom audio policy')
    if type(profile['physical_car_id']) is not int or not 26<=profile['physical_car_id']<=255: _fail('custom audio requires explicit addon CarID')
    if type(profile['stock_audio_profile_id']) is not int or not 0<=profile['stock_audio_profile_id']<=24: _fail('unqualified stock audio tuning profile')
    # The ice-cream/UFO cases own additional special state. Keep this first-stage
    # source substitution restricted to ordinary engine cases rather than hiding it.
    if profile['stock_audio_profile_id'] in (23,24): _fail('special stock audio cases are not custom-engine baselines')
    if not isinstance(profile['namespace'],str) or not NAMESPACE.fullmatch(profile['namespace']): _fail('invalid audio namespace')
    if not isinstance(profile['notes'],str) or len(profile['notes'])>8192: _fail('audio notes must be bounded text')
    engine=profile['engine']
    if not isinstance(engine,dict) or set(engine)!={'source_path','source_sha256','trim_frames','gain_db','remove_dc','crossfade_frames'}: _fail('invalid engine source declaration')
    path=engine['source_path']
    if not isinstance(path,str) or len(path)>240 or '\\' in path or ':' in path or not path or PurePosixPath(path).is_absolute() or any(x in ('','..','.') for x in path.split('/')) or PurePosixPath(path).suffix.lower()!='.wav': _fail('engine source must be a relative WAV path')
    if not isinstance(engine['source_sha256'],str) or not re.fullmatch('[a-f0-9]{64}',engine['source_sha256']): _fail('engine source SHA256 required')
    trim=engine['trim_frames']
    if not isinstance(trim,list) or len(trim)!=2 or any(type(v) is not int for v in trim) or not 0<=trim[0]<trim[1]<=2000000: _fail('engine trim must be an explicit bounded frame interval')
    gain=engine['gain_db']
    if type(gain) not in (int,float) or not math.isfinite(gain) or not -36<=gain<=12: _fail('engine gain outside SDK -36..12 dB guard')
    if type(engine['remove_dc']) is not bool: _fail('remove_dc must be boolean')
    cf=engine['crossfade_frames']
    if type(cf) is not int or not 0<=cf<=4096 or cf*8>trim[1]-trim[0]: _fail('crossfade exceeds source interval guard')
    for layer in ('transmission_whine','turbo_spool','bov_release'):
        if layer not in profile:continue
        whine=profile[layer]
        if not isinstance(whine,dict) or set(whine)!={'source','response','provenance'}: _fail('invalid transmission whine declaration')
        if not isinstance(whine['provenance'],str) or not 1<=len(whine['provenance'])<=8192: _fail('whine provenance must be bounded nonempty text')
        # Reuse exactly the established WAV guards; the additive source never
        # becomes an input to the existing native engine synthesizer.
        temporary={k:v for k,v in profile.items() if k not in ('transmission_whine','turbo_spool','bov_release')}
        temporary['engine']=whine['source'];validate_profile(temporary)
        response=whine['response']
        bounds={'reference_rpm':(500,20000),'pitch_min':(.125,1),'pitch_max':(1,2),
                'gain_drive':(0,1),'gain_coast':(0,1),'fade_in_rpm':(100,5000)}
        if layer=='turbo_spool':bounds={'reference_rpm':(500,20000),'pitch_min':(.125,1),'pitch_max':(1,2),'gain':(0,1),'fade_in_rpm':(100,5000),'load_threshold':(0,.95),'spool_up_seconds':(.02,5),'spool_down_seconds':(.02,5)}
        if layer=='bov_release':bounds={'release_rate_threshold':(.1,100),'boost_threshold':(.05,1),'gain':(0,1),'pitch_variation':(0,.25),'retrigger_seconds':(.1,5),'release_decay_seconds':(.02,5),'min_rpm':(500,10000)}
        required=set(bounds)|({'mute_neutral'} if layer!='bov_release' else set())
        allowed=required|({'mute_neutral'} if layer=='bov_release' else set())
        if not isinstance(response,dict) or not required<=set(response)<=allowed: _fail('invalid audio layer response keys')
        for key,(low,high) in bounds.items():
            value=response[key]
            if type(value) not in (int,float) or not math.isfinite(value) or not low<=value<=high: _fail('whine '+key+' outside SDK guard')
        if 'mute_neutral' in response and type(response['mute_neutral']) is not bool: _fail('audio mute_neutral must be boolean')
    return profile

def decode_pcm(raw):
    """Bounded RIFF PCM reader; accepts metadata chunks, never scans for data."""
    if not isinstance(raw,bytes) or not 44<=len(raw)<=MAX_SOURCE_BYTES or raw[:4]!=b'RIFF' or raw[8:12]!=b'WAVE' or struct.unpack_from('<I',raw,4)[0]+8!=len(raw): _fail('invalid or oversized RIFF/WAVE')
    pos=12;fmt=None;data=None
    while pos<len(raw):
        if pos+8>len(raw): _fail('truncated WAV chunk')
        kind=raw[pos:pos+4];length=struct.unpack_from('<I',raw,pos+4)[0];pos+=8
        if pos+length>len(raw): _fail('WAV chunk exceeds file')
        part=raw[pos:pos+length]
        if kind==b'fmt ':
            if fmt is not None or length not in (16,18): _fail('duplicate or unsupported PCM fmt chunk')
            fmt=struct.unpack_from('<HHIIHH',part)
            if length==18 and part[16:]!=b'\0\0': _fail('unsupported WAV format extension')
        if kind==b'data':
            if data is not None: _fail('duplicate WAV data')
            data=part
        pos+=length+(length&1)
    if pos!=len(raw) or fmt is None or data is None: _fail('incomplete WAV chunks')
    code,channels,rate,byte_rate,align,bits=fmt
    if code!=1 or channels not in (1,2) or bits not in (8,16,24,32) or not 11025<=rate<=48000 or align!=channels*(bits//8) or byte_rate!=rate*align or len(data)%align: _fail('unsupported or inconsistent PCM source format')
    count=len(data)//align
    if not count or count>2000000: _fail('PCM frame count outside guard')
    step=bits//8;values=[]
    for offset in range(0,len(data),align):
        total=0
        for channel in range(channels):
            b=data[offset+channel*step:offset+(channel+1)*step]
            n=(b[0]-128)<<8 if bits==8 else int.from_bytes(b,'little',signed=True)
            if bits>16:n >>= bits-16
            total+=n
        # Truncate toward zero, not toward negative infinity.
        values.append(int(total/channels))
    return values,{'sample_rate':rate,'channels':channels,'bits_per_sample':bits,'frames':count}

def canonical_wav(samples,rate=RATE):
    if type(rate) is not int or not 11025<=rate<=48000 or not samples: _fail('invalid canonical WAV arguments')
    if any(type(v) is not int or not -32768<=v<=32767 for v in samples): _fail('canonical PCM16 sample outside range')
    data=struct.pack('<'+'h'*len(samples),*samples)
    return b'RIFF'+struct.pack('<I',36+len(data))+b'WAVEfmt '+struct.pack('<IHHIIHH',16,1,1,rate,rate*2,2,16)+b'data'+struct.pack('<I',len(data))+data

def engine_resource(profile):
    validate_profile(profile)
    return 'vehicles/sdk/'+profile['namespace']+'/engine'


def whine_resource(profile):
    validate_profile(profile)
    if 'transmission_whine' not in profile: _fail('transmission whine is not configured')
    return 'vehicles/sdk/'+profile['namespace']+'/transmission_whine'


def turbo_resource(profile):
    validate_profile(profile)
    if 'turbo_spool' not in profile:_fail('turbo spool is not configured')
    return 'vehicles/sdk/'+profile['namespace']+'/turbo_spool'


def bov_resource(profile):
    validate_profile(profile)
    if 'bov_release' not in profile:_fail('BOV is not configured')
    return 'vehicles/sdk/'+profile['namespace']+'/bov_release'


def audio_resource_hashes(report):
    """Exact compiled resource allowlist, never arbitrary DataAudio paths."""
    if not isinstance(report,dict): _fail('audio compile report must be an object')
    profile=report.get('audio_profile');validate_profile(profile)
    resource=engine_resource(profile);path='DataAudio/'+resource+'.wav'
    digest=report.get('engine_sha256')
    if report.get('resource_path')!=path or report.get('engine_resource')!=resource or not isinstance(digest,str) or not re.fullmatch('[a-f0-9]{64}',digest): _fail('audio report engine resource/hash mismatch')
    result={path:digest}
    for layer,get_resource in (('transmission_whine',whine_resource),('turbo_spool',turbo_resource),('bov_release',bov_resource)):
        if layer not in profile:
            if layer in report:_fail('unconfigured audio layer in report')
            continue
        extra=report.get(layer);resource=get_resource(profile);path='DataAudio/'+resource+'.wav'
        if not isinstance(extra,dict) or extra.get('resource_path')!=path or extra.get('resource')!=resource or not isinstance(extra.get('sha256'),str) or not re.fullmatch('[a-f0-9]{64}',extra['sha256']): _fail('audio report whine resource/hash mismatch')
        if extra.get('response')!=profile[layer]['response'] or extra.get('provenance')!=profile[layer]['provenance']: _fail('audio report whine profile mismatch')
        result[path]=extra['sha256']
    return result

def _without_links(path):
    """Match project authoring's complete-ancestor link/junction policy."""
    absolute=Path(os.path.abspath(path));current=Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current=current/component
        if current.is_symlink() or getattr(current,'is_junction',lambda:False)():
            _fail('audio source path contains a symbolic link or junction: '+str(current))
    return absolute

def compile_audio(profile,source_root):
    """Return namespaced resource bytes and provenance; never replace stock WAVs."""
    validate_profile(profile)
    root=_without_links(source_root);source=_without_links(root.joinpath(*PurePosixPath(profile['engine']['source_path']).parts))
    if not root.is_dir() or not source.is_file() or not source.resolve().is_relative_to(root.resolve()): _fail('audio source missing or outside source root')
    if source.stat().st_size>MAX_SOURCE_BYTES: _fail('audio source exceeds size guard')
    raw=source.read_bytes();digest=hashlib.sha256(raw).hexdigest()
    if digest!=profile['engine']['source_sha256']: _fail('audio source SHA256 mismatch')
    values,fmt=decode_pcm(raw);engine=profile['engine'];a,b=engine['trim_frames']
    if b>len(values): _fail('audio trim exceeds source frames')
    values=values[a:b]
    if not .1<=len(values)/fmt['sample_rate']<=4: _fail('engine source interval must be 0.1..4 seconds')
    dc=sum(values)/len(values) if engine['remove_dc'] else 0.;gain=10**(engine['gain_db']/20)
    values=[int(round((v-dc)*gain)) for v in values]
    if min(values)<-32768 or max(values)>32767: _fail('audio gain clips PCM16; lower gain_db')
    cf=engine['crossfade_frames']
    if cf:
        # Circular overlap, shortening the loop by cf; explicit authoring choice.
        joined=[round((values[-cf+i]*(cf-i)+values[i]*i)/cf) for i in range(cf)]
        values=joined+values[cf:-cf]
    # Integer linear resampling. No audioop, external executable or modern DSP.
    count=(len(values)*RATE)//fmt['sample_rate'];out=[]
    for i in range(count):
        q,r=divmod(i*fmt['sample_rate'],RATE);v0=values[min(q,len(values)-1)];v1=values[min(q+1,len(values)-1)]
        out.append(round((v0*(RATE-r)+v1*r)/RATE))
    if not any(out): _fail('silent engine source')
    wav=canonical_wav(out);resource=engine_resource(profile);member='DataAudio/'+resource+'.wav'
    report={'audio_profile':copy.deepcopy(profile),'engine_resource':resource,'resource_path':member,'engine_sha256':hashlib.sha256(wav).hexdigest(),
        'source_sha256':digest,'source_format':fmt,'output_format':{'channels':1,'bits_per_sample':16,'sample_rate':RATE,'frames':len(out)},
        'peak_pcm16':max(abs(v) for v in out),'rms_pcm16':math.sqrt(sum(v*v for v in out)/len(out)),
        'approximation':'one source waveform through native MR wsDsFxRevs synthesizer and unchanged stock control tables; not GT4 multilayer playback',
        'runtime_qualified':False}
    resources={member:wav}
    for layer,get_resource in (('transmission_whine',whine_resource),('turbo_spool',turbo_resource),('bov_release',bov_resource)):
        if layer not in profile:continue
        temporary={k:copy.deepcopy(v) for k,v in profile.items() if k not in ('transmission_whine','turbo_spool','bov_release')}
        temporary['engine']=copy.deepcopy(profile[layer]['source'])
        extra,detail=compile_audio(temporary,source_root)
        whine_member='DataAudio/'+get_resource(profile)+'.wav'
        resources[whine_member]=next(iter(extra.values()))
        report[layer]={'resource_path':whine_member,'resource':get_resource(profile),
            'sha256':detail['engine_sha256'],'source_sha256':detail['source_sha256'],
            'source_format':detail['source_format'],'output_format':detail['output_format'],
            'peak_pcm16':detail['peak_pcm16'],'rms_pcm16':detail['rms_pcm16'],
            'response':copy.deepcopy(profile[layer]['response']),
            'provenance':profile[layer]['provenance'],
            'boundary':'Independent ordinary native SFX loop; inputshaft speed and signed net crank torque response are an authored approximation, not original GT transmission playback.',
            'runtime_qualified':False}
        if layer!='transmission_whine':
            report[layer]['boundary']='Independent native SFX with authored estimated spool/load-release response; not a recovered GT playback system or physical boost signal.'
    return resources,report
