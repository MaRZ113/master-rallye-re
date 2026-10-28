"""Explicit convex semantic masks on a qualified scene, before native authoring.

Masks are authoring evidence, never inferred from an unknown source material.
Both sides of every cut retain barycentric source-triangle provenance. UVs,
normals and colour are interpolated; positions are never moved to fit a mask.
"""
from dataclasses import replace
import math
from .topology_writer import DrawGeometry

MAX_TRIANGLES = 100000
MAX_OUTPUT_TRIANGLES = 200000
EPS = 1e-10


def compose_ledger(rows, parents):
    """Carry cut provenance through another partition without renumber drift."""
    result=[]
    for row in rows:
        parent=parents[row['source_triangle']]
        result.append({'source_triangle':parent['source_triangle'],
            'barycentric':[tuple(sum(w[j]*parent['barycentric'][j][k]for j in range(3))for k in range(3))for w in row['barycentric']]})
    return result


def partition(geometry, triangle_ids, polygon, *, uv_layer=None, axes=None):
    """Return inside/outside geometry and an exact source-triangle cut ledger.

    Only explicitly nominated triangles may be split. All other triangles pass
    through outside. Polygon must be strictly convex, finite and nondegenerate.
    Projection is either an explicit UV layer or two explicit position axes.
    """
    if (uv_layer is None) == (axes is None):
        raise ValueError('Exactly one semantic projection required')
    if axes is not None and (len(axes)!=2 or len(set(axes))!=2 or any(type(a)is not int or a not in (0,1,2)for a in axes)):
        raise ValueError('Invalid semantic position axes')
    if uv_layer is not None and (type(uv_layer)is not int or uv_layer<0):
        raise ValueError('Invalid semantic UV layer')
    if not 3<=len(polygon)<=32 or any(len(p)!=2 or any(not math.isfinite(x)for x in p)for p in polygon):
        raise ValueError('Invalid semantic polygon')
    cross=lambda a,b,c:(b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0])
    turns=[cross(polygon[i-1],polygon[i],polygon[(i+1)%len(polygon)])for i in range(len(polygon))]
    if not(all(x>EPS for x in turns)or all(x<-EPS for x in turns)):
        raise ValueError('Semantic polygon must be strictly convex')
    sign=1 if turns[0]>0 else -1
    if any(sign*((b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])) < -EPS
           for i,a in enumerate(polygon)for b in [polygon[(i+1)%len(polygon)]]for p in polygon):
        raise ValueError('Semantic polygon is self-intersecting or nonconvex')
    ids=list(triangle_ids)
    if len(ids)!=len(set(ids))or any(type(i)is not int or not 0<=i<len(geometry.triangles)for i in ids):
        raise ValueError('Invalid semantic source triangle IDs')
    if len(geometry.triangles)>MAX_TRIANGLES:raise ValueError('Semantic input budget exceeded')
    selected=set(ids);vertices=[[],[]];triangles=[[],[]];ledger=[[],[]]
    def project(v):
        return v.uvs[uv_layer]if uv_layer is not None else tuple(v.position[a]for a in axes)
    for v in geometry.vertices:
        fields=(*v.position,*v.normal,*[x for pair in v.uvs for x in pair])
        if any(not math.isfinite(x)for x in fields):raise ValueError('Nonfinite semantic vertex')
        if uv_layer is not None and len(v.uvs)<=uv_layer:raise ValueError('Missing semantic UV layer')
    def emit(poly,side,index,source):
        for n in range(1,len(poly)-1):
            bary=[poly[0],poly[n],poly[n+1]]
            out=[]
            for weights in bary:
                def blend(values):return tuple(sum(weights[j]*values[j][k]for j in range(3))for k in range(len(values[0])))
                normal=blend([v.normal for v in source]);length=math.hypot(*normal)
                if length<EPS:raise ValueError('Ambiguous interpolated semantic normal')
                exact=next((source[k]for k in range(3)if weights[k]==1.),None)
                out.append(exact or replace(source[0],position=blend([v.position for v in source]),
                    normal=tuple(x/length for x in normal),color=bytes(round(x)for x in blend([v.color for v in source])),
                    uvs=tuple(blend([v.uvs[layer]for v in source])for layer in range(len(source[0].uvs))),
                    source_vertex_id=None,parent_source_vertex_id=None))
            a,b,c=[v.position for v in out];u=[b[k]-a[k]for k in range(3)];v=[c[k]-a[k]for k in range(3)]
            area=math.hypot(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
            if area<EPS:continue
            start=len(vertices[side]);vertices[side].extend(out);triangles[side].append((start,start+1,start+2))
            ledger[side].append({'source_triangle':index,'barycentric':bary})
            if sum(map(len,triangles))>MAX_OUTPUT_TRIANGLES:raise ValueError('Semantic output budget exceeded')
    for index,tri in enumerate(geometry.triangles):
        if len(tri)!=3 or any(type(v)is not int or not 0<=v<len(geometry.vertices)for v in tri):raise ValueError('Invalid semantic geometry index')
        source=[geometry.vertices[v]for v in tri]
        if len({len(v.uvs)for v in source})!=1:raise ValueError('Mismatched semantic UV channels')
        poly=[(1.,0.,0.),(0.,1.,0.),(0.,0.,1.)]
        if index not in selected:emit(poly,1,index,source);continue
        points=[project(v)for v in source]
        for edge,a in enumerate(polygon):
            b=polygon[(edge+1)%len(polygon)]
            def distance(w):
                p=[sum(w[j]*points[j][k]for j in range(3))for k in range(2)]
                return sign*((b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0]))
            inside=[];outside=[]
            for i,w in enumerate(poly):
                previous=poly[i-1];d=distance(w);pd=distance(previous)
                if (d>=0)!=(pd>=0):
                    t=pd/(pd-d);hit=tuple(previous[k]+t*(w[k]-previous[k])for k in range(3))
                    inside.append(hit);outside.append(hit)
                (inside if d>=0 else outside).append(w)
            emit(outside,1,index,source);poly=inside
            if not poly:break
        emit(poly,0,index,source)
    return (DrawGeometry(tuple(vertices[0]),tuple(triangles[0])),
            DrawGeometry(tuple(vertices[1]),tuple(triangles[1])),
            {'inside':ledger[0],'outside':ledger[1],'projection':{'uv_layer':uv_layer,'axes':axes},'polygon':polygon})
