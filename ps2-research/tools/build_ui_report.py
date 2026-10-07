"""Rebuild PS2-UI1 source metadata from immutable canonical PackFS inputs.

Only targeted HUD/bonus assets and HUD XML are written, under ignored data.
PS2 frontend XML is read for a bounded reference audit. No proprietary payload
or diagnostic bitmap is placed in the committed ui directory.
"""
import argparse
import re
import xml.etree.ElementTree as ET
from pathlib import Path
import tngtool as t
import psbtool as p
from build_report import EXPECTED

ROOT = Path(__file__).resolve().parents[1]
BONUS = {
    'GRASS1':r'\TNG\DATAPSM\PARTICLES\GRASS1.GXI',
    'BUSH1':r'\TNG\DATAPSM\PARTICLES\BUSH1.GXI',
    'WATERSURFACE2':r'\TNG\DATAPSM\COMMONTEXTURES\WATERSURFACE2.GXI',
    'ENVSOURCE64X64':r'\TNG\DATAPSM\COMMONTEXTURES\ENVSOURCE64X64.GXI',
    'RENDERTARGET64X64':r'\TNG\DATAPSM\COMMONTEXTURES\RENDERTARGET64X64.GXI',
    'STATICRENDERTARGET64X64':r'\TNG\DATAPSM\COMMONTEXTURES\STATICRENDERTARGET64X64.GXI',
    'WINDSCREEN-REFLECT':r'\TNG\DATAPSM\COMMONTEXTURES\WINDSCREEN-REFLECT.GXI',
    'MAP128STRIPED':r'\TNG\DATAPSM\COMMONTEXTURES\MAP128STRIPED1-TGA.GXI',
}
MODEL_BASE = r'\TNG\DATAPSM'+'\\'
HUD = r'\TNG\DATAPSM\HUD'+'\\'
SCENES = r'\TNG\DATASCENE\HUD'+'\\'
FRONTEND = r'\TNG\DATASCENE\FRONTENDSCREENS\PS2'+'\\'
MODEL_CATEGORIES = {
    'HUD-TEMPLATE.PSB': ['tachometer_dial','circular_radar_background','tachometer_needle',
        'race_progress_car_marker','green_vertical_marker','race_progress_split_tick',
        'race_progress_finish_flag','gps_direction_pointer','race_progress_left_cap',
        'race_progress_middle_outline','race_progress_right_cap'],
    'NEWHUD.PSB': ['tachometer_dial','circular_radar_background','tachometer_needle',
        'race_progress_car_marker','green_vertical_marker','race_progress_split_tick',
        'race_progress_finish_flag','race_progress_left_cap','race_progress_middle_outline',
        'race_progress_right_cap']+['small_digit_'+str(i) for i in range(10)]+
        ['UNKNOWN_ELEMENT_20','up_arrow_large','up_arrow_small','damage_steering',
         'damage_engine','damage_suspension','damage_gear','damage_tyres']+
        ['large_digit_'+str(i) for i in range(1,10)]+['large_digit_0'],
    'HUD-DAMAGE.PSB':['damage_steering','damage_engine','damage_suspension','damage_gear','damage_tyres','damage_overlay'],
    'MASTER_TEMPLATE.PSB':['tachometer_dial','tachometer_needle','circular_radar_background',
        'gps_direction_pointer','white_marker_large','white_marker_small','green_vertical_marker',
        'white_dashed_marker','checkered_finish_marker','oval_progress_strip'],
    'HUD-NUMSSMALL.PSB':['small_digit_'+str(i) for i in range(1,5)],
}


def model_path(name):
    if name=='Null': return None
    return MODEL_BASE+name.replace('/','\\').upper()+'.PSB'


