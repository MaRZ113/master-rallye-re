"""Optional local media decoding and reviewed import over the established DSP.

No GT dependency, new mixer or native hook. Originals and decoded pins are private.
"""
from __future__ import annotations
import copy,json,math,shutil,struct,subprocess,uuid
from pathlib import Path
from master_rallye.addon_sdk.audio_profile import decode_pcm,canonical_wav,compile_audio
from .audio import sha,LAYERS

MAX_MEDIA_BYTES=64*1024*1024
MAX_SECONDS=30
EXTENSIONS={'.wav','.flac','.mp3','.ogg'}

def decoder_capabilities():
    tools={name:shutil.which(name) for name in ('ffmpeg','ffprobe')}
    return {'pcm_wav':'existing bounded RIFF PCM decoder','optional_media':sorted(EXTENSIONS) if all(tools.values()) else [],'tools':tools,'boundary':'External decoding is optional. No proprietary banks or GT ownership required. Verified extensions/codec checks only.'}

def run_decoder(command,timeout=60):
    options={}
    if hasattr(subprocess,'CREATE_NO_WINDOW'):options['creationflags']=subprocess.CREATE_NO_WINDOW
    result=subprocess.run(command,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout,**options)
    if result.returncode:raise ValueError('Local audio decoder failed: '+result.stderr.decode('utf-8',errors='replace')[-1000:])
    return result.stdout

def wav_loop(raw,frames):
    """Read one forward RIFF smpl loop; preserve unsupported forms as diagnostics."""
    if raw[:4]!=b'RIFF' or raw[8:12]!=b'WAVE':return None
    at=12
    while at+8<=len(raw):
        kind=raw[at:at+4];size=struct.unpack_from('<I',raw,at+4)[0];at+=8
        if at+size>len(raw):raise ValueError('Truncated original WAV metadata')
        if kind==b'smpl':
            if size<36:raise ValueError('Short smpl metadata')
            count=struct.unpack_from('<I',raw,at+28)[0]
            if count!=1 or size<60:return {'status':'UNSUPPORTED_LOOP_LAYOUT','loop_count':count}
            _,kind,start,end,fraction,repeats=struct.unpack_from('<6I',raw,at+36)
            if kind or fraction or not 0<=start<=end<frames:return {'status':'UNSUPPORTED_LOOP_LAYOUT','type':kind,'start':start,'inclusive_end':end}
            return {'status':'FORWARD_SOURCE_LOOP','frames':[start,end+1],'repeat_count':repeats,'semantics':'RIFF inclusive end converted to exclusive source frame end'}
        at+=size+(size&1)
    return None

