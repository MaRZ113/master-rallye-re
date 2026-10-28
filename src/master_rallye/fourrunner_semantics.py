"""Reviewed 4Runner apertures; MR interpretations, not source renderer flags."""
from dataclasses import replace
from pathlib import Path
import hashlib
from .glass_authoring import subset
from .semantic_aperture import partition,compose_ledger
from .topology_writer import DrawGeometry


def merge(parts):
    vertices=[];triangles=[]
    for part in parts:
        start=len(vertices);vertices.extend(part.geometry.vertices)
        triangles.extend(tuple(start+i for i in t)for t in part.geometry.triangles)
    return replace(parts[0],geometry=DrawGeometry(tuple(vertices),tuple(triangles)))


def author_apertures(result):
    """Split explicit source nodes before native draw numbering is assigned.

    The 512px original body atlas supplies the visible rubber-frame boundary.
    GlassI has its own interior atlas coordinates, so it uses the same boundary
    projected into Y/Z by the exterior mesh's evidenced affine UV mapping.
    No global alpha, two-sided flag or position offset is used.
    """
    rows={r['node_id']:r['draw_index']for r in result['report']['body_draws']}
    # Owner-tested native pilot copy and earlier neutral delivery differ only
    # in metadata.implementation_sha256.universal_vehicle_scene.py. Arrays,
    # original resource hashes and all texture/geometry sidecars are identical.
    if result['report']['source_scene_sha256']not in (
            '05cb2b9db5b3c103cd623b8c1282099ac9f1f1f93593ad95d8243003f41e33dd',
            '246cae8bbe646640b50b0a9e228a2f0c7ec49e13c7d13837ba756cb68d05ad3d'):
        raise ValueError('Semantic apertures require the exact reviewed source scene')
    if any(k not in rows for k in ('node-mesh-000','node-mesh-010','node-mesh-011')):
        raise ValueError('Qualified aperture source nodes missing')
    parts=list(result['body_parts']);panes={};records={};cuts=[]
    # Keep accepted windshield geometry byte-for-byte in attribute space.
    wind={'node-mesh-010':list(range(7,19)),'node-mesh-011':list(range(16,32))}
    selected={};front=[]
    for node,ids in wind.items():
        draw=rows[node];g=parts[draw].geometry
        if len(g.triangles)!=(40 if node.endswith('010')else 70):raise ValueError('Qualified pane topology changed')
        front.append(replace(parts[draw],geometry=subset(g,ids)))
        selected[draw]=set(ids)
    panes['screenfront']=merge(front);records['screenfront']=wind
    polygon_px=[(174.,194.),(270.,194.),(270.,145.),(226.,146.),(209.,151.),(193.,162.),(174.,179.)]
    exterior=parts[rows['node-mesh-011']].geometry
    # Solve exact source UV -> projected position affine map using three
    # original, noncollinear exterior corners. Keep this evidence in the ledger.
    anchors=[exterior.vertices[i]for i in exterior.triangles[6]]
    p0,p1,p2=[tuple(x*512 for x in v.uvs[0])for v in anchors]
    u=(p1[0]-p0[0],p1[1]-p0[1]);v=(p2[0]-p0[0],p2[1]-p0[1]);det=u[0]*v[1]-u[1]*v[0]
    if abs(det)<1e-8:raise ValueError('Ambiguous aperture UV evidence')
    def position(p):
        d=(p[0]-p0[0],p[1]-p0[1]);a=(d[0]*v[1]-d[1]*v[0])/det;b=(u[0]*d[1]-u[1]*d[0])/det
        return tuple(anchors[0].position[k]+a*(anchors[1].position[k]-anchors[0].position[k])+b*(anchors[2].position[k]-anchors[0].position[k])for k in (2,1))
    yz=[position(p)for p in polygon_px]
    sides={
        'screenleft':{'node-mesh-010':[*range(21,26),38], 'node-mesh-011':[*range(0,16),55,56,57]},
        'screenright':{'node-mesh-010':[*range(2,7),26], 'node-mesh-011':list(range(32,51))}}
    # Work on the original index space; partition passes all unselected
    # triangles through, including the windshield until its final removal.
    for label,nodes in sides.items():
        chosen=[]
        for node,ids in nodes.items():
            draw=rows[node];part=parts[draw]
            inside,outside,ledger=partition(part.geometry,ids,yz,axes=(2,1))
            if not inside.triangles:raise ValueError('Qualified side aperture became empty')
            chosen.append(replace(part,geometry=inside))
            # Store outside pieces by source ID; later cuts must still address
            # original IDs, so the disjoint left/right masks are accumulated.
            cuts.append({'role':label,'node_id':node,'source_triangle_ids':ids,'ledger':ledger})
        panes[label]=merge(chosen);records[label]=nodes
    # Rebuild opaque glass shells using their source-indexed outside ledgers.
    for node in ('node-mesh-010','node-mesh-011'):
        draw=rows[node];original=parts[draw];opaque=[];handled=set(selected[draw])
        for cut in cuts:
            if cut['node_id']!=node:continue
            ids=cut['source_triangle_ids'];handled.update(ids)
            # Local subset keeps a small bounded operation; convert cut IDs
            # back to source IDs in the stored full ledger above.
            _,outside,_=partition(subset(original.geometry,ids),range(len(ids)),yz,axes=(2,1))
            if outside.triangles:opaque.append(replace(original,geometry=outside))
        rest=sorted(set(range(len(original.geometry.triangles)))-handled)
        if rest:opaque.append(replace(original,geometry=subset(original.geometry,rest)))
        parts[draw]=merge(opaque)
    # Lamps: the old auxiliary corner footprint is a broad panel, not a lens.
    # Split its red lens texels from the bumper/paint BEFORE assigning native
    # state draw IDs. Clear indicator/reverse areas remain ordinary opaque.
    body=parts[rows['node-mesh-000']];geometry=body.geometry;lamp_parts=[];lamp_cuts=[]
    original_ids={176,177,178,179,254,255,256,257,258,323,324,325,304,291,292}
    # Three separate atlas islands: side (shared L/R), rear-left, rear-right.
    masks=[[(224.5,375.),(242.,375.),(242.,387.),(224.5,387.)],
           [(347.,3.),(360.,3.),(360.,14.),(347.,14.)],
           [(347.,166.),(360.,166.),(360.,177.),(347.,177.)]]
    mapping=[{'source_triangle':i,'barycentric':[(1.,0.,0.),(0.,1.,0.),(0.,0.,1.)]}for i in range(len(geometry.triangles))]
    for pixels in masks:
        ids=[i for i,source in enumerate(mapping)if source['source_triangle']in original_ids]
        inside,outside,ledger=partition(geometry,ids,[tuple(x/512 for x in p)for p in pixels],uv_layer=0)
        for side in ('inside','outside'):
            ledger[side]=compose_ledger(ledger[side],mapping)
        if inside.triangles:lamp_parts.append(replace(body,geometry=inside))
        lamp_cuts.append(ledger);mapping=ledger['outside'];geometry=outside
    if not lamp_parts:raise ValueError('Qualified rear lens masks empty')
    parts[rows['node-mesh-000']]=replace(body,geometry=geometry)
    indices={}
    for label,pane in panes.items():
        g=replace(pane.geometry,vertices=tuple(replace(v,color=v.color[:3]+bytes([89]))for v in pane.geometry.vertices))
        indices[label]=len(parts);parts.append(replace(pane,geometry=g,alpha=True,alpha_test=False,environment=False))
    lamp_index=len(parts);parts.append(merge(lamp_parts))
    report={'schema':'qualified-semantic-apertures/1','interpretation':'explicit MR authoring',
        'evidence':'Exact qualified scene nodes and source texture atlas512 rubber window frame / red lower rear-lens islands; authored convex boundary lies inside the visible frame.',
        'source_scene_sha256':result['report'].get('source_scene_sha256'),
        'side_window_polygon_atlas_pixels':polygon_px,'side_window_polygon_yz_m':yz,
        'side_cuts':cuts,'lamp_cuts':lamp_cuts,'lamp_source_body_triangles':sorted(original_ids),
        'body_partition_ledger':mapping,
        'unknowns':['Original glass/reflection/lighting semantics remain unresolved; TIFF additional sample is not alpha.',
                    'Rear glazing unchanged; no invented rear damage controller.',
                    'Original suspension/axle animation not reconstructed; no physics or hub changes.'],
        'positions_moved':False,'windshield_source_selection_unchanged':True}
    report['implementation_sha256']={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
        for name in ('semantic_aperture.py','fourrunner_semantics.py')}
    return parts,indices,lamp_index,records,report
