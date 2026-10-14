"""Derive compact lamp source ownership from the earlier immutable source audit.

No brake simulation, new draw behavior, resource bytes or runtime pointer is
created. Source child selectors and original spelling remain separate from
unperformed live selection/GS validation.
"""
from pathlib import Path
from collections import Counter
import json

HERE=Path(__file__).resolve().parent
PORT=HERE.parents[2]


def main():
    original=PORT/'docs/coverage-followup/body-lights/source-joins.json'
    source=json.loads(original.read_text())
    families=[];counts=Counter()
    for family in source['brake_family_inventory']:
        if 'error' in family:
            families.append({'family':family['family'],'error':family['error']});continue
        names=[n for n in family['named_nodes'] if n.get('name')=='blight']
        groups=[]
        for mesh in family['light_meshes']:
            counts[str(mesh['final_mode_in_loader'])]+=1
            # Exact source hierarchy; no equation between child ordinal and state.
            ancestor=[n for n in family['named_nodes'] if
                mesh['path'].startswith(n['path']+'.') and n.get('tag')==8]
            selected=max(ancestor,key=lambda n:len(n['path'])) if ancestor else None
            groups.append({'mesh_path':mesh['path'],'node_offset':mesh['node_offset'],
                'material_offset':mesh['material_offset'],'material':mesh['material'],
                'source_faces':mesh['source_faces'],'texture_slots':mesh['texture_slots'],
                'final_mode':mesh['final_mode_in_loader'],
                'selector':selected.get('selector') if selected else None,
                'selector_wrapper':selected.get('path') if selected else None,
                'on_off_role':'ON_TEXTURE_AND_SELECTOR2' if mesh['final_mode_in_loader'] in (1,14) else 'SOURCE_OFF_OR_UNCONDITIONAL_LIGHT_CANDIDATE',
                'runtime_validation':'NOT_PERFORMED'})
        families.append({'family':family['family'],'source':family['source'],
            'sha256':family['sha256'],'blight_named_wrapper':names,'light_meshes':groups})
    out={'schema_version':1,'source_basis':'coverage-followup/body-lights/source-joins.json',
        'source_representation':'AUTHORED_SOURCE_MESH_NOT_NUMBER_OF_LIGHTS',
        'mode_record_counts':dict(sorted(counts.items())), 'families':families,
        'owner_init':{'entry':'0x001a07e0','model_field':'+0x18','option_index_field':'+0x14',
            'lookup_name':'blight','lookup':'0x001d76d0','controller_key':'Controller/<source Egg name>'},
        'owner_update':{'entry':'0x001a08c0','source':'Broker 0x001e4280 -> 0x001e3820 -> result+8 pointer -> float32+0x24',
            'threshold_word':'0x3dcccccd','rule':'source > float32(0.1): selector2; otherwise selector1',
            'option_writer':'0x001d77a0','writer_contract':'index>=0 && index<model+0x18 count;0<=value<=model+0x0c max[index];write model+0x00 values[index]',
            'source_semantics':'STATIC_BRAKE_OWNER_CONTRACT;liveControllerownershipnotcaptured'},
        'material_classifier':{'entry':'0x00391690','post_shader_priority':[
            {'original_primary_substring':'breaklightsonglow-','mode':14,'field2c':1,'field3c':0,'field44':.3,'first_write':'0x00391c54'},
            {'original_primary_substring':'breaklightson-','mode':1,'field2c':0,'field3c':0,'field44':.3,'first_write':'0x00391cc0'}],
            'unknown_shader_names':['carbrakelight','carbrakelights','brakelight'],
            'unknown_names_not_silently_aliased':True},
        'evidence_grade':'CONFIRMED_BY_BOTH','gs_and_runtime_status':'UNKNOWN',
        'missing_interfaces':['Actual brake-source key owner/lifetime/current field24 value',
            'Selected liveblight1/2 source mesh and runtime GS submission',
            'Mode14 fulltexture/ALPHA/TEST/ZBUF/inheritedstate/order',
            'PCnativecurrentbrakeidentity+off/on/glowdraw ownership',
            'PS2 lamptexturealpha/sampling andpostprocess visualcapture']}
    (HERE/'lights-contract.json').write_text(json.dumps(out,indent=2)+'\n')


if __name__=='__main__':main()
