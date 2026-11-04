"""Read-only sky inventory; private previews and a bounded native sunset set.

Only the existing PC cylindrical clouds/layer geometry is supported. No cubemap
or GT3 format is implied. Original files are never written.
"""
from __future__ import annotations
import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from master_rallye.dx import parse_dx
from master_rallye.dxt import parse_dxt, encode_png, PNG_ROWS_PRESERVE_STORED

PALETTE = ((.87,.86,.86),(.57,.66,.8),(.47,.53,.59),(.56,.36,.24),(.27,.33,.4),(.88,.94,.98))
def sha(data): return hashlib.sha256(data).hexdigest()

def inventory(source: Path, output: Path):
    source, output = source.resolve(), output.resolve()
    if output == source or source in output.parents or output in source.parents:
        raise ValueError('source and output must be disjoint')
    output.mkdir(parents=True, exist_ok=True)
    rows, identities = [], []
    for preset in range(6):
        row = {'preset':preset, 'fog_rgb':PALETTE[preset], 'resources':[]}
        folder = source / f'cloud{preset}'
        for layer, name in enumerate((f'clouds{preset}', f'layer{preset}')):
            path = folder / (name+'.dx'); model = parse_dx(path)
            draws = [r for r in model.physical_draws if r.index_count]
            textures = sorted({s.value for r in draws for s in r.texture_slots if s.value != 'Null'})
            if len(textures)!=1: raise ValueError(f'expected one texture: {path}: {textures}')
            tex_path = folder / (textures[0]+'.dxt'); tex = parse_dxt(tex_path)
            record = {'model':path.relative_to(source).as_posix(), 'model_sha256':sha(path.read_bytes()),
                      'vertices':model.vertex_count, 'bounds': [list(v) for v in (tuple(min(p[i] for p in model.vertices.positions) for i in range(3)),tuple(max(p[i] for p in model.vertices.positions) for i in range(3)))],
                      'draws':[{'flags':r.flags_0x20.hex(),'indices':r.index_count,'textures':list(r.texture_tuple)} for r in draws],
                      'texture':tex_path.relative_to(source).as_posix(),'texture_sha256':sha(tex_path.read_bytes()),
                      'pixels_bgra_sha256':sha(tex.bgra),'width':tex.width,'height':tex.height,
                      'alpha_range':[min(tex.bgra[3::4]),max(tex.bgra[3::4])],
                      'format':'FEED header + BGRA8 stored rows; not block DXT', 'thumbnail_rows':'preserve-stored, RGB inspection with alpha forced opaque'}
            (output/f'{preset}-{layer}-source-alpha.png').write_bytes(encode_png(tex,PNG_ROWS_PRESERVE_STORED))
            rgb=bytearray(tex.bgra);rgb[3::4]=bytes([255])*(tex.width*tex.height)
            (output/f'{preset}-{layer}.png').write_bytes(encode_png(replace(tex,bgra=bytes(rgb)),PNG_ROWS_PRESERVE_STORED))
            row['resources'].append(record)
            identities.append((sha(tex.bgra),sha(tex.bgra[3::4]),preset,layer,tex.width,tex.height))
            if preset==3:
                # A deliberately mild authoring experiment. The original alpha,
                # row order, periodic U seam and cylinder geometry are retained.
                pixels=bytearray(tex.bgra)
                for i in range(0,len(pixels),4):
                    b,g,r,a=pixels[i:i+4]
                    pixels[i:i+4]=bytes((round(b*.82),round(g*.94),min(255,round(r*1.04+5)),a))
                dest=output/'sets'/'sunset';dest.mkdir(parents=True,exist_ok=True)
                (dest/('clouds.dxt' if layer==0 else 'layer.dxt')).write_bytes(tex.header+pixels)
        rows.append(row)
    report={'schema':1,'evidence':'OFFLINE_VALIDATED_RESOURCE_BYTES','source':str(source),'presets':rows,
            'extra_debug_preset_6':'present in retail corpus; outside original 0..5 cycle; excluded from selector',
            'custom_set':'sets/sunset: derived private colour experiment on preset 3, same geometry/alpha, not a GT3 asset',
            'runtime':'NOT_TESTED'}
    (output/'catalog.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    cards=[]
    for row in rows:
        p=row['preset']; cards.append(f'<article><h2>CloudNumber {p}</h2><p>Fog RGB {row["fog_rgb"]}</p>'+''.join(f'<figure><img src="{p}-{k}.png"><figcaption>{r["texture"]} — {r["width"]}×{r["height"]}; stored rows</figcaption></figure>' for k,r in enumerate(row['resources']))+'</article>')
    (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>MR sky catalog</title><style>body{background:#20232a;color:#eee;font:16px system-ui}main{display:grid;grid-template-columns:repeat(2,1fr)}article{padding:16px}img{max-width:100%;height:160px;object-fit:contain;background:#555}figure{margin:8px}</style><h1>Six native skies — resource inventory</h1><p>Stored texture rows, RGB inspection with alpha forced opaque. Original-alpha PNGs are provided separately. Not in-game screenshots. Runtime geometry, material alpha and camera decide presentation.</p><main>'+''.join(cards)+'</main>',encoding='utf-8')
    return identities

def registry(rows):
    return '#pragma once\n// Generated by tools/atmosphere_catalog.py; original BGRA8 level-0 identities.\nnamespace gfx2::atmosphere {\nstruct SkyIdentity { const char* sha; const char* alpha_sha; unsigned preset,layer,width,height; };\ninline constexpr SkyIdentity kSkyIdentities[]={\n'+''.join(f'    {{"{s}","{a}",{p},{l},{w},{h}}},\n' for s,a,p,l,w,h in rows)+'};\n}\n'

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--registry',type=Path)
    a=p.parse_args();rows=inventory(a.source,a.output)
    if a.registry:a.registry.write_text(registry(rows),encoding='utf-8')
    print(f'Validated {len(rows)} native sky resources; private output: {a.output}')
if __name__=='__main__':main()
