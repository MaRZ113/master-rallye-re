"""Regenerate exact original Terrano native glow hashes; no game asset export."""
from pathlib import Path
import importlib.util,json,struct,hashlib
PORT=Path(__file__).resolve().parents[1]
def main():
 spec=importlib.util.spec_from_file_location('glow_common',PORT/'docs/full-coverage/vehicles/audit.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
 d=json.loads((PORT/'docs/xtrail-brake-followup/glow-source.json').read_text());path=a.PC/'Terrano/car.dx'
 if a.sha(path.read_bytes())!=d['source_sha256']:raise ValueError('PC source drift')
 m=a.parse_dx(path);draw=m.physical_draws[d['draw']];geometry=a.geometry_signature(a.faces(m,draw));records=[struct.pack('<3f3f2f',*m.vertices.positions[i],*m.vertices.normals[i],*m.uv_sets[0].values[i]) for i in range(draw.vertex_base,draw.vertex_base+draw.local_vertex_max+1)];attributes=hashlib.sha256(b''.join(sorted(records))).hexdigest()
 if geometry!=d['geometry_sha256'] or attributes!=d['attribute_sha256']:raise ValueError('Original glow identity changed')
 header='#pragma once\nnamespace gfx2::ps2port {\ninline constexpr const char* kTerranoGlowGeometry="'+geometry+'";\ninline constexpr const char* kTerranoGlowAttributes="'+attributes+'";\n}\n'
 (PORT/'renderer/brake_glow_identity.hpp').write_text(header)
 print('Original source identity reproduced')
if __name__=='__main__':main()
