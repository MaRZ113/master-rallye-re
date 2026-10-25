"""Geometry-neighbor reflection warnings, without inferring paint from colour/names."""
from collections import defaultdict
import math
from master_rallye.dx import parse_dx_bytes
from master_rallye.topology_writer import source_geometry


def audit(data,*,eligible_draws=None,tolerance_m=0.0001):
    if not math.isfinite(tolerance_m) or not 1e-7<=tolerance_m<=.01:raise ValueError('invalid adjacency tolerance')
    model=parse_dx_bytes(data)
    if not model.diagnostics.validated:raise ValueError('invalid DX geometry')
    ids={d.draw_index for d in model.physical_draws}
    eligible=ids if eligible_draws is None else set(eligible_draws)
    if not eligible<=ids:raise ValueError('continuity selection contains absent draws')
    geometries=source_geometry(model);edges=defaultdict(set);states={};areas={}
    for draw in model.physical_draws:
        i=draw.draw_index;g=geometries[i];states[i]=bool(draw.unknown_0x24&4)
        area=0.
        for tri in g.triangles:
            ps=[g.vertices[k].position for k in tri];u=[ps[1][k]-ps[0][k] for k in range(3)];v=[ps[2][k]-ps[0][k] for k in range(3)]
            area+=.5*math.sqrt(sum(x*x for x in (u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])))
            for a,b in ((ps[0],ps[1]),(ps[1],ps[2]),(ps[2],ps[0])):
                if math.dist(a,b)<=tolerance_m:continue
                key=tuple(sorted(tuple(round(x/tolerance_m) for x in p) for p in (a,b)))
                edges[key].add(i)
        areas[i]=area
    pairs=defaultdict(int)
    for owners in edges.values():
        owners=sorted(owners&eligible)
        for n,a in enumerate(owners):
            for b in owners[n+1:]:pairs[a,b]+=1
    warnings=[{'draws':[a,b],'shared_edges':count,'environment_flags':[states[a],states[b]],
               'classification':'neighboring reflection mismatch; inspect intentional material boundary before any repair'}
              for (a,b),count in sorted(pairs.items()) if states[a]!=states[b]]
    return {'status':'DIAGNOSTIC_NOT_AUTOMATIC_MATERIAL_CLASSIFICATION','tolerance_m':tolerance_m,
            'scope':'all draws; includes intentional glass/trim boundaries' if eligible_draws is None else 'explicit editable eligible draw selection',
            'eligible_draws':sorted(eligible),'neighbor_pairs':len(pairs),'warnings':warnings,
            'reflected_area_m2':sum(v for i,v in areas.items() if i in eligible and states[i]),
            'unreflected_area_m2':sum(v for i,v in areas.items() if i in eligible and not states[i]),
            'boundary':'Quantized shared-edge topology is a suspicion diagnostic, not proof of paint identity or live reflection brightness.'}
