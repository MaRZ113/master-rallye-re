#!/usr/bin/env python3
"""Extract cross-file references from Master Rallye XML and vehicle TXT sidecars."""
from __future__ import annotations
import argparse, json, re, xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

MESH_RE=re.compile(r"moMesh\(Name \[(.*?)\] Index (\d+) Size (\d+)\)")
MAT_RE=re.compile(r"Material number \[\s*(\d+)\] has name \[(.*?)\]")
TEX_RE=re.compile(r"Texture \[\s*(\d+)\].*?Name\[([^\]]+\.tga)\]",re.I)

def rel(p,root): return p.relative_to(root).as_posix()
def dxt_name(tga): return (Path(tga.replace('\\','/')).stem+'-tga.dxt').lower()

def parse_sidecar(path,root):
    text=path.read_text(encoding='latin-1')
    mats=[{"number":int(m.group(1)),"name":m.group(2)} for m in MAT_RE.finditer(text)]
    meshes=[{"name":m.group(1),"index":int(m.group(2)),"size":int(m.group(3))} for m in MESH_RE.finditer(text)]
    textures=[]
    for m in TEX_RE.finditer(text):
        src=Path(m.group(2).replace('\\','/')).name
        textures.append({"slot":int(m.group(1)),"source_tga":src,"expected_dxt":dxt_name(src)})
    return {"path":rel(path,root),"materials":mats,"meshes":meshes,"textures":textures,
            "mesh_span":max((m['index']+m['size'] for m in meshes),default=0)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source',required=True,type=Path); ap.add_argument('--relationships',required=True,type=Path)
    args=ap.parse_args(); root=args.source.resolve(); vehicle_root=root/'DataGx'/'Vehicles'
    asset_dirs=sorted((p.name for p in vehicle_root.iterdir() if p.is_dir()),key=str.lower); asset_lut={x.lower():x for x in asset_dirs}
    xml_files=sorted(root.rglob('*.xml')); parsed=0; failures=[]; config_ids=defaultdict(lambda:defaultdict(int)); direct_refs=defaultdict(list)
    key_value_names=Counter(); model_values=[]
    for path in xml_files:
        try: tree=ET.parse(path); parsed+=1
        except ET.ParseError as exc: failures.append({"path":rel(path,root),"error":str(exc)}); continue
        for elem in tree.iter():
            name=elem.attrib.get('Name',''); value=elem.attrib.get('Value','')
            if elem.tag=='Value' and name: key_value_names[name]+=1
            m=re.match(r"Vehicles[/\\]([^/\\]+)[/\\]",name,re.I)
            if m: config_ids[m.group(1)][rel(path,root)]+=1
            if name in {'CarModelDataFile','Car Name'} and value:
                direct_refs[value].append({"file":rel(path,root),"field":name,"value":value})
            if name in {'en3d Model Name','en2d Model Name','Model Name','Texture Name'} and value not in {'','Null'}:
                model_values.append({"file":rel(path,root),"field":name,"value":value})
    graphs=[]
    for asset in asset_dirs:
        directory=vehicle_root/asset; available={p.name.lower():p.name for p in directory.iterdir() if p.is_file()}
        sidecars=[parse_sidecar(p,root) for p in sorted(directory.glob('*.txt'))]
        expected=sorted({t['expected_dxt'] for s in sidecars for t in s['textures']})
        resolved=[available[x] for x in expected if x in available]
        missing=[x for x in expected if x not in available]
        config=[]
        for ident,files in config_ids.items():
            if ident.lower()==asset.lower(): config.extend({"identifier":ident,"file":f,"entry_count":n} for f,n in sorted(files.items()))
        refs=[]
        for ident,items in direct_refs.items():
            if ident.lower()==asset.lower(): refs.extend(items)
        graphs.append({"vehicle_identifier":asset,"asset_directory":f"DataGx/Vehicles/{asset}","config_entries":config,
                       "direct_scene_references":refs,"model_files":[available[x] for x in ('car.dx','complete.dx','wheel.dx') if x in available],
                       "sidecars":sidecars,"referenced_dxt":{"resolved":resolved,"missing":missing}})
    config_only=sorted(k for k in config_ids if k.lower() not in asset_lut)
    asset_only=sorted(a for a in asset_dirs if a.lower() not in {k.lower() for k in config_ids})
    relationships=json.loads(args.relationships.read_text(encoding='utf-8'))
    relationships['text_corpus']={"xml_file_count":len(xml_files),"xml_parsed":parsed,"xml_parse_failures":failures,
                                  "unique_value_names":len(key_value_names),"model_or_texture_value_count":len(model_values),
                                  "config_vehicle_identifiers":sorted(config_ids),"config_only_identifiers":config_only,"asset_only_directories":asset_only}
    relationships['vehicle_reference_graph']=graphs
    relationships['lab_samples']={"primary":"Astero","normal_validation":"Bruno","unusual_validation":"Ufo",
      "rationale":{"Astero":"common 3 DX + 3 TXT layout","Bruno":"same common layout; independent geometry/material payload",
                   "Ufo":"only car/complete pairs and no wheel resource; smallest vehicle file set"}}
    relationships['selected_model_texture_values']=model_values[:200]
    args.relationships.write_text(json.dumps(relationships,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f"parsed XML: {parsed}/{len(xml_files)}; vehicle graphs: {len(graphs)}")
    print(f"config-only identifiers: {len(config_only)}; asset-only directories: {len(asset_only)}")
if __name__=='__main__':main()