def scene_rows(data,logical,lookup):
    if not data.lstrip().startswith(b'<'): return [],'UNSUPPORTED_XML_ENCODING'
    try: tree=ET.fromstring(data)
    except ET.ParseError: return [],'MALFORMED_XML'
    rows=[]
    names=('Use en2d','en2d Model Name','en2d Matrix','en2d Image Bank Index',
           'Draw Priority','en2d FileType','en2d Visible','en2d 2dGlobal','en2d Draw 2D',
           'en2d ZBuffered','en2d Interpolated')
    for egg in tree.iter('Egg'):
        values={v.attrib.get('Name'):dict(v.attrib) for v in egg.findall('Value') if v.attrib.get('Name') in names}
        model=values.get('en2d Model Name',{}).get('Value','Null')
        matrix=values.get('en2d Matrix',{})
        ais=[]
        for ai in egg.findall('AI_List/AI'):
            owner=ai.find("Value[@Name='AI Name']")
            if owner is None or owner.attrib.get('Value')=='Null':continue
            extra=[dict(v.attrib) for child in ai if child.tag!='Value' for v in child.findall('Value')]
            ais.append({'slot':ai.attrib.get('No'),'owner':owner.attrib.get('Value'),'authored_parameters':extra})
        path=model_path(model)
        rows.append({'source':logical,'egg':egg.attrib.get('Name'),'model_name':model,
                     'logical_model_path':path,'model_manifest_match':path in lookup if path else None,
                     'image_bank_index':values.get('en2d Image Bank Index',{}).get('Value'),
                     'authored_matrix':{k:v for k,v in matrix.items() if k.startswith('Row')},
                     'authored_properties':values,'ai_owners':ais,
                     'evidence':'CONFIRMED_BY_BYTES','runtime_selection':'UNKNOWN'})
    return rows,'TEXT_XML'


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--inputs',type=Path,required=True)
    ap.add_argument('--screens',type=Path)
    a=ap.parse_args()
    output,local=ROOT/'ui',ROOT/'data'/'ui1'/'extracted'
    provenance={}
    for name,expected in EXPECTED.items():
        file=a.inputs/name
        value=t.file_hash(file)
        if value!=expected:raise t.FormatError('Canonical hash mismatch: '+name)
        provenance[name]={'size':file.stat().st_size,'sha256':value}
    manifest,_=t.load_pak(a.inputs/'TNG.PAK')
    files=sorted((r for r in manifest['entries'] if r['kind']=='file'),key=lambda r:r['path'])
    lookup={r['path']:r for r in files}
    selected=[r for r in files if r['path'].startswith(HUD) or r['path'] in BONUS.values() or r['path'].startswith(SCENES)]
    payloads,reports={},{}
    for row in selected:
        logical=row['path'];data,report=t.read_payload(row,a.inputs/'TNG.000')
        report['packfs_format_hint']=report.get('asset_format')
        report['asset_format']=(p.parse_psb(data)['format'] if logical.endswith('.PSB') else
                                p.parse_gxi(data)['format'] if logical.endswith('.GXI') else
                                'TEXT_XML' if data.lstrip().startswith(b'<') else 'UNKNOWN')
        dest=t.extraction_path(local,logical)
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        t.write_json(dest.with_name(dest.name+'.provenance.json'),report)
        payloads[logical],reports[logical]=data,report
    psbs=[]
    for logical,data in payloads.items():
        if not logical.endswith('.PSB'):continue
        doc=p.parse_psb(data)
        references=p.resolve_textures(doc,logical,manifest)
        textures={name:payloads[path] for name,path in references.items()}
        verification=p.verify(doc,textures)
        doc['logical_path']=logical
        doc['provenance'].update(reports[logical])
        doc['resolved_textures']=references
        doc['glyphs']=p.glyphs(doc)
        doc['verification']=verification
        psbs.append(doc)
    textures=[]
    for logical,data in payloads.items():
        if not logical.endswith('.GXI'):continue
        info=p.parse_gxi(data)
        textures.append({'logical_path':logical,'provenance':reports[logical],**info})
    color_samples=[]
    for suffix,channel,description in (('NEWHUD_000.GXI',1,'green radar grid'),('NEWHUD_003.GXI',0,'red tachometer band')):
        logical=HUD+suffix;raw=payloads[logical];g=p.parse_gxi(raw)
        pixels=[tuple(raw[i:i+4]) for i in range(8,len(raw),4)]
        index=max(range(len(pixels)),key=lambda i:pixels[i][channel]-max(pixels[i][c] for c in range(3) if c!=channel))
        color_samples.append({'logical_path':logical,'pixel_xy':[index%g['width'],index//g['width']],
                              'raw_byte_order_rgba':list(pixels[index]),'feature':description,
                              'evidence':'CONFIRMED_BY_VISUAL_RECONSTRUCTION'})
    scenes=[]
    xml_audit=[]
    for row in files:
        logical=row['path']
        if not logical.startswith((SCENES,FRONTEND)):continue
        data,report=(payloads[logical],reports[logical]) if logical in payloads else t.read_payload(row,a.inputs/'TNG.000')
        rows,status=scene_rows(data,logical,lookup)
        if logical.startswith(SCENES):scenes.extend(rows)
        map_refs=[v.attrib for v in ET.fromstring(data).iter('Value') if 'MAP128STRIPED' in str(v.attrib).upper()] if status=='TEXT_XML' else []
        xml_audit.append({'logical_path':logical,'provenance':report,'format':status,
                          'map128striped_references':map_refs})
    elements=[]
    for doc in psbs:
        name=doc['logical_path'].rsplit('\\',1)[-1]
        for image in doc['images']:
            i=image['image_index']
            candidates=MODEL_CATEGORIES.get(name,[])
            category=candidates[i] if i<len(candidates) else f'UNKNOWN_ELEMENT_{i}'
            if name=='HUD-NUMS.PSB':category='large_digit_'+str(i+1)
            if name=='PACENOTES.PSB':category='pace_note_symbol_'+str(i)
            users=[{'source':s['source'],'egg':s['egg'],'owners':[o['owner'] for o in s['ai_owners']]} for s in scenes
                   if s['logical_model_path']==doc['logical_path'] and s['image_bank_index']==str(i)]
            elements.append({'psb':doc['logical_path'],'image_index':i,'category':category,
                             'category_evidence':'UNKNOWN' if category.startswith('UNKNOWN') else 'CONFIRMED_BY_VISUAL_RECONSTRUCTION',
                             'triangles':image['triangle_count'],'local_bounds_xyxy':image['local_bounds_xyxy'],
                             'texture_references':sorted({r['texture_name'] for r in image['triangles'] if r['texture_name']!='Null'}),
                             'authored_scene_users':users,'runtime_screen_position':'UNKNOWN'})
    bonus=[]
    texture_by_path={r['logical_path']:r for r in textures}
    categories={'GRASS1':'grass cutout','BUSH1':'bush cutout','WATERSURFACE2':'water pattern',
                'ENVSOURCE64X64':'environment sphere','WINDSCREEN-REFLECT':'blurred environment sphere',
                'RENDERTARGET64X64':'environment capture','STATICRENDERTARGET64X64':'course landscape capture',
                'MAP128STRIPED':'striped world-map background'}
    for key,path in BONUS.items():
        bonus.append({'target':key,'logical_path':path,'present':path in lookup,
                      'texture':texture_by_path.get(path),'visual_category':categories[key],
                      'category_evidence':'CONFIRMED_BY_VISUAL_RECONSTRUCTION','runtime_usage':'UNKNOWN'})
    screens=[]
    if a.screens:
        from PIL import Image
        for path in sorted(a.screens.iterdir()):
            if path.suffix.lower() not in ('.png','.jpg','.jpeg'):continue
            with Image.open(path) as im:dimensions=list(im.size)
            racing=path.name in ('Master Rallye_SLES-50906_20251213161001.jpg','Master Rallye_SLES-50906_20260415224620.jpg')
            screens.append({'filename':path.name,'size':path.stat().st_size,'sha256':t.file_hash(path),'dimensions':dimensions,
                           'type':'racing HUD' if racing else 'replay',
                           'correlations':['tachometer outline/red band','large rank numerals','damage icon family','race progress strip','dynamic course minimap'] if racing else ['replay mode; no full race HUD'],
                           'evidence':'SCREENSHOT_CORRELATION','build_hash_verified':False})
    inventory=[{k:r[k] for k in ('path','entry_index','offset','stored_size','storage_codec')} for r in files
               if r['path'].startswith((HUD,SCENES,FRONTEND)) or r['path'] in BONUS.values()]
    p.write_json(output/'input-provenance.json',{'schema_version':1,'inputs':provenance})
    p.write_json(output/'psb-manifest.json',{'schema_version':1,'parser_version':p.SCHEMA_VERSION,'input_provenance':provenance,
                                          'scope':'10 exact HUD PSBs; other PSB files inventory only','entries':psbs})
    p.write_json(output/'hud-elements.json',{'schema_version':1,'input_provenance':provenance,'elements':elements,'authored_scenes':scenes})
    p.write_json(output/'texture-metadata.json',{'schema_version':1,'input_provenance':provenance,'entries':textures,'bonus_targets':bonus,
                                              'channel_order_samples':color_samples})
    p.write_json(output/'resource-inventory.json',{'schema_version':1,'input_provenance':provenance,'entries':inventory,
                 'all_psb_paths':[r['path'] for r in files if r['path'].endswith('.PSB')],'xml_reference_audit':xml_audit})
    p.write_json(output/'extraction-provenance.json',{'schema_version':1,'input_provenance':provenance,'scope':'targeted HUD assets, HUD XML, and eight bonus/map textures',
                                                  'entries':[reports[k] for k in sorted(reports)]})
    p.write_json(output/'screenshot-correlation.json',{'schema_version':1,'screenshots':screens,
                 'limitation':'User supplied historical images; visual correlation does not prove exact runtime build, frame selection, anchors or transforms.'})
    print({'psbs':len(psbs),'images':sum(len(d['images']) for d in psbs),'triangles':sum(d['triangle_count'] for d in psbs),
           'textures':len(textures),'extractions':len(reports),'XML_audited':len(xml_audit),'screenshots':len(screens)})


if __name__=='__main__':
    try:main()
    except (t.FormatError,p.FormatError,OSError) as error:
        raise SystemExit('build_ui_report: '+str(error))
