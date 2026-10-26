"""Optional read-only adapter for qualified private GT Sound Bank Lab sources.

The Lab parsers remain the authority. No mesh-code guesses or fallback recordings.
"""
from __future__ import annotations
import copy,hashlib,json,sys
from pathlib import Path

LAB_COMMIT='1dc5b16f44aa327345a8e4529b5b10414bd09e74'
SCHEMA='gt-sound-bank-lab/1'

def lab_tools():
    path=str(Path(__file__).resolve().parents[3]/'tools')
    if path not in sys.path:sys.path.insert(0,path)
    import gt_sound_lab,gt3_sound_lab
    return gt_sound_lab,gt3_sound_lab

def digest(raw):return hashlib.sha256(raw).hexdigest()

class GTSourceAdapter:
    def __init__(self,config):
        from master_rallye.addon_sdk.audio_profile import _without_links
        if not isinstance(config,dict) or not {'game','source'}<=set(config) or set(config)-{'game','source','catalog','core'} or config['game'] not in ('gt3','gt4'):raise ValueError('Explicit GT3/GT4 source configuration required')
        self.config=copy.deepcopy(config);self.game=config['game'];self.source=_without_links(Path(config['source'])).resolve();self.core=Path(config['core']).resolve() if config.get('core') else None
        if not (self.source.is_dir() if self.game=='gt4' else self.source.is_file()):raise ValueError('Local GT source missing')
        if self.core:_without_links(self.core)
        self.lab,self.gt3=lab_tools();self._live=None;self.vehicle=None
        if config.get('catalog'):
            path=_without_links(Path(config['catalog']));raw=self.lab.read_bounded(path,64*1024*1024);self.catalog=json.loads(raw);self.catalog_sha256=digest(raw)
        else:
            self.catalog=self._live_catalog();self.catalog_sha256=digest(json.dumps(self.catalog,sort_keys=True).encode())
        if self.catalog.get('schema')!=SCHEMA or self.catalog.get('game')!=self.game:raise ValueError('Catalog schema/game mismatch')
        vehicles=self.catalog.get('vehicles');banks=self.catalog.get('banks')
        if not isinstance(vehicles,list) or not isinstance(banks,list) or len(vehicles)>10000 or len(banks)>10000:raise ValueError('Catalog collection budget')
        if len({v['vehicle_id'] for v in vehicles})!=len(vehicles) or len({b['bank_id'] for b in banks})!=len(banks):raise ValueError('Ambiguous catalog IDs')
        self.allowed={b['bank_id'] for b in banks}
        if self.game=='gt4':self.allowed.update(p.relative_to(self.source).as_posix() for p in (self.source/'sound_gt/sound').iterdir() if p.is_file() and p.suffix in ('.ins','.es')) if (self.source/'sound_gt/sound').is_dir() else None
        self._inspected={}

    def _live_catalog(self):
        if self._live is None:self._live=self.lab.gt4_catalog(self.source) if self.game=='gt4' else self.lab.normalize_gt3(self.gt3.catalog(self.source,include_banks=False))
        return self._live

    def find_vehicle(self,selector):
        try:chosen=self.lab.select_vehicle(self.catalog,selector)
        except ValueError as exc:raise ValueError(str(exc)+('; GT3 short mesh-code association is unqualified: select an exact CAR label' if self.game=='gt3' else '')) from exc
        live=self.lab.select_vehicle(self._live_catalog(),selector)
        keys=('vehicle_id','sound_id','banks','model_codes','source_rows','car_row_sha256','engine_row_sha256','default_native_bank_candidate','default_secondary_bank_category')
        if any(chosen.get(k)!=live.get(k) for k in keys):raise ValueError('Catalog/source association changed; regenerate the private catalog')
        self.vehicle=copy.deepcopy(live);return self.vehicle

    def inspect(self,bank):
        if bank not in self.allowed:raise ValueError('Bank not in configured local catalog/inventory')
        report=self.lab.inspect_gt4(self.source,bank,self.core if bank.startswith('carsound/') else None) if self.game=='gt4' else self.gt3.inspect_member(self.source,bank)
        ids=[str(e['entry_id']) for e in report['entries']]
        if len(ids)!=len(set(ids)):raise ValueError('Ambiguous source sample IDs')
        self._inspected[bank]=copy.deepcopy(report);return report

    def events(self):
        if self.game=='gt3' and self.core is None:raise ValueError('GT3 named-event attribution requires the qualified original CORE; opaque tokens are not sample identities')
        return self.lab.event_mapping(self.game,root=self.source if self.game=='gt4' else None,volume=self.source if self.game=='gt3' else None,core=self.core)

    def event_selection(self,name):
        mapping=self.events();matches=[e for e in mapping['events'] if e['name']==name]
        if len(matches)!=1:raise ValueError('Named event absent or ambiguous')
        event=matches[0]
        if self.game=='gt4':
            if event['status']!='STATIC_DIRECT_FIRST_SPLIT':raise ValueError(name+': '+event['status']+'; no substitute sample')
            bank='sound_gt/sound/'+event['bank_name'];report=self.inspect(bank);s=event['selection'];entries=[e for e in report['entries'] if (e['kind'],e['program'],e['split'])==(s['kind'],s['program'],s['split'])]
        else:
            if event.get('native_event_id') is None:raise ValueError('GT3 event lacks native enum association')
            lane=next(x for x in event['lanes'] if x['lane']=='primary');bank=lane['member'];report=self.inspect(bank);entries=[e for e in report['entries'] if e['entry_id']==lane['entry_id']]
        if len(entries)!=1 or entries[0].get('codec_status')!='PCM_VALID':raise ValueError('Named source entry is unsupported; no silent replacement')
        return {'bank_id':bank,'entry_id':str(entries[0]['entry_id']),'event':event,'boundary':mapping['boundary'],'inspection':report}

    def export(self,bank,entry_id,output,*,rate=24000,rate_mode='nominal',event_name=None,expected_bank_sha256=None):
        output=Path(output);self.lab.private_output(output,(self.source.parent,))
        if rate_mode not in ('nominal','native'):raise ValueError('Choose explicit nominal or qualified native pitch')
        previous=self._inspected.get(bank);report=self.inspect(bank)
        if expected_bank_sha256 is not None and expected_bank_sha256!=report['sha256']:raise ValueError('Bank changed since reviewed selection')
        if previous is not None and previous['sha256']!=report['sha256']:raise ValueError('Bank changed since inspection')
        entries=[e for e in report['entries'] if str(e['entry_id'])==str(entry_id)]
        if len(entries)!=1 or entries[0].get('codec_status')!='PCM_VALID':raise ValueError('Choose one PCM-valid sample; unsupported entries have no fallback')
        association=None
        if event_name:
            association=self.event_selection(event_name)
            if (association['bank_id'],association['entry_id'])!=(bank,str(entry_id)):raise ValueError('Selected sample does not match the named-event route')
        if self.game=='gt4':
            if rate_mode=='native' and (not self.core or report['format']!='ENGN'):raise ValueError('GT4 native anchor rate requires qualified CORE and ENGN; INST/event rate remains nominal')
            evidence=self.lab.export_gt4(self.source,bank,output,rate if rate_mode=='nominal' else None,self.core if rate_mode=='native' else None,str(entry_id))
        else:
            pitch=None
            if rate_mode=='native':
                if not self.core:raise ValueError('Qualified GT3 CORE required for native leaf pitch')
                if event_name:
                    evidence=self.gt3.export_event(self.source,self.core,event_name,output)
                else:
                    pitch=self.gt3.native_engn_pitch(self.source,self.core,bank,str(entry_id));rate=round(pitch['wave_rate_hz_at_48k_clock'])
                    evidence=self.gt3.export_member(self.source,bank,str(entry_id),output,rate);evidence['native_pitch']=pitch;evidence['playback_rate_provenance']='qualified original GT3 leaf pitch at nominal SPU2 48000Hz clock; no complete mixer'
            else:evidence=self.gt3.export_member(self.source,bank,str(entry_id),output,rate)
        evidence.update(adapter_schema=SCHEMA,lab_source_commit=LAB_COMMIT,catalog_sha256=self.catalog_sha256,game=self.game,bank_id=bank,vehicle_association=copy.deepcopy(self.vehicle),static_native_event={k:v for k,v in association.items() if k!='inspection'} if association else None,
                        source_bank=report.get('source',str(self.source)),source_bank_sha256=report['sha256'],selected_entry=copy.deepcopy(entries[0]),rate_mode=rate_mode,authentic_effect_identity=None,
                        adaptation='Explicit single recording / engine-band MR approximation. No original GT engine orchestra, ADSR/LFO/spatial mix or gameplay parity.',offset_semantics='sample_file_offset is within decoded bank/member; GT3 RoFS stored/compressed member location is separate and must not be added to it')
        folder=Path(self.lab.__file__).parent
        evidence['parser_sha256']={name:digest((folder/name).read_bytes()) for name in ('gt_sound_lab.py','gt3_sound_lab.py','gt_sound_jam.py','gt4_audio_extract.py')}
        evidence['source_core_identity']=self.lab.file_identity(self.core) if self.core else None
        output.with_suffix('.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8');return evidence
