"""Reversible project audio authoring. Native playback remains in addon_sdk.

Imports are pinned private PCM copies; presets contain no native allocation IDs.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
import re
from pathlib import Path
from master_rallye.addon_sdk.audio_profile import compile_audio, decode_pcm, MAX_SOURCE_BYTES

LAYERS = ('engine', 'transmission_whine', 'turbo_spool', 'bov_release')
LABELS = ('Engine', 'Transmission Whine', 'Turbo Spool', 'BOV / pressure release')

def sha(raw): return hashlib.sha256(raw).hexdigest()

def read_wav(path):
    from .service import plain_tree
    path = plain_tree(path)
    if not path.is_file():raise ValueError('Audio WAV missing: '+str(path))
    if path.suffix.lower() != '.wav' or not path.is_file() or path.stat().st_size > MAX_SOURCE_BYTES:
        raise ValueError('Select a bounded local RIFF PCM WAV (8 MiB maximum)')
    raw = path.read_bytes()
    samples, fmt = decode_pcm(raw)
    return raw, samples, fmt

def sources(profile):
    for layer in LAYERS:
        if layer in profile:
            yield layer, profile[layer] if layer == 'engine' else profile[layer]['source']

class AudioAuthoring:
    def audio_state(self):
        if self.data['kind'] != 'addon': raise ValueError('Audio authoring requires a qualified SDK addon project')
        if 'audio' not in self.data or not self.data['audio']:
            from .service import write_json
            path = self.working/'audio-profile.json'
            if not path.is_file(): raise ValueError('This addon has no qualified custom audio profile; stock passthrough is unchanged')
            if path.stat().st_size > 65536: raise ValueError('Audio profile exceeds JSON budget')
            profile = json.loads(path.read_text())
            compile_audio(profile, self.working)
            # A lazy baseline also supports projects made before Audio Studio.
            baseline = self.root/'audio-baseline.json'
            if baseline.exists():
                profile = json.loads(baseline.read_text())
            else:
                write_json(baseline, profile)
            for _, source in sources(profile):
                self._audio_pin(self.working/source['source_path'], source['source_sha256'])
            self.data['audio'] = {'profile':copy.deepcopy(profile), 'enabled':{k:True for k in LAYERS if k in profile},
                                  'imports':{}, 'presets':{}, 'baseline_sha256':sha(baseline.read_bytes())}
            self.save()
        return copy.deepcopy(self.data['audio'])

    def _audio_pin(self, path, expected):
        from .service import write_resource
        raw, _, _ = read_wav(path)
        if sha(raw) != expected: raise ValueError('Audio source SHA256 mismatch: '+str(path))
        folder = self.root/'audio-sources'; folder.mkdir(exist_ok=True)
        write_resource(folder/(expected+'.wav'), raw)
        return raw

    def audio_effective(self, state=None):
        state = state or self.audio_state()
        profile = copy.deepcopy(state['profile'])
        for key in LAYERS[1:]:
            if not state['enabled'].get(key, False):
                # BOV uses this estimator even when its continuous spool sound is
                # muted. Keep qualified pressure controls rather than substitute
                # native defaults by deleting the whole turbo declaration.
                if key=='turbo_spool' and key in profile:profile[key]['response']['gain']=0.
                else:profile.pop(key, None)
        return profile

    def audio_compile(self, state=None):
        """Compile against a private pinned source tree, independent of working files."""
        from .service import plain_tree, write_resource
        state = state or self.audio_state()
        if sha((self.root/'audio-baseline.json').read_bytes())!=state['baseline_sha256']:raise ValueError('Audio baseline changed')
        from master_rallye.addon_sdk.audio_profile import validate_profile
        validate_profile(state['profile'])
        if not isinstance(state['enabled'],dict) or set(state['enabled'])-set(LAYERS) or any(type(v) is not bool for v in state['enabled'].values()):
            raise ValueError('Invalid audio enable map')
        if state['enabled'].get('engine') is not True:raise ValueError('Native engine must remain enabled')
        profile = self.audio_effective(state)
        cache = self.root/'audio-compile'; cache.mkdir(exist_ok=True)
        for _, source in sources(state['profile']):
            # Schema validation below rejects traversal; check before path construction too.
            rel = source['source_path']
            if not isinstance(rel,str) or '\\' in rel or ':' in rel or rel.startswith('/') or any(p in ('','.','..') for p in rel.split('/')):
                raise ValueError('Unsafe audio source path')
            pin = self.root/'audio-sources'/(source['source_sha256']+'.wav')
            raw, _, _ = read_wav(pin)
            if sha(raw) != source['source_sha256']: raise ValueError('Pinned audio source changed')
            target = plain_tree(cache/rel); target.parent.mkdir(parents=True,exist_ok=True); write_resource(target,raw)
        full=compile_audio(state['profile'],cache)
        return full if profile==state['profile'] else compile_audio(profile,cache)

    def audio_inspect(self):
        state = self.audio_state(); resources, report = self.audio_compile(state)
        layers = {}
        for key, source in sources(state['profile']):
            raw, samples, fmt = read_wav(self.root/'audio-sources'/(source['source_sha256']+'.wav'))
            detail = report if key == 'engine' else report.get(key)
            warnings = []
            if key != 'bov_release' and abs(samples[source['trim_frames'][0]]-samples[source['trim_frames'][1]-1]) > 2048 and not source['crossfade_frames']:
                warnings.append('Loop endpoint jump exceeds 2048 PCM16 units; audition or use crossfade')
            layers[key] = {'enabled':state['enabled'].get(key,True), 'source':source,
                'provenance':state['imports'].get(source['source_sha256'],{}),
                'source_format':fmt,'seconds':len(samples)/fmt['sample_rate'],
                'playback':'one-shot' if key == 'bov_release' else 'continuous',
                'compiled':detail,'warnings':warnings}
        return {'layers':layers,'profile':state['profile'],'resources':{k:sha(v) for k,v in resources.items()},
                'presets':list(self.audio_available_presets()),'boundary':'Native MR engine synthesis; supplementary layers use signed crank-torque load and estimated spool, not a boost/throttle sensor. Gameplay listening pending. Disabling spool mutes its gain while retaining the BOV pressure estimator.'}

    def _audio_commit(self, state):
        # Compile BEFORE history/state mutation; clipping/missing input fails atomically.
        self.audio_compile(state)
        self._record(); self.data['audio'] = state
        self.audio_materialize(); self.save()

    def audio_update(self, layer, *, source=None, response=None, enabled=None, stock_profile=None):
        if layer not in LAYERS: raise ValueError('Unknown audio layer')
        state = self.audio_state(); profile = state['profile']
        if layer not in profile: raise ValueError('No qualified default for this layer; assign a compatible preset first')
        if enabled is not None:
            if type(enabled) is not bool: raise ValueError('Enable requires boolean')
            if layer == 'engine' and not enabled: raise ValueError('Engine disable is audition-only; native engine replacement cannot be muted by this schema')
            state['enabled'][layer] = enabled
        if source is not None:
            if layer == 'engine': profile[layer] = copy.deepcopy(source)
            else: profile[layer]['source'] = copy.deepcopy(source)
        if response is not None:
            if layer == 'engine': raise ValueError('Engine response uses stock synthesis tables')
            profile[layer]['response'] = copy.deepcopy(response)
        if stock_profile is not None: profile['stock_audio_profile_id'] = stock_profile
        # Validate disabled declarations too, so invalid hidden edits cannot persist.
        from master_rallye.addon_sdk.audio_profile import validate_profile
        validate_profile(profile)
        self._audio_commit(state)

    def audio_import(self, layer, path, *, trim=None, crossfade=0, gain_db=0, remove_dc=True):
        if layer not in LAYERS: raise ValueError('Unknown audio layer')
        raw,samples,fmt = read_wav(path); digest = sha(raw)
        state = self.audio_state()
        if layer not in state['profile']: raise ValueError('Layer needs a qualified response preset')
        self._audio_pin(path,digest)
        source = {'source_path':'workshop-audio/'+digest+'.wav','source_sha256':digest,
                  'trim_frames':trim or [0,len(samples)],'crossfade_frames':crossfade,'gain_db':gain_db,'remove_dc':remove_dc}
        if layer == 'engine': state['profile'][layer] = source
        else:
            state['profile'][layer]['source'] = source
            state['profile'][layer]['provenance'] = 'User-supplied local PCM WAV; identity not independently attributed: '+Path(path).name
        state['imports'][digest] = {'original_path':str(Path(path).resolve()),'name':Path(path).name,
                                    'sha256':digest,'format':fmt,'rights':'Private user-supplied input; no redistribution implied'}
        self._audio_commit(state)
        return self.audio_inspect()

    def audio_assign(self, layer, other_layer):
        state = self.audio_state()
        available = dict(sources(state['profile']))
        if other_layer in available:source=available[other_layer]
        else:
            catalog=self.audio_catalog()
            if other_layer not in catalog:raise ValueError('Choose an existing pinned project source')
            source=catalog[other_layer]['source']
        self.audio_update(layer,source=source)

    def audio_catalog(self):
        state=self.audio_state();catalog={}
        baseline=json.loads((self.root/'audio-baseline.json').read_text())
        for profile in (baseline,*(p['profile'] for p in state['presets'].values()),state['profile']):
            for layer,source in sources(profile):
                digest=source['source_sha256'];catalog[digest]={'source':copy.deepcopy(source),
                    'name':state['imports'].get(digest,{}).get('name',Path(source['source_path']).name),'last_role':layer}
        return catalog

    def audio_reset(self, layer=None):
        state = self.audio_state(); baseline = self.root/'audio-baseline.json'
        if sha(baseline.read_bytes()) != state['baseline_sha256']: raise ValueError('Audio baseline changed')
        default = json.loads(baseline.read_text())
        if layer is None:
            state['profile'] = default; state['enabled'] = {k:True for k in LAYERS if k in default}
        else:
            if layer not in LAYERS: raise ValueError('Unknown layer')
            if layer in default: state['profile'][layer] = default[layer]; state['enabled'][layer] = True
            else: state['profile'].pop(layer,None); state['enabled'].pop(layer,None)
            if layer=='engine':state['profile']['stock_audio_profile_id']=default['stock_audio_profile_id']
        self._audio_commit(state)

    def audio_materialize(self):
        from .service import write_json, write_resource, plain_tree
        if not self.data.get('audio'): return
        state = self.data['audio']; baseline = self.root/'audio-baseline.json'
        if sha(baseline.read_bytes()) != state['baseline_sha256']: raise ValueError('Audio baseline changed')
        self.audio_compile(state)
        for _,source in sources(self.audio_effective(state)):
            target = plain_tree(self.working/source['source_path']); target.parent.mkdir(parents=True,exist_ok=True)
            write_resource(target,(self.root/'audio-sources'/(source['source_sha256']+'.wav')).read_bytes())
        write_json(self.working/'audio-profile.json',self.audio_effective(state))
        addon_path = self.working/'addon.json'; addon = json.loads(addon_path.read_text())
        if addon['audio']['stock_audio_profile_id'] != state['profile']['stock_audio_profile_id']:
            addon['audio']['stock_audio_profile_id'] = state['profile']['stock_audio_profile_id']
            write_json(addon_path,addon)

    def audio_save_preset(self, name):
        if not isinstance(name,str) or not name.strip() or len(name)>80: raise ValueError('Use a preset name of 1..80 characters')
        state = self.audio_state(); self.audio_compile(state)
        if name not in state['presets'] and len(state['presets'])>=64:raise ValueError('Project audio preset limit: 64')
        state['presets'][name] = {k:copy.deepcopy(state[k]) for k in ('profile','enabled','imports')}
        self._audio_commit(state)

    def audio_load_preset(self,name):
        state=self.audio_state()
        if name not in state['presets']:
            available=self.audio_available_presets()
            if name not in available:raise ValueError('Audio preset not found')
            from .service import WorkshopProject
            donor,original=available[name]
            return self.audio_transfer(WorkshopProject(donor),original)
        preset=copy.deepcopy(state['presets'][name])
        for key in ('physical_car_id','namespace'):preset['profile'][key]=state['profile'][key]
        state.update(preset);self._audio_commit(state)

    def audio_available_presets(self):
        """Discover sibling-version presets without editing that version's state."""
        state=self.audio_state();available={name:(str(self.root),name) for name in state['presets']}
        from .service import WorkshopProject
        for style,folder in self.data.get('style_versions',{}).items():
            if Path(folder).resolve()==self.root:continue
            other=WorkshopProject(folder)
            if other.data['identity']!=self.data['identity']:raise ValueError('Audio version link has a different vehicle identity')
            for name in other.data.get('audio',{}).get('presets',{}):available[name+' ('+style+')']=(str(other.root),name)
        return available

    def audio_transfer(self, other, name):
        """Explicit compatible preset import with destination namespace/CarID rebinding."""
        state=self.audio_state(); donor=other.audio_state()
        if name not in donor['presets']:raise ValueError('Donor preset not found')
        preset=copy.deepcopy(donor['presets'][name])
        for _,source in sources(preset['profile']):
            self._audio_pin(other.root/'audio-sources'/(source['source_sha256']+'.wav'),source['source_sha256'])
        for key in ('physical_car_id','namespace'):preset['profile'][key]=state['profile'][key]
        preset['imports']['preset_origin']={'project':str(other.root),'preset':name,'rebinding':'Explicit destination CarID/namespace; no native allocation identifiers'}
        state.update(preset);state['presets'][name]=copy.deepcopy(preset);self._audio_commit(state)

    def audio_inherit(self, other):
        """Carry audio authoring across newly generated visual versions only."""
        if not other.data.get('audio'):return
        state=self.audio_state();inherited=other.audio_state()
        for record in (inherited,*inherited['presets'].values()):
            for _,source in sources(record['profile']):self._audio_pin(other.root/'audio-sources'/(source['source_sha256']+'.wav'),source['source_sha256'])
            for key in ('namespace','physical_car_id'):record['profile'][key]=state['profile'][key]
        inherited['baseline_sha256']=state['baseline_sha256'];self._audio_commit(inherited)

    def audio_restore_author_baseline(self, author):
        """Reset only a NEW author snapshot before making a visual version."""
        if not self.data.get('audio'):return
        from .service import write_json
        baseline=self.root/'audio-baseline.json'
        if sha(baseline.read_bytes())!=self.data['audio']['baseline_sha256']:raise ValueError('Audio baseline changed')
        profile=json.loads(baseline.read_text());write_json(Path(author)/'audio-profile.json',profile)
        addon_path=Path(author)/'addon.json';addon=json.loads(addon_path.read_text())
        if addon['audio']['stock_audio_profile_id']!=profile['stock_audio_profile_id']:
            addon['audio']['stock_audio_profile_id']=profile['stock_audio_profile_id'];write_json(addon_path,addon)

    def audio_audition(self, exe, output, *, rpms=(900,2000,4000,6000,3000,900), load=1., gear=2, enabled=None, lift=True, seconds=.3, rev_limit=7000):
        """Original x86 engine DSP plus existing authored response simulation."""
        from vehicle_audio_audition import audition
        from vehicle_audio_layers import mix_sequence
        from .service import write_json
        output=Path(output)
        if output.exists():raise ValueError('Audition output already exists')
        resources,report=self.audio_compile();profile=self.audio_effective()
        engine,native=audition(Path(exe).read_bytes(),resources[report['resource_path']],
            stock_audio_profile_id=profile['stock_audio_profile_id'],rpms=list(rpms),seconds=seconds,rev_limit=rev_limit)
        selection=enabled if enabled is not None else {k:True for k in LAYERS}
        release=max(1,math.ceil(len(rpms)*.65))
        controls=[{'rpm':rpm,'load':0. if lift and index>=release else load,'gear':gear} for index,rpm in enumerate(rpms)]
        mixed,mixes=mix_sequence(engine,resources,report,controls,selection)
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_bytes(mixed);values,_=decode_pcm(mixed)
        diagnostics={'native':native,'mix':mixes,'sha256':sha(output.read_bytes()),
                     'peak_pcm16':max(abs(v) for v in values),'rms_pcm16':math.sqrt(sum(v*v for v in values)/len(values)),
                     'boundary':'Native DSP RPM steps and continuous authored spool/BOV/phase state with scripted signed-load release. No DirectSound/spatial/timing/gameplay qualification.'}
        write_json(output.with_suffix('.json'),diagnostics)
        return diagnostics
