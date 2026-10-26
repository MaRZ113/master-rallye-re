"""Bounded radial dust-cover reduction in explicitly approved source draws.

The existing contour, centre and their full attributes survive. This is a
documented shape approximation, never general-purpose automatic decimation.
"""


from .topology_writer import DrawGeometry


def simplify_radial_cover(geometry, *, expected_boundary=16, max_relief_m=.04):
    """Explicitly approved convex dust-cover approximation, never an auto repair.

    Retain the exact outer contour and original central attributes. Refuse
    seams, multiple boundaries, folded rings and non-radial texture ownership.
    The discarded intermediate curvature is recorded as an approximation.
    """
    from collections import Counter
    import numpy as np
    if not 8<=expected_boundary<=64 or not 0<max_relief_m<=.04:
        raise ValueError('Unqualified radial cover limits')
    vertices=[];lookup={};remap={}
    for i,v in enumerate(geometry.vertices):
        key=(v.position,v.normal,v.color,v.uvs)
        if key not in lookup:lookup[key]=len(vertices);vertices.append(v)
        remap[i]=lookup[key]
    triangles=[tuple(remap[i] for i in t) for t in geometry.triangles]
    edges=Counter(tuple(sorted((t[j],t[(j+1)%3]))) for t in triangles for j in range(3))
    if any(n>2 for n in edges.values()):raise ValueError('Non-manifold cover')
    boundary={e for e,n in edges.items() if n==1};links={}
    for t in triangles:
        for j in range(3):
            a,b=t[j],t[(j+1)%3]
            if tuple(sorted((a,b))) in boundary:
                if a in links:raise ValueError('Cover boundary seam')
                links[a]=b
    if len(links)!=expected_boundary:raise ValueError('Cover outer contour differs from recipe')
    ring=[min(links)]
    while links[ring[-1]] not in ring:ring.append(links[ring[-1]])
    if len(ring)!=len(links) or links[ring[-1]]!=ring[0]:raise ValueError('Multiple cover boundaries')
    p=np.array([v.position for v in vertices]);bp=p[ring];mean=bp.mean(axis=0)
    _,_,axes=np.linalg.svd(bp-mean,full_matrices=False);normal=axes[-1]
    if np.max(np.abs((bp-mean)@normal))>.00025:raise ValueError('Nonplanar outer contour exceeds quantized contour tolerance')
    interior=sorted(set(range(len(vertices)))-set(ring))
    if len(interior)!=expected_boundary+1:raise ValueError('Expected one intermediate ring and centre')
    center=min(interior,key=lambda i:float(np.linalg.norm((p[i]-mean)@axes[:2].T)))
    if np.linalg.norm((p[center]-mean)@axes[:2].T)>.005:raise ValueError('No qualified radial centre')
    relief=float(np.max(np.abs((p-mean)@normal)))
    if relief>max_relief_m:raise ValueError('Cover relief exceeds explicit approximation bound')
    # All source UVs must be affine over the cover plane: no hidden lettering
    # or islands can be moved by dropping the intermediate ring.
    if any(len(v.uvs)!=1 for v in vertices):raise ValueError('Cover requires one qualified UV channel')
    matrix=np.column_stack(((p-mean)@axes[:2].T,np.ones(len(p))))
    uv=np.array([v.uvs[0]for v in vertices])
    uv_error=float(np.max(np.abs(matrix@np.linalg.lstsq(matrix,uv,rcond=None)[0]-uv)))
    if uv_error>.005:
        raise ValueError('Non-affine cover UV mapping')
    output=[vertices[center]]+[vertices[i]for i in ring]
    ts=tuple((0,1+j,1+(j+1)%len(ring))for j in range(len(ring)))
    for t in triangles:
        if np.dot(np.cross(p[t[1]]-p[t[0]],p[t[2]]-p[t[0]]),normal)*np.dot(np.cross(bp[1]-p[center],bp[0]-p[center]),normal)>=0:
            raise ValueError('Folded or inconsistent cover winding')
    return DrawGeometry(tuple(output),ts),{'method':'approved radial dust-cover approximation','triangles_before':len(triangles),'triangles_after':len(ts),'boundary_vertices':len(ring),'boundary_preserved':True,'central_attributes_preserved':True,'discarded_relief_bound_m':relief,'source_uv_affine_residual':uv_error,'limits':{'contour_planarity_m':.00025,'centre_off_axis_m':.005,'uv_affine_residual':.005},'approximation':'Intermediate convex ring removed; original rim and centre retained. Not a source reconstruction.'}
