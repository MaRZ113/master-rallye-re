"""Project-owned configuration/provenance for the optional read-only GT adapter."""
import copy,json,uuid
from pathlib import Path
from .audio import sha
from master_rallye.addon_sdk.gt_audio_source import GTSourceAdapter,LAB_COMMIT

class GTAudioAuthoring:
    def gt_audio_configure(self,config):
        from .service import write_json
        state=self.audio_state()
        adapter=GTSourceAdapter(config);config=copy.deepcopy(config)
        if not config.get('catalog'):
            path=self.root/'gt-catalogs'/(uuid.uuid4().hex+'.json');adapter.lab.private_output(path,(adapter.source.parent,));write_json(path,adapter.catalog);config['catalog']=str(path)
        digest=sha(Path(config['catalog']).read_bytes())
        state.setdefault('gt_sources',{})[config['game']]={'config':config,'catalog_sha256':digest,'lab_commit':LAB_COMMIT}
        self._audio_commit(state);return {'config':config,'catalog_sha256':digest,'counts':adapter.catalog.get('counts'),'boundary':adapter.catalog['boundary']}

    def gt_audio_adapter(self,game):
        state=self.audio_state();record=state.get('gt_sources',{}).get(game)
        if not record:raise ValueError('Configure an explicit local GT source first; ordinary audio import is independent')
        if sha(Path(record['config']['catalog']).read_bytes())!=record['catalog_sha256']:raise ValueError('Private catalog changed; explicitly load/reconfigure it')
        return GTSourceAdapter(record['config'])

    def gt_audio_export(self,game,bank,entry_id,*,selector=None,rate=24000,rate_mode='nominal',event_name=None,expected_bank_sha256=None):
        adapter=self.gt_audio_adapter(game)
        if selector:adapter.find_vehicle(selector)
        out=self.root/'gt-auditions'/(uuid.uuid4().hex+'.wav');evidence=adapter.export(bank,entry_id,out,rate=rate,rate_mode=rate_mode,event_name=event_name,expected_bank_sha256=expected_bank_sha256)
        return {'wav':str(out),'evidence':evidence,'boundary':'Private single source recording. Audition and review conversion before explicit assignment to any MR layer.'}
