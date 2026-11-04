"""Extract one original road draw for an isolated D3D8 lighting experiment.

The output is private source-derived data, never a gameplay capture or a course
replacement. The Course SDK's parser is used, including its explicit limits.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'src'))
from master_rallye.dx_course import parse_course_dx
from master_rallye.dxt import parse_dxt

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--course',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    source=a.course.resolve();out=a.output.resolve()
    if source.parent==out or source.parent in out.parents:raise ValueError('output must be outside original course')
    model=parse_course_dx(source)
    if model.diagnostics.errors:raise ValueError(model.diagnostics.errors)
    draw=next(r for r in model.physical_draws if r.index_count and r.texture_tuple[0]=='road-tga' and 'noise-tga' in r.texture_tuple)
    indices=[draw.vertex_base+i for i in model.local_indices[draw.index_start:draw.index_start+draw.index_count]]
    tex_path=source.parent/'road-tga.dxt';tex=parse_dxt(tex_path)
    payload=bytearray(struct.pack('<4s3I',b'ATL1',len(indices),tex.width,tex.height))
    for i in indices:
        color=struct.unpack_from('<I',model.vertices.colors,4*i)[0]
        payload+=struct.pack('<3fI2f',*model.vertices.positions[i],color,*model.uv_sets[0].values[i])
    payload+=tex.bgra;out.mkdir(parents=True,exist_ok=True);(out/'road.bin').write_bytes(payload)
    (out/'source.json').write_text(json.dumps({'evidence':'SOURCE_DERIVED_D3D8_PROBE_INPUT_NOT_GAMEPLAY','source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'texture':str(tex_path),'texture_sha256':hashlib.sha256(tex_path.read_bytes()).hexdigest(),'record':draw.record_path,'vertices_flat':len(indices),'parser_warnings':model.diagnostics.warnings,'whole_course_reconstructed_global_match':model.diagnostics.reconstructed_global_match,'probe_sha256':hashlib.sha256(payload).hexdigest()},indent=2)+'\n')
    print(f'{draw.record_path}: {len(indices)//3} original road triangles, private {out}')
if __name__=='__main__':main()