def decode_media(path):
    from .service import plain_tree
    path=plain_tree(path).resolve()
    if path.suffix.lower() not in EXTENSIONS or not path.is_file() or not 44<=path.stat().st_size<=MAX_MEDIA_BYTES:raise ValueError('Choose bounded local WAV/FLAC/MP3/Ogg audio (64 MiB maximum)')
    with path.open('rb') as stream:raw=stream.read(MAX_MEDIA_BYTES+1)
    if len(raw)>MAX_MEDIA_BYTES:raise ValueError('Source changed beyond media budget')
    try:
        values,fmt=decode_pcm(raw)
        if len(values)/fmt['sample_rate']>MAX_SECONDS:raise ValueError('Audio Import 2.0 source exceeds 30 seconds; trim the original into a separate file first')
        return raw,raw,{'input_format':fmt,'decoded_format':fmt,'decoder':'existing SDK RIFF PCM','source_loop':wav_loop(raw,len(values)),'duration_seconds':len(values)/fmt['sample_rate']}
    except ValueError as exc:
        if 'exceeds 30 seconds' in str(exc):raise
    caps=decoder_capabilities()
    if not caps['optional_media']:raise ValueError('This source requires optional ffmpeg AND ffprobe on PATH; bounded RIFF PCM WAV remains available')
    probe=run_decoder([caps['tools']['ffprobe'],'-v','error','-protocol_whitelist','file,pipe','-show_streams','-show_format','-of','json',str(path)])
    if len(probe)>1024*1024:raise ValueError('Decoder metadata exceeds budget')
    info=json.loads(probe);streams=[x for x in info.get('streams',[]) if x.get('codec_type')=='audio']
    if len(streams)!=1 or any(x.get('codec_type')=='video' and not x.get('disposition',{}).get('attached_pic') for x in info.get('streams',[])):raise ValueError('Exactly one audio stream required; video containers unsupported')
    stream=streams[0];codec=stream.get('codec_name','');container=info.get('format',{}).get('format_name','').split(',')
    allowed={'.flac':('flac',{'flac'}),'.mp3':('mp3',{'mp3'}),'.ogg':('ogg',{'vorbis','opus'}),'.wav':('wav',{'pcm_u8','pcm_s16le','pcm_s24le','pcm_s32le','pcm_f32le','pcm_f64le','pcm_s16be'})}
    expected,codecs=allowed[path.suffix.lower()]
    if expected not in container or codec not in codecs:raise ValueError('Audio extension/container/codec combination is not supported')
    rate=int(stream['sample_rate']);channels=int(stream['channels']);duration=float(stream.get('duration',info['format'].get('duration',0)))
    if channels not in (1,2) or not 8000<=rate<=192000 or not math.isfinite(duration) or not 0<duration<=MAX_SECONDS:raise ValueError('Source must be mono/stereo, 8000..192000 Hz, finite duration up to 30 seconds')
    pcm=run_decoder([caps['tools']['ffmpeg'],'-nostdin','-v','error','-max_alloc','67108864','-protocol_whitelist','file,pipe','-i',str(path),'-map','0:a:0','-vn','-sn','-dn','-t',str(MAX_SECONDS+.001),'-ac','1','-ar','48000','-c:a','pcm_s16le','-f','s16le','pipe:1'])
    with path.open('rb') as stream:
        if stream.read(MAX_MEDIA_BYTES+1)!=raw:raise ValueError('Original media changed during decoding; retry from an immutable file')
    if not pcm or len(pcm)%2 or len(pcm)>MAX_SECONDS*48000*2:raise ValueError('Decoded audio exceeds frame budget')
    decoded=canonical_wav(list(struct.unpack('<'+'h'*(len(pcm)//2),pcm)));_,fmt=decode_pcm(decoded)
    original={'sample_rate':rate,'channels':channels,'codec':codec,'container':container,'frames':round(duration*rate)}
    loop=wav_loop(raw,original['frames'])
    if loop and loop['status']=='FORWARD_SOURCE_LOOP':loop['decoded_frames']=[round(x*48000/rate) for x in loop['frames']]
    version=run_decoder([caps['tools']['ffmpeg'],'-version']).decode('utf-8',errors='replace').splitlines()[0]
    return raw,decoded,{'input_format':original,'decoded_format':fmt,'decoder':version,'decoder_paths':caps['tools'],'duration_seconds':duration,'source_loop':loop,'conversion':'Optional decoder downmix/resample to mono PCM16 48000 Hz; encoded source immutable'}

class AudioImportAuthoring:
    def audio_prepare_import(self,path,*,trim=None,crossfade=0,gain_db=0,remove_dc=True,use_source_loop=False,source_evidence=None):
        from .service import write_json
        self.audio_state();raw,decoded,media=decode_media(path);values,fmt=decode_pcm(decoded)
        if source_evidence and (source_evidence.get('adapter_schema')!='gt-sound-bank-lab/1' or source_evidence.get('wav_sha256')!=sha(raw) or source_evidence.get('authentic_effect_identity') is not None):raise ValueError('GT source evidence does not match this individual source WAV')
        loop=media['source_loop']
        if use_source_loop:
            if not loop or loop['status']!='FORWARD_SOURCE_LOOP':raise ValueError('No qualified forward source loop; use explicit trim')
            trim=loop.get('decoded_frames',loop['frames'])
        trim=trim or [0,min(len(values),fmt['sample_rate']*4)]
        source={'source_path':'decoded.wav','source_sha256':sha(decoded),'trim_frames':trim,'crossfade_frames':crossfade,'gain_db':gain_db,'remove_dc':remove_dc}
        profile={k:v for k,v in self.audio_effective().items() if k not in LAYERS[1:]};profile['engine']=source
        out=self.root/'audio-import-previews'/uuid.uuid4().hex;out.mkdir(parents=True);(out/'decoded.wav').write_bytes(decoded)
        resources,detail=compile_audio(profile,out);converted=next(iter(resources.values()));(out/'converted.wav').write_bytes(converted)
        excerpt=canonical_wav(values[trim[0]:trim[1]],fmt['sample_rate']);(out/'original-preview.wav').write_bytes(excerpt)
        original=out/('original'+Path(path).suffix.lower());original.write_bytes(raw)
        report={'version':1,'preview_root':str(out),'original_path':str(Path(path).resolve()),'original_name':Path(path).name,'original_sha256':sha(raw),'original_pin':str(original),'decoded_sha256':sha(decoded),'native_sha256':sha(converted),'media':media,'source':source,'compiler':detail,'source_evidence':copy.deepcopy(source_evidence),'decoded_full_scale_samples':sum(abs(v)>=32767 for v in values),'decoder_clipping_boundary':'Native gain clipping is rejected exactly. Source/lossy/float-decoder saturation is not proof of unclipped original audio; inspect full-scale sample count and audition.',
                'loop_endpoint_jump_pcm16':abs(values[trim[0]]-values[trim[1]-1]),'boundary':'Reviewed source excerpt vs actual native resource conversion. Native DSP/DirectSound/gameplay mixing is a separate audition and owner test.'}
        write_json(out/'import.json',report);return report

    def audio_apply_import(self,report,layer):
        from .service import plain_tree,write_resource
        if layer not in LAYERS:raise ValueError('Unknown audio layer')
        out=plain_tree(report['preview_root']).resolve()
        if not out.is_relative_to((self.root/'audio-import-previews').resolve()):raise ValueError('Import preview belongs to another project')
        stored=json.loads((out/'import.json').read_text())
        if stored!=report:raise ValueError('Reviewed import report changed')
        decoded=(out/'decoded.wav').read_bytes();converted=(out/'converted.wav').read_bytes();original=plain_tree(report['original_pin'])
        if original.parent!=out or sha(original.read_bytes())!=report['original_sha256'] or sha(decoded)!=report['decoded_sha256'] or sha(converted)!=report['native_sha256']:raise ValueError('Reviewed import bytes changed')
        state=self.audio_state()
        if layer not in state['profile']:raise ValueError('Layer has no qualified response defaults; import a compatible preset first')
        source=copy.deepcopy(report['source']);source['source_path']='workshop-audio/'+source['source_sha256']+'.wav'
        self._audio_pin(out/'decoded.wav',source['source_sha256'])
        evidence=report['source_evidence'];title=(evidence['game'].upper()+' '+evidence['bank_id']+' :: '+str(evidence['selected_entry']['entry_id'])) if evidence else report['original_name']
        if layer=='engine':state['profile'][layer]=source
        else:
            state['profile'][layer]['source']=source;state['profile'][layer]['provenance']='Private source adaptation: '+title+'; full original/decoder/GT evidence in project import metadata; acoustic identity not asserted'
        digest=source['source_sha256'];record={'name':title,'original_path':report['original_path'],'original_sha256':report['original_sha256'],'sha256':digest,'format':report['media']['decoded_format'],'media':report['media'],'gt_source':evidence,'reviewed_native_sha256':report['native_sha256'],'source_options':source,'rights':'Private user-supplied input; no redistribution implied'}
        old=state['imports'].get(digest);origins=copy.deepcopy(old.get('origins',[old]) if old else [])
        if record not in origins:origins.append(copy.deepcopy(record))
        state['imports'][digest]={**record,'origins':origins};state.setdefault('layer_imports',{})[layer]=copy.deepcopy(record)
        check=copy.deepcopy(state);check['enabled'][layer]=True
        resources,detail=self.audio_compile(check);member=detail['resource_path'] if layer=='engine' else detail[layer]['resource_path']
        if resources[member]!=converted:raise ValueError('Target layer conversion differs from reviewed native bytes')
        target=plain_tree(self.root/'audio-originals'/(report['original_sha256']+original.suffix));target.parent.mkdir(exist_ok=True);write_resource(target,original.read_bytes())
        self._audio_commit(state);return self.audio_inspect()
