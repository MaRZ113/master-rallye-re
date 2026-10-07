"""Rebuild safe UI2 metadata from UI1 reports and local bounded ELF exports.

No raw decompilation or extracted route coordinates are copied to source.
The source ELF is hash locked. Export addresses below were manually checked
against direct calls, vtables, and scalar assembly before being admitted.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import hudruntime as h

ROOT = h.ROOT
ELF = 'CONFIRMED_BY_ELF'
BOTH = 'CONFIRMED_BY_BOTH'
UNKNOWN = 'UNKNOWN'

# Working labels, not original C++ symbols. Explicit admission list excludes
# exploratory false starts (e.g. 338d88 cleanup and 21e800 mid-function).
FUNCTIONS = [
    (0x146118, 'gaHudAiMap_ctor', 'Initialize type ID, vtable, vector headers, dimensions/center defaults', ['0x7c','0x80','0x84','0x88']),
    (0x1461f8, 'gaHudAiMap_initialize', 'Resolve player/car/marker keys, colors, clip globals and buffers', ['0xc','0x10','0x14','0x18','0x24','0x30','0x70']),
    (0x146868, 'gaHudAiMap_schema', 'Serialize Hud No, clip dimensions and center', ['0xc','0x7c','0x80','0x84','0x88']),
    (0x146960, 'gaHudAiMap_configure', 'Read custom map settings from owner configuration broker', ['0xc','0x7c','0x80','0x84','0x88']),
    (0x1469f0, 'clip_map_segment', 'Clip against shared half extents and append translated Vec2 endpoint pairs', []),
    (0x146d80, 'draw_map_endpoint_pairs', 'Compare odd endpoint to cached even point, flush on inequality; nonzero segments submit separately', ['0x54']),
    (0x147038, 'gaHudAiMap_update_draw', 'RaceLine and vehicle output to clipped route, player chevron and opponent crosses', ['0x14','0x3c','0x48','0x54','0x60','0x74','0x78','0x84','0x88']),
    (0x14b040, 'gaHudAiSpeedDial_ctor', 'Register dial type ID and vtable', []),
    (0x14b290, 'configure_dial', 'Read offsets and rotation settings then publish them', ['0x10','0x14','0x1c','0x20','0x24','0x28']),
    (0x14b388, 'publish_dial_settings', 'Read visual translation and publish needle, gear and speed broker positions', ['0x50','0x54']),
    (0x14b580, 'gaHudAiSpeedNeedle_ctor', 'Register needle type ID and vtable', []),
    (0x14b6c8, 'initialize_needle', 'Apply published dial position to en2d and resolve vehicle-output source', ['0x10','0x14','0x50','0x54']),
    (0x14db88, 'gaHudLoader_ctor', 'Register HUD scene loader type and vtable', []),
    (0x14dbd8, 'load_hud_scene', 'Select attract/single/split scene and Visable keys from race state', []),
    (0x14de38, 'gaHudRankAi_ctor', 'Default rank bank HUD/newhud and font selector 0x67', ['0x24','0x28']),
    (0x14dfc0, 'configure_rank', 'Read Hud No, RankImageBank and Font No', ['0xc','0x24','0x28']),
    (0x14e028, 'rebuild_rank_commands', 'Rebuild same en2d bank/key commands for rank digits and localized suffix', ['0x14','0x18','0x1c']),
    (0x14e250, 'initialize_rank', 'Resolve Race/CarN/Rank and font resource; initialize digit commands', ['0x14','0x20']),
    (0x14e360, 'update_rank', 'Rebuild commands on changed broker rank', ['0x10','0x20']),
    (0x15b190, 'register_game_ai_prototypes', 'Allocate and append typed AI prototypes, including HUD subset', []),
    (0x1cc908, 'initialize_hud_name_ids', 'Intern static RaceLine, vehicle-output and HUD scene/key identifiers', []),
    (0x1fc4c0, 'clone_owner_by_type', 'Lookup prototype then invoke virtual clone slot +0x14', ['0x8']),
    (0x1fc500, 'lookup_owner_prototype', 'Search registry vector comparing owner type ID +4', ['0x4']),
    (0x1fc760, 'owner_registry_holder', 'Singleton holder of owner prototype registry', []),
    (0x1fde60, 'marker_manager_holder', 'Resolve marker-list manager singleton', []),
    (0x1fdba8, 'find_named_marker_list', 'Resolve list by interned name ID', []),
    (0x1ff618, 'read_marker_lists', 'Dispatch scene MarkerLists entries to named-list reader', []),
    (0x1ff6a0, 'read_named_marker_list', 'Create named list then visit markers in document order', []),
    (0x1ff7a8, 'read_append_marker', 'Read type, position and direction, append 0x50-byte record', ['0x40','0x44','0x48','0x4c']),
    (0x205bf8, 'en2d_ctor', 'Create visual object with matrix, command vector and renderer cache', ['0x4','0x20','0x64','0x78','0x80']),
    (0x205ce0, 'append_image_key', 'Append authored index as u16 mapping key', []),
    (0x205dc8, 'append_string_keys', 'Append unsigned byte characters as u16 bank keys', []),
    (0x205ea0, 'reset_en2d', 'Identity matrix and initial 0x34-byte command', ['0x20','0x50','0x64']),
    (0x2060f8, 'clear_en2d_commands', 'Reset command stream for dynamic owners', []),
    (0x206218, 'replace_en2d_render_cache', 'Replace renderer-owned cache +0x80', ['0x80']),
    (0x2062a8, 'select_command_bank', 'Assign current command bank name ID', ['0xc']),
    (0x206338, 'set_command_rgba', 'Assign command float RGBA', ['0x1c']),
    (0x2063a0, 'set_command_position', 'Assign command cursor/position', ['0x10','0x14','0x18']),
    (0x21e290, 'runtime_entity_ctor', 'Create 0x7c entity, four owner slots and visual references', ['0x4','0x4c','0x50']),
    (0x21e4f0, 'request_entity_removal', 'Set removal flag and enqueue deferred destruction', ['0x0']),
    (0x21e540, 'attach_en2d', 'Replace entity en2d visual', ['0x4c']),
    (0x21e620, 'attach_ai_initialize', 'Store owner in slot and invoke virtual initializer +0x34', ['0x4']),
    (0x292a48, 'hatch_entity', 'Template matrix/bank/key/flags to entity and en2d, clone/configure/initialize owners', ['0x30','0x38','0x40','0x90']),
    (0x295d58, 'read_egg_version4', 'Parse modern authored template including en2d 2dGlobal bit6', ['0x28','0x30','0x38','0x40','0x90']),
    (0x2dc4d0, 'install_ps2_ui_renderer', 'Install concrete PS2 renderer into UI renderer holder', []),
    (0x2dd510, 'configure_ui_viewport_projection', '640/480 viewport ratios, GS center/scissor and orthographic bounds', []),
    (0x318bd8, 'tag_ui_triangle_strip_packet', 'Packet tag PRIM=0x14c: triangle strip, texture disabled, alpha blend enabled', []),
    (0x318e10, 'emit_ps2_ui_primitive_packets', 'Expand stroked line/polyline/polygon to vertex pairs and GS packet positions', []),
    (0x3280d0, 'projection_object_ctor', 'Construct affine, clip and screen matrices from extended float ABI arguments', []),
    (0x328168, 'build_projection_matrices', 'Scalar projection and viewport matrix builder', []),
    (0x32e8e8, 'ps2_ui_renderer_ctor', 'Concrete UI interface vtable and primitive object', ['0x468']),
    (0x32edf8, 'set_primitive_rgba', 'Pack R:G:B:A bytes in high-to-low order', []),
    (0x32ee28, 'set_primitive_width', 'Store half of requested stroke width', []),
    (0x32ee40, 'queue_ui_line', 'Queue type1 and float XY endpoints', []),
    (0x32f498, 'queue_ui_open_polyline', 'Queue type4 with at most 64 points', []),
    (0x32f710, 'queue_ui_closed_polygon', 'Queue type5 with at most 63 points', []),
    (0x32fce0, 'flush_ui_frame', 'Flush global sprites then map primitive packets and clear vectors', ['0x468']),
    (0x337a98, 'build_psb_sprite_vertices', 'Visible en2d commands to bank key lookup and local triangle geometry', ['0x4c','0x64','0x78','0x80']),
    (0x338ab8, 'configure_sprite_orthographic', 'Apply orthographic UI camera for en2d modes 1/2', []),
    (0x342b90, 'sprite_matrix_product_wrapper', 'Call COP2 matrix product; numeric semantics not modeled by the scalar query', []),
    (0x3432b8, 'submit_sprite_world_matrices', 'Pass current/interpolated world matrices to GS renderer and snapshot globals', []),
    (0x36a5a8, 'copy_sprite_world_matrices', 'Copy en2d-derived current/interpolated matrix to cache +0x50/+0x90', ['0x50','0x90']),
    (0x3cb2d0, 'matrix_product_cop2_unmodeled', 'Four vector rows consumed/produced by COP2; exact VU result remains UNKNOWN here', []),
]

OWNER_DEFS = {
    'gaHudAiMap': (0x146118, 0x44cb00, 0x8c),
    'gaHudAiSpeedDial': (0x14b040, 0x44c900, 0x44),
    'gaHudAiSpeedNeedle': (0x14b580, 0x44c8c0, 0x34),
    'gaHudRankAi': (0x14de38, 0x44c700, 0x2c),
    'gaHudLoader': (0x14db88, 0x44c740, 0xc),
}


def va(n):
    return f'0x{n:08x}'


def write(name, document):
    dest = ROOT / 'ui2' / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(document, indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')


def field(name, offset, size, representation, accessors, grade=ELF):
    return {'name': name, 'offset': offset, 'size': size, 'representation': representation,
            'accessors': [va(a) for a in accessors], 'evidence': grade}


def structures():
    fields = [field('base_header', 0, 12, 'sentinel, interned type ID, AI vtable pointer', [0x146118]),
              field('hud_no', 0xc, 4, 's32', [0x146868,0x146960,0x1461f8]),
              field('player_id', 0x10, 4, 's32', [0x1461f8,0x147038]),
              field('finish_best_marker', 0x14, 4, 's32 from FinishArea/BestMarker', [0x1461f8,0x147038])]
    for name, offset, kind in [('split_best_markers',0x18,'u32'),('car_name_ids',0x24,'u32'),
                               ('car_colors',0x30,'float32 RGBA'),('route_segments',0x3c,'float32 Vec2'),
                               ('split_segments',0x48,'float32 Vec2'),('polyline_scratch',0x54,'float32 Vec2'),
                               ('finish_segments',0x60,'float32 Vec2')]:
        fields.append(field(name,offset,12,'begin/end/capacity pointers to '+kind,[0x146118,0x1461f8,0x147038]))
    for name, offset, kind, acc in [
        ('last_marker_key',0x6c,'interned Race/CarN/LastMarker key',[0x1461f8,0x147038]),
        ('car_count',0x70,'s32 Race/NumCars',[0x1461f8,0x147038]),
        ('heading_z',0x74,'float32; initial value UNKNOWN',[0x147038]),
        ('heading_x',0x78,'float32; initial value UNKNOWN',[0x147038]),
        ('clip_height',0x7c,'float32',[0x146118,0x146868,0x146960,0x1461f8,0x147038]),
        ('clip_width',0x80,'float32',[0x146118,0x146868,0x146960,0x1461f8,0x147038]),
        ('center_x',0x84,'float32 top-left logical X',[0x146118,0x146868,0x146960,0x1461f8,0x147038]),
        ('center_y',0x88,'float32 top-left logical Y',[0x146118,0x146868,0x146960,0x1461f8,0x147038])]:
        fields.append(field(name,offset,4,kind,acc))
    return {'schema_version':1,'elf_sha256':h.ELF_SHA,'structures':[
        {'name':'runtime_entity','size':0x7c,'fields':[
            field('flags',0,4,'bit0 Freezable, bit1 pending removal',[0x21e290,0x21e4f0,0x292a48]),
            field('owner_slots',4,16,'four AI pointers',[0x21e290,0x21e620,0x292a48]),
            field('en2d',0x4c,4,'visual pointer',[0x21e290,0x21e540,0x292a48,0x337a98]),
            field('en3d',0x50,4,'visual pointer',[0x21e290,0x292a48]),
            field('name_id',0x5c,4,'interned name ID',[0x292a48]),
            field('parent',None,None,'UNKNOWN',[],UNKNOWN)]},
        {'name':'en2d','size':0x90,'fields':[
            field('commands',4,12,'vector of 0x34-byte bank/key commands',[0x205bf8,0x205ea0,0x337a98]),
            field('color',0x10,16,'float32 RGBA',[0x205bf8,0x337a98]),
            field('matrix',0x20,64,'row-oriented float32 matrix, translation +0x50/+0x54',[0x205ea0,0x292a48,0x337a98]),
            field('coordinate_mode',0x64,4,'0=world,1=viewport UI,2=global UI',[0x292a48,0x337a98]),
            field('flags',0x78,8,'bit0 Visible; bit1 ZBuffered; bit2 Interpolated',[0x292a48,0x337a98]),
            field('renderer_cache',0x80,4,'renderer-owned cached geometry',[0x206218,0x337a98])]},
        {'name':'en2d_command','size':0x34,'fields':[
            field('keys',0,12,'vector<u16> mapping keys',[0x205ce0,0x205dc8,0x337a98]),
            field('bank_id',0xc,4,'interned bank name ID',[0x2062a8,0x337a98]),
            field('cursor_xyz',0x10,12,'float32',[0x2063a0,0x337a98]),
            field('rgba',0x1c,16,'float32',[0x206338,0x337a98]),
            field('carry_cursor',0x30,4,'0 resets cursor, 1 continues previous position',[0x337a98])]},
        {'name':'gaHudAiMap','size':0x8c,'fields':fields},
        {'name':'marker_record','size':0x50,'fields':[
            field('type_id',0,4,'interned Marker Type',[0x1ff7a8]),
            field('basis_and_position',0x10,64,'float32 matrix',[0x1ff7a8]),
            field('position_xyzw',0x40,16,'float32 XYZ + W=1; map reads X/Z only',[0x1ff7a8,0x147038],BOTH)]},
        {'name':'marker_vector','size':12,'fields':[
            field('begin_end_capacity',0,12,'32-bit pointers; count=(end-begin)/0x50',[0x1ff7a8,0x147038],BOTH)]},
        {'name':'ui_primitive_command','size':24,'fields':[
            field('half_width',0,4,'float32',[0x32ee28,0x318e10]),
            field('rgba_bytes',4,4,'R<<24|G<<16|B<<8|A',[0x32edf8,0x318e10]),
            field('type',8,4,'1=line,4=open polyline,5=closed polygon',[0x32ee40,0x32f498,0x32f710,0x318e10]),
            field('vertex_start',12,4,'index in Vec2 array',[0x32f498,0x318e10]),
            field('vertex_count',16,4,'s32',[0x32f498,0x318e10]),
            field('minimum_vertex_count',20,4,'s32',[0x32f498])]},
        {'name':'ui_primitive_vertex','size':8,'fields':[field('xy',0,8,'float32 top-left logical XY',[0x1469f0,0x32f498,0x318e10])]},
    ]}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--elf',type=Path,required=True)
    args=parser.parse_args()
    data=args.elf.read_bytes()
    if hashlib.sha256(data).hexdigest()!=h.ELF_SHA:
        raise ValueError('Unsupported ELF SHA256')
    def word(address): return struct.unpack_from('<I',data,address-0xff000)[0]
    owners={}
    for name,(ctor,table,size) in OWNER_DEFS.items():
        owners[name]={'constructor':va(ctor),'vtable':va(table),'size':size,'type_id':'interned name, not a fixed literal integer',
                      'configure':va(word(table+0x24)), 'initialize':va(word(table+0x34)),
                      'update':va(word(table+0x2c)), 'clone':va(word(table+0x14)), 'evidence':ELF}
    if owners['gaHudAiMap']['update']!=va(0x147038) or owners['gaHudAiMap']['initialize']!=va(0x1461f8):
        raise ValueError('Owner vtable role mismatch')
    calls={}
    for off in range(0x1000,0x30ea74,4):
        w=struct.unpack_from('<I',data,off)[0]
        if w>>26==3: calls.setdefault((w&0x3ffffff)*4,[]).append(va(off+0xff000))
    functions=[]
    for address,label,purpose,offsets in FUNCTIONS:
        export=ROOT/'data'/'ui2'/'elf'/f'{address:08x}.json'
        if not export.exists():
            export=ROOT/'data'/'ui1'/'elf'/f'{address:08x}.json'
        doc=json.loads(export.read_text())
        if int(doc['address'],16)!=address: raise ValueError('Export address mismatch')
        callees={int(c['addr'],16) for c in doc['callees']}
        for instruction in doc['assembly']:
            at=int(instruction.split()[0],16)
            original=word(at)
            if original>>26==3:
                callees.add((original&0x3ffffff)*4)
        functions.append({'va':va(address),'working_label':label,'purpose':purpose,
                          'direct_call_sites':calls.get(address,[]),
                          'callees':[va(c) for c in sorted(callees)],
                          'important_offsets':offsets,'confidence':ELF,
                          'boundary':'direct JAL target or checked vtable entry; ABI inferred from assembly',
                          'indirect_calls':'see owner/renderer slot tables; direct callees are not a complete runtime graph'})
    write('elf-hud-functions.json',{'schema_version':1,'elf_sha256':h.ELF_SHA,'function_count':len(functions),
          'owner_factory':{'intern_name':va(0x1d4040),'registration':va(0x15b190),'registry_holder':va(0x1fc760),
                           'lookup':va(0x1fc500),'clone':va(0x1fc4c0),'xml_parser':va(0x295d58),'hatch':va(0x292a48),
                           'attach_initialize':va(0x21e620),'evidence':ELF},
          'owners':owners,'functions':functions,
          'supersedes_ui1':{'gaHudAiMap_initialize':va(0x1461f8),'gaHudAiMap_update':va(0x147038),
                            'reason':'attach_ai invokes slot +0x34; frame draw is slot +0x2c'}})
    write('hud-runtime-structures.json',structures())
    prior=json.loads((ROOT/'ui'/'hud-elements.json').read_text())
    banks={p['logical_path']:p for p in json.loads((ROOT/'ui'/'psb-manifest.json').read_text())['entries']}
    rows=[]
    for row in prior['authored_scenes']:
        if row['source']!=r'\TNG\DATASCENE\HUD\HUD0.XML':continue
        owner_list=[a['owner'] for a in row['ai_owners']]
        model=row['logical_model_path']; key=int(row['image_bank_index']);bank=banks.get(model)
        index=next((m['image_index_u32'] for m in bank['mappings'] if m['key_u32']==key),None) if bank else None
        local=bank['images'][index]['local_bounds_xyxy'] if index is not None else None
        pos=[float(x) for x in row['authored_matrix']['Row3'].split()[:2]]
        static=row['egg']=='SpeedDial'
        use2d=row['authored_properties']['Use en2d']['Value']=='True'
        conditional=h.sprite_logical_rect(pos,local) if local else None
        if row['egg']=='SpeedNeedle': conditional=h.sprite_logical_rect((557,98),local)
        records=[{'owner':name,'runtime_class':name,'code':owners.get(name),'evidence':ELF if name in owners else UNKNOWN} for name in owner_list]
        rows.append({'authored_name':row['egg'],'owner':owner_list,'XML_position':pos,
                     'runtime_class':'runtime_entity + optional en2d + AI slots','uses_en2d':use2d,
                     'runtime_field_offsets':{'entity_en2d':0x4c,'en2d_translation_x':0x50,'en2d_translation_y':0x54},
                     'PSB_bank':model,'mapping_key':key if bank else None,'image_index':index,
                     'local_rect':local,'final_logical_rect':None,
                     'conditional_logical_rect':conditional,
                     'rect_condition':'identity global UI; zero command cursor; vertical factor=1; before owner deformation' if local else None,
                     'runtime_translation': [557,98] if row['egg']=='SpeedNeedle' else pos if static else None,
                     'update_owner':records,'evidence':BOTH if bank else 'CONFIRMED_BY_BYTES',
                     'unknown':'physical factor/safe-area capture; dynamic owner fields not recovered except Map, dial, needle initialization and rank',
                     'source':row['source']})
    write('hud-runtime-map.json',{'schema_version':1,'elf_sha256':h.ELF_SHA,'status':'PARTIAL',
          'logical_dimensions':[640,480],'screen_equation_condition':'global identity UI; physical vertical factor=1',
          'screen_equation':['tx + local_x - 0.5','480 - ty + local_y - 0.5'],
          'map_exception':{'authored_position_used':False,'center_xy':[74,392],'clip_size':[90,86],'evidence':BOTH},
          'bank_selection':{'authored':'XML bank/key copied into en2d commands','rank':'HUD/newhud by default; RankImageBank can override',
                            'global_style_replacement':'UNKNOWN; no replacement of every HUD0 model established'},
          'elements':rows})
    write('minimap-format.json',{'schema_version':1,'elf_sha256':h.ELF_SHA,'evidence':ELF,
          'source':{'scene_section':'MarkerLists','list_name':'RaceLine','name_id_va':va(0x40e818),
                    'parser':[va(0x1ff618),va(0x1ff6a0),va(0x1ff7a8)],'consumer':va(0x147038)},
          'route':{'point_stride':80,'position_offset':64,'position_representation':'float32 XYZ/W=1',
                   'count':'(end-begin)/80','order':'document order, consecutive pairs; Marker No not sorted by ELF',
                   'segment_breaks':'no authored breaks; clipping creates visible discontinuities',
                   'queue_batching':'146d80 compares odd endpoint against preceding cached even endpoint; ordinary nonzero segments flush separately',
                   'sample_resource':r'\TNG\DATASCENE\RACETEST\ITALYS1.XML','sample_count':293,
                   'sample_decoded_sha256':'56603a9b51f509032a3f15953f161eeaa25044b2c00b5988a73e0c2cbc9c9a92'},
          'transform':{'scale':h.SCALE,'scale_va':va(0x40e5e8),'center_xy':[74,392],'clip_width':90,'clip_height':86,
                       'local_x':'S * (Hz*(Wx-Px) - Hx*(Wz-Pz))','local_y':'S * (Hx*(Wx-Px) + Hz*(Wz-Pz))',
                       'screen_xy':'clipped local XY + center XY','heading_offsets':{'x':120,'z':116},
                       'heading_initial_state':None,'bounds_fit':False,'route_window':'max(last-32,0) <= i < min(last+32,FinishArea/BestMarker)',
                       'clip':'Cohen-Sutherland, inclusive rectangle centered on zero'},
          'vehicle_output':{'wrapper_data_pointer_offset':8,'position_x_offset':240,'position_z_offset':248,
                            'heading_input_offsets':[224,228,232],'secondary_vector_offsets':[24,28,32],
                            'semantic_grade':'position confirmed by flow; forward/velocity names are STATIC_INFERENCE'},
          'player':{'source':'HUD PlayerID, CarN/gaVehicleOutputData','centered':True,
                    'marker_offsets':[[-5,5],[0,-5],[5,5]],'shadow_offset':[3,3],'width':4},
          'opponents':{'source':'Car0..NumCars-1 except player','marker':'two clipped diagonals +/-4 around transformed position',
                       'width':4,'color_source':'Race/CarN/Colour float RGBA; RGB intensity*250, command alpha250'},
          'renderer':{'concrete_vtable':va(0x485a00),'object_primitive_offset':1128,
                      'slots':{'set_color':156,'set_width':164,'line':172,'polyline':188,'polygon':196},
                      'producer':va(0x318e10),'vertex_stride':8,'command_stride':24,
                      'topology':'stroked open/closed triangle strips, two vertices per point; closed repeats first',
                      'gs_position':['CVT.W(16*(x/640*RasterW + 2048-RasterW/2))',
                                     'CVT.W(16*(y/480*RasterH + 2048-RasterH/2))'],
                      'alpha':'command byte shifted right one before packet packing; e.g.250 ->125',
                      'route_style':{'shadow_width':6,'front_width':3,'rgb_float':[0.2,0.6,0.1],'shadow_intensity':127,'front_intensity':250}},
          'MAP128STRIPED':{'participates_in_traced_race_map':False,'evidence':ELF,
                          'scope':'Map -> primitive queues -> 318e10 has no texture or PSB lookup; wider asset consumers UNKNOWN'},
          'offline_scope':'centerlines and player/opponent foreground geometry; exact heading evolution, crossbars and raster joins excluded'})
    print(f'{len(functions)} function records; {len(rows)} HUD0 entities; five owner vtables')


if __name__=='__main__':main()
