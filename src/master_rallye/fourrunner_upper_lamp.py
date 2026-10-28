"""Separate opt-in upper brake strip on the qualified original spoiler surface.

Only the original Body595/596 footprint is eligible. Existing lower lamps and
all native controllers are reused without modifying the accepted glass policy.
"""
from dataclasses import replace
from .fourrunner_semantics import merge
from .semantic_aperture import partition,compose_ledger

PIXELS=((50.,451.),(70.,451.),(70.,453.),(50.,453.))


def author(parts,lamp_index,semantic_report,*,enabled=False):
    if type(enabled)is not bool:raise ValueError('Upper brake lamp requires an explicit boolean')
    if not enabled:return list(parts),{'enabled':False,'qualification':'NOT REQUESTED'}
    if semantic_report.get('source_scene_sha256')not in (
            '05cb2b9db5b3c103cd623b8c1282099ac9f1f1f93593ad95d8243003f41e33dd',
            '246cae8bbe646640b50b0a9e228a2f0c7ec49e13c7d13837ba756cb68d05ad3d'):
        raise ValueError('Upper brake lamp requires the exact qualified source scene')
    parts=list(parts);body=parts[0];mapping=semantic_report['body_partition_ledger']
    if len(mapping)!=len(body.geometry.triangles):raise ValueError('Upper lamp source ledger mismatch')
    ids=[i for i,row in enumerate(mapping)if row['source_triangle']in (595,596)]
    if {mapping[i]['source_triangle']for i in ids}!={595,596}:raise ValueError('Original upper spoiler faces missing')
    inside,outside,ledger=partition(body.geometry,ids,[tuple(x/512 for x in p)for p in PIXELS],uv_layer=0)
    if not inside.triangles:raise ValueError('Original upper red strip is empty')
    for v in inside.vertices:
        x,y,z=v.position
        if not(abs(x)<.12 and 1.30<y<1.34 and -2.12<z<-2.08):
            raise ValueError('Upper lamp geometry escapes qualified high rear strip')
    for side in ('inside','outside'):ledger[side]=compose_ledger(ledger[side],mapping)
    before=parts[lamp_index]
    parts[0]=replace(body,geometry=outside)
    parts[lamp_index]=merge([before,replace(body,geometry=inside)])
    return parts,{'schema':'fourrunner-upper-brake/1','enabled':True,
        'qualification':'PASS_BOUNDED_AUTHORING_D3D8_PENDING_OWNER',
        'source_scene_sha256':semantic_report['source_scene_sha256'],
        'source_node_id':'node-mesh-000','source_mesh_id':'mesh-000',
        'source_triangle_ids':[595,596],'source_atlas_size':[512,512],
        'atlas_polygon_pixels':PIXELS,'source_ledger':ledger,
        'bounds_m':[[f(v.position[k]for v in inside.vertices)for k in range(3)]for f in (min,max)],
        'triangles':len(inside.triangles),'accepted_lower_triangles':len(before.geometry.triangles),
        'native_binding':'Additional original lens footprint merged after accepted lower triangles into existing blight OFF/ON parts; no new controller or enlarged glow.',
        'evidence':'Original Body595/596 form the upper rear spoiler sheet; this small red inset lies within both its3D plane and the original visible red atlas strip. It is an explicit MR brake role, not recovered Evo2 runtime lamp semantics.'}
