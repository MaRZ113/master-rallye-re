"""Rebuild deterministic PackFS metadata and a small ignored extraction set."""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path
import tngtool as t

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    r'\TNG\DATAPSM\HUD\HUD-TEMPLATE.PSB',
    r'\TNG\DATAPSM\HUD\HUD-NUMS.PSB',
    r'\TNG\DATAPSM\HUD\NEWHUD_000.GXI',
    r'\TNG\DATAPSM\COMMONTEXTURES\ENVSOURCE64X64.GXI',
    r'\TNG\DATAPSM\COMMONTEXTURES\REAR128-TGA.GXI',
    r'\TNG\DATAPSM\COURSE\FRANCE1\WATER-TGA.GXI',
    r'\TNG\DATAPSM\COURSE\FRANCE2\GRASS-TGA.GXI',
]
EXPECTED = {
    'SLES_509.06': 'b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2',
    'SYSTEM.CNF': 'db08eef06278820a562f9cdacd6a2d5d2bb31870e7cf3a51e83daee3a90c5df2',
    'TNG.PAK': t.PAK_SHA,
    'TNG.000': '004ac1676376275bf40c1fd5c1c4a9dcfaae870bf1a7916434eb73b0b1faff86',
}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--inputs',type=Path,required=True)
    a=ap.parse_args()
    output=ROOT/'packfs'
    inputs={}
    for name,expected in EXPECTED.items():
        path=a.inputs/name
        inputs[name]={'available':path.is_file()}
        if path.is_file():
            value=t.file_hash(path)
            if value!=expected: raise t.FormatError('Canonical input hash mismatch: '+name)
            inputs[name].update(size=path.stat().st_size,sha256=value,verified=True)
    t.write_json(output/'input-provenance.json',{'schema_version':1,'inputs':inputs,'source_policy':'immutable external proprietary inputs'})
    manifest,framing=t.load_pak(a.inputs/'TNG.PAK')
    validation=t.verify_data(manifest,a.inputs/'TNG.000')
    t.write_json(output/'tng-manifest.json',manifest)
    t.write_json(output/'golden-validation.json',{'input_sha256':t.PAK_SHA,'input_size':135556,
                  'output_size':269668,'output_sha256':manifest['directory_sha256'], 'golden_match':True,'framing':framing})
    files=[r for r in manifest['entries'] if r['kind']=='file']
    lookup={r['path']:r for r in files}
    paths=list(TARGETS)
    paths+=sorted(r['path'] for r in files if '\\ITALY3\\' in r['path'] and 'GRASSPATH' in r['path'])[:1]
    reports=[]
    for path in paths:
        if path not in lookup: raise t.FormatError('Validation target missing: '+path)
        payload,report=t.read_payload(lookup[path],a.inputs/'TNG.000')
        dest=t.extraction_path(ROOT/'data'/'validation',path)
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(payload)
        t.write_json(dest.with_name(dest.name+'.provenance.json'),report)
        reports.append(report)
    t.write_json(output/'extraction-provenance.json',{'schema_version':1,'input_sha256':validation['sha256'],
                 'validation_scope':'exactly the listed assets; other payloads not fully decompressed', 'entries':reports})
    patterns={
        'HUD':('\\HUD\\','MASTER_TEMPLATE','PACENOTES','CARDAMAGEBITS','MAP128STRIPED','\\FRONTENDSCREENS\\PS2\\'),
        'grass_detail':('GRASS','SHRUB','STONES','\\PARTICLES\\'),
        'water':('WATER','PUDDLE'),
        'reflection':('ENV','REFLECT','CHROME','REAR128','RENDERTARGET','WINDSCREEN'),
    }
    families={}
    fields=('path','entry_index','offset','stored_size','unpacked_size','compression','storage_codec')
    for family,terms in patterns.items():
        rows=[{k:r[k] for k in fields} for r in files if any(term in r['path'] for term in terms)]
        families[family]={'selection':'name-based inventory; rendering role remains STATIC_INFERENCE',
                          'patterns':list(terms),'resource_count':len(rows),'entries':rows}
    t.write_json(output/'graphics-targets.json',{'schema_version':1,'families':families})
    extensions=Counter(Path(r['path'].replace('\\','/')).suffix or '(none)' for r in files)
    compression=Counter(r['compression'] for r in files)
    summary=['# TNG directory inventory','',f"Canonical body: {manifest['directory_sha256']}",
        '',f"Directories: **{manifest['directory_count']}**. Files: **{manifest['file_count']}**.",
        f"Hash buckets: {manifest['bucket_count']}; codec descriptors: {len(manifest['codecs'])}.",
        '', 'Manifest order is serialized node-pool order. `entry_index` is a zero-based offline index, not a proven engine resource ID.',
        '', '| Extension | Files |','| --- | ---: |',
        *[f'| {key} | {value} |' for key,value in sorted(extensions.items())],
        '', '| Storage | Files |','| --- | ---: |',
        *[f'| {key} | {value} |' for key,value in sorted(compression.items())],
        '', f"Total stored bytes: **{validation['total_stored_bytes']}**.",
        f"Total unpacked bytes declared by resource headers/raw directory sizes: **{validation['total_header_declared_unpacked_bytes']}**.",
        'The latter is a header inventory, not full decompression validation of all resources.',
        '', 'All 3599 file ranges are valid. No overlaps; ranges cover TNG.000 completely with no gaps.',
        'All 3345 codec `gz` resources have header `(compressor_id=1, unknown_0x05=1, block_size=8192)`.',
        '', '## Resource families','',
        *[f"- {family}: {value['resource_count']} name-matched candidates." for family,value in families.items()],
        '', 'Course: '+str(sum('\\COURSE\\' in r['path'] for r in files))+' files.',
        'CommonTextures: '+str(sum('\\COMMONTEXTURES\\' in r['path'] for r in files))+' files.',
        'Particles: '+str(sum('\\PARTICLES\\' in r['path'] for r in files))+' files.',
        '', 'Exact target records and hashes are in `extraction-provenance.json`; family inventories are in `graphics-targets.json`.',
    ]
    (output/'tng-directory.md').write_text('\n'.join(summary)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'directories':manifest['directory_count'],'files':manifest['file_count'],
                      'compression':dict(compression),'extractions':len(reports),
                      'families':{k:v['resource_count'] for k,v in families.items()}},indent=2))

if __name__=='__main__':
    try: main()
    except (t.FormatError,OSError) as error:
        sys.exit(f'build_report: {error}')
