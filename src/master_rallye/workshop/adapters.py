"""Capability inventory, not an optimistic arbitrary-format importer."""
FORMATS = (
    {'id':'mr-pc-dx','status':'OFFLINE-VERIFIED','gui':'open/inspect; texture-only edits preserve model bytes','backend':'master_rallye.dx / preview_scene','limits':'qualified PC grammar; malformed/unknown records fail parser validation'},
    {'id':'mr-feed-bgra','status':'OFFLINE-VERIFIED','gui':'RGB multiplier, restore','backend':'master_rallye.dxt','limits':'observed FEED wrapper with exact-sized BGRA payload; not generic DDS or DXT compression'},
    {'id':'png-rgba8','status':'OFFLINE-VERIFIED','gui':'same-dimension replacement','backend':'master_rallye.texture_authoring.decode_rgba_png','limits':'qualified existing PNG decoder only; unsupported encodings rejected'},
    {'id':'gt3-qualified-source','status':'CLI-ONLY','gui':'open existing converted SDK project','backend':'tools/vmesh_gt3_to_dx.py','limits':'optional local GT tooling and tested source profiles; no bundled GT resources'},
    {'id':'gt4-beta-modelset2','status':'CLI-ONLY','gui':'open existing converted SDK project','backend':'addon_sdk.gt4_scene / tools/build_gt4_vehicle.py','limits':'qualified Beta profiles, explicit unknown-pass fallbacks; not every GT4 release'},
    {'id':'blender-roundtrip','status':'PLANNED','gui':'not editable','backend':None,'limits':'stable-ID topology round-trip not qualified'},
)

EXTENSION_NAMES = ('glass_panes','paint_masks','transforms','audio_presets','adapters')

def validate_extensions(extensions):
    """Preserve future author metadata without claiming native effect execution."""
    if not isinstance(extensions,dict) or set(extensions)-set(EXTENSION_NAMES):raise ValueError('Unknown extension workspace')
    for name,records in extensions.items():
        if not isinstance(records,list):raise ValueError('Extension records must be a list')
        ids=set()
        for record in records:
            if not isinstance(record,dict) or set(record)!={'id','status','data'}:raise ValueError('Invalid extension metadata')
            if not isinstance(record['id'],str) or not 1<=len(record['id'])<=64 or record['id'] in ids:raise ValueError('Invalid/duplicate extension ID')
            if record['status'] not in ('PLANNED','AUTHORING-METADATA') or not isinstance(record['data'],dict):raise ValueError('Unimplemented extension cannot claim native execution')
            ids.add(record['id'])
    return extensions
