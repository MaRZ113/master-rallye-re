"""Marker selection policy and provenance over the existing native writer."""
import copy,json
from ..addon_sdk.marker_colour import analyze,select


class MarkerAuthoring:
    def marker_context(self):
        selected=self.vehicle_state().get('marker_policy')
        return copy.deepcopy(selected)if selected else {'version':1,'historical':None,'policy':{'mode':'MANUAL','rgba':self.vehicle_state()['race_marker']}}

    def marker_recalculate(self):
        context=self.marker_context();settings=context.get('policy',{}).get('analysis_settings',{})
        if set(settings)-{'paint_draws','paint_textures','fallback_texture'}:raise ValueError('Unsupported colour analysis setting')
        # Recalculate is inspection only. It cannot overwrite a manual choice.
        self.materialize();return analyze(self.assets,**settings)

    def marker_select(self,mode,*,manual=None,contrast=False,analysis=None):
        context=self.marker_context();policy={'mode':mode,'contrast':contrast}
        settings=context.get('policy',{}).get('analysis_settings')
        if settings:policy['analysis_settings']=settings
        if mode=='MANUAL':policy['rgba']=manual
        # Recompute from current owned resources. Caller-supplied stale analysis
        # must never silently select colours from another mesh/texture revision.
        if mode.startswith('AUTO_'):
            current=self.marker_recalculate()
            if analysis is not None and current!=analysis:raise ValueError('Colour analysis source changed; recalculate')
            analysis=current
        value=select(policy,analysis,context.get('historical'))
        state=self.vehicle_state();state['race_marker']=value;state['marker_policy']={**context,'policy':policy,'selected_rgba':value}
        if analysis is not None:state['marker_policy']['analysis']=analysis
        self._vehicle_commit(state);return self.marker_inspect()

    def ai_inspect(self):
        from sdk_addon_ai import SUPPORTED
        addon=json.loads((self.working/'addon.json').read_text());cls=addon['vehicle_class']
        # Runtime class can differ from the technical author slot.
        history=self.working/'historical-identity.json'
        if history.exists():cls=json.loads(history.read_text()).get('runtime_class',cls)
        return {'vehicle_class':cls,'supported_modes':list(SUPPORTED[cls]),'eligibility':copy.deepcopy(self.vehicle_state()['ai_eligibility']),
                'boundary':'New native roster creation only; no saved participants rewritten. D3D8 owner confirmation pending.'}

    def ai_update(self,enabled):
        from sdk_addon_ai import validate_eligibility
        info=self.ai_inspect();state=self.vehicle_state();flags=copy.deepcopy(state['ai_eligibility'])
        if set(enabled)!=set(flags)or any(type(v)is not bool for v in enabled.values()):raise ValueError('AI modes require explicit booleans')
        boundaries={'quick_race':'new_race','rallye_cup':'new_cup','master_rallye':'new_competition','invitation':'new_invitation'}
        for mode,value in enabled.items():flags[mode]={'enabled':True,'boundary':boundaries.get(mode,'unsupported'),'pool':'ordinary_t3'if mode=='invitation'else'dynamic_class'}if value else{'enabled':False,'reason':'Explicit author exclusion; restricted/unqualified modes remain disabled.'}
        validate_eligibility(info['vehicle_class'],flags)
        state['ai_eligibility']=flags;self._vehicle_commit(state);return self.ai_inspect()
