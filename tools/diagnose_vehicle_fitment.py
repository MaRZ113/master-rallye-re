"""Compare frozen visual wheels, native attachment data and qualified source hubs.

Never edits a model or fits collision automatically. Geometry bounds include
decorations; they are not a justified convex-hull fitting target.
"""
import argparse,hashlib,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from master_rallye.dx import parse_dx_bytes
from master_rallye.vehicle_config_analysis import parse_vehicle_config_bytes
from master_rallye.addon_sdk.physics_model import wheel_attachments,effective_setup,suspension_summary


def source_rest_datum(rows):
    """Derive axle ride-reference deltas from qualified rest hubs, never sag.

    Native attachment Y=-RideHeight; additive reference r moves it by -r.
    Thus r=current_Y-source_Y. This is an authored rest-datum candidate only;
    it is not automatically applied and does not infer loaded suspension pose.
    """
    result={}
    if len(rows)!=4:raise ValueError('four matched hub rows required')
    for axle in ('Front','Rear'):
        selected=[r for r in rows if r['axle']==axle]
        if len(selected)!=2 or {r['positive_x'] for r in selected}!={True,False}:raise ValueError('unambiguous left/right axle required')
        deltas=[r['native_attachment'][1]-r['source_reference_hub'][1] for r in selected]
        if any(not math.isfinite(v) or abs(v)>.5 for v in deltas) or abs(deltas[0]-deltas[1])>1e-5:raise ValueError('unsupported asymmetric/excessive ride datum')
        result[axle]=sum(deltas)/2
    return result

def diagnose(assets,vehicles,family,reference,*,physics_profile=None,modifications=None,saved_state=None,player=1):
    raw=(assets/'car.dx').read_bytes();body=parse_dx_bytes(raw);wheelraw=(assets/'wheel.dx').read_bytes();wheel=parse_dx_bytes(wheelraw)
    if not body.diagnostics.validated or not wheel.diagnostics.validated:raise ValueError('invalid DX')
    fields=parse_vehicle_config_bytes(vehicles.read_bytes(),build='retail-2001-verified').families[family]
    definition=json.loads(physics_profile.read_text()) if physics_profile else {}
    mods=parse_vehicle_config_bytes(modifications.read_bytes(),build='retail-2001-verified').families[family] if modifications else {}
    from vehicle_physics_native import runtime_reference
    fields,setup=effective_setup(fields,mods,family=family,player=player,saved_state=saved_state.read_bytes() if saved_state else None,reference=runtime_reference(definition))
    setup['reference_binding']=definition.get('ride_height_reference_binding','legacy_inactive_or_absent')
    profile=wheel_attachments(fields);ref=json.loads(reference.read_text());source=ref.get('race_wheel_instances',[])
    if len(source)!=4 or not ref.get('provenance'):raise ValueError('four source-qualified reference instances are required')
    radius=max(math.hypot(p[1],p[2]) for p in wheel.vertices.positions);rows=[]
    for item in profile['race_wheel_instances']:
        p=item['translation'];axle='Front' if p[2]>0 else 'Rear';candidates=[x for x in source if x['translation'][0]*p[0]>0 and x['translation'][2]*p[2]>0]
        if len(candidates)!=1:raise ValueError('reference hubs cannot be associated unambiguously')
        q=candidates[0]['translation'];physical_radius=float(fields['Dimensions/WheelRadius'+axle]['value'])
        rows.append({'axle':axle,'positive_x':p[0]>0,'native_attachment':p,'source_reference_hub':q,'attachment_minus_source':[p[k]-q[k] for k in range(3)],'distance_m':math.dist(p,q),'visual_radial_envelope_m':radius,'physical_radius_m':physical_radius,'radius_difference_m':physical_radius-radius})
    hull=body.collision.convex_hull
    bounds=lambda ps:[[f(p[k] for p in ps) for k in range(3)] for f in (min,max)]
    collision=bounds(hull.representation_a.geometry_a.vertices) if hull and hasattr(hull,'representation_a') else None
    ground=[]
    for row in rows[::2]:
        origin=row['physical_radius_m']-row['native_attachment'][1]
        ground.append({'axle':row['axle'],'zero_jounce_body_origin_above_plane_m':origin,
                       'visual_tyre_bottom_above_plane_m':row['physical_radius_m']-row['visual_radial_envelope_m'],
                       'collision_bottom_above_plane_m':origin+collision[0][1] if collision else None,
                       'body_vertex_bottom_above_plane_m':origin+min(p[1] for p in body.vertices.positions)})
    return {'status':'PASS_OFFLINE_FITMENT_MEASUREMENTS','family':family,'model_sha256':hashlib.sha256(raw).hexdigest(),'wheel_sha256':hashlib.sha256(wheelraw).hexdigest(),'physics_sha256':hashlib.sha256(vehicles.read_bytes()).hexdigest(),'reference_sha256':hashlib.sha256(reference.read_bytes()).hexdigest(),'reference_provenance':ref['provenance'],'effective_setup':setup,'native_symmetric_force_diagnostic':suspension_summary(fields),'rows':rows,'source_rest_datum_reference_delta_m':source_rest_datum(rows),'source_rest_datum_boundary':'additive delta from this exact effective setup; not an automatic edit or universal height, and not a loaded equilibrium result','zero_jounce_flat_plane_diagnostic':ground,'collision_aabb_m':collision,'body_render_bounds_m':bounds(body.vertices.positions),'runtime_qualified':False,'boundary':'native initialization attachments versus source rest assembly, with optional saved setup/reference; no whole-vehicle equilibrium, contact, jump or landing simulation','collision_note':'explicit core-shell affine fit' if definition.get('collision_fit') else 'retained donor tag101; decorative bounds are not an automatic hull target'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--assets',type=Path,required=True);p.add_argument('--vehicles',type=Path,required=True);p.add_argument('--family',required=True);p.add_argument('--reference-profile',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--physics-profile',type=Path);p.add_argument('--modifications',type=Path);p.add_argument('--player-state',type=Path);p.add_argument('--player',type=int,choices=[1,2],default=1);a=p.parse_args()
    r=diagnose(a.assets,a.vehicles,a.family,a.reference_profile,physics_profile=a.physics_profile,modifications=a.modifications,saved_state=a.player_state,player=a.player);a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'max_attachment_error_m':max(x['distance_m'] for x in r['rows']),'max_radius_error_m':max(abs(x['radius_difference_m']) for x in r['rows'])}))
