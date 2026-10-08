"""Regenerate bounded AMBIENT1 diagnostics and compact authored applicability metadata.

Uses CDELTA1's existing 24-object selection; does not repeat course pairing.
Coordinates, raw XML, observer inputs and SVGs stay in ignored data/ambient1.
"""
import argparse
import json
from pathlib import Path
import struct

import spline_runtime as s

CASES = [('ITALY3','barge'), ('TURKEYW','barge'), ('FRANCE1','boat1'),
         ('FRANCEM','zeppelin'), ('SPAINS2','boat1'), ('SPAINS2','boat5')]


def build(directory):
    corpus = s.Corpus(directory)
    baseline = json.loads((s.ROOT/'cdelta1'/'ambient-evidence.json').read_text())
    expected = {r['source']:r['decoded_sha256'] for r in baseline['source_hashes']}
    applicability = []
    for r in baseline['splines']:
        course = r['source'].rsplit('\\',1)[-1].removesuffix('.XML')
        identity, points, config = corpus.case(course,r['egg'])
        if identity['decoded_sha256'] != expected[r['source']]:
            raise s.ContractError('CDELTA1 source provenance changed')
        if len(points) != r['marker_count'] or identity['model'] != r['model']:
            raise s.ContractError('CDELTA1 authored selection changed')
        path = s.PathState(points,config)
        applicability.append({'source':r['source'],'egg':r['egg'],
                              'decoded_sha256':identity['decoded_sha256'],
                              'route_sha256':identity['route_sha256'],
                              'marker_list':identity['marker_list'],
                              'markers':len(points),'model':identity['model'],
                              'const_speed':config.const_speed,'loop':config.loop,
                              'trigger':config.trigger,'banking':config.banking,
                              'samples':config.samples,'duration':path.duration,
                              'status':'STRUCTURALLY_APPLICABLE',
                              'evidence':'CONFIRMED_BY_BOTH',
                              'runtime_execution':'UNKNOWN'})
    rows = []
    dest = s.ROOT/'data'/'ambient1'/'diagnostics'
    dest.mkdir(parents=True,exist_ok=True)
    for course,egg in CASES:
        identity, points, config = corpus.case(course,egg)
        authored_matrix = next(v for v in identity['egg_properties']
                               if v.get('Name') == 'en3d Matrix' and v.get('Type') == 'Matrix')
        authored_is_identity = all(
            [float(x) for x in authored_matrix['Row'+str(i)].split()]
            == [float(i == j) for j in range(4)] for i in range(4))
        path = s.PathState(points,config)
        observers = [points[0]]*360  # Explicit synthetic Car0 inputs, no captured player.
        result = s.diagnostic(identity,points,config,observers,initial_bank_flag=0)
        result['inputs'] = corpus.provenance
        result['path_sweep'] = [{'time':s.mul(path.duration,s.f32(j/600)),
                                'position':path.evaluate(s.mul(path.duration,s.f32(j/600)))}
                               for j in range(601)]
        again = s.diagnostic(identity,points,config,observers,initial_bank_flag=0)
        if json.dumps(again,sort_keys=True) != json.dumps({k:result[k] for k in again},sort_keys=True):
            raise s.ContractError('nondeterministic controller output')
        tag = course+'-'+egg.replace(' ','_')
        output = dest/(tag+'.json')
        svg = dest/(tag+'.svg')
        s.tngtool.write_json(output,result)
        s.write_svg(svg,points,result['path_sweep'])
        rows.append({'course':course,'egg':egg,'marker_list':identity['marker_list'],
                     'markers':len(points),'decoded_sha256':identity['decoded_sha256'],
                     'route_sha256':identity['route_sha256'],'const_speed':config.const_speed,
                     'loop':config.loop,'trigger':config.trigger,'speed':config.speed,
                     'banking':config.banking,'samples':config.samples,'rest_ticks':config.rest_ticks,
                     'last_knot':path.knots[-1],'closing_time':path.closing_time,
                     'duration':path.duration,'authored_y_is_constant':len({p[1] for p in points})==1,
                     'authored_matrix_is_identity':authored_is_identity,
                     'controller_steps':360,'spatial_sweep_samples':601,'deterministic':True,
                     'timeline_sha256':s.tngtool.file_hash(output),
                     'svg_sha256':s.tngtool.file_hash(svg)})
    probes = []
    for segment in [0,1,3,7]:
        for local in [0.,.1,.125,.3,.5,.875]:
            coordinate = s.add(float(segment),s.f32(local))
            a = s.weights(s.sub(coordinate,float(segment)))
            b = s.probe_basis_from_elf(corpus.directory/'SLES_509.06',coordinate,segment)
            if tuple(struct.pack('<f',x) for x in a) != tuple(struct.pack('<f',x) for x in b):
                raise s.ContractError('original ELF basis probe mismatch')
            probes.append({'segment':segment,'coordinate':coordinate,'matched_host_float32_bits':True})
    metadata = {'schema_version':1,'evidence':'CONFIRMED_BY_BOTH',
                'runtime_validation':'NOT_PERFORMED',
                'initialization_assumption':'pre-init +0x128 = 0',
                'observer_assumption':'fixed at the selected first marker, synthesized input, no capture',
                'inputs':corpus.provenance,'cases':rows,
                'applicability':applicability,'basis_probes':probes}
    s.tngtool.write_json(s.ROOT/'ambient1'/'case-evidence.json',metadata)
    return metadata


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input',type=Path,required=True)
    a = ap.parse_args()
    result = build(a.input)
    print(json.dumps({'cases':len(result['cases']),'structural_instances':len(result['applicability']),
                      'basis_probes':len(result['basis_probes']),'runtime_validation':'NOT_PERFORMED'}))
