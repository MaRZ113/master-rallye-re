"""Native menu widget bindings for the common configurable roster builder."""
from master_rallye.addon_sdk.roster_layout import CLASSES

def reorder_scene(data, layout):
    """Move widget ownership, retaining each car's original bank frame and state."""
    import re
    import prepare_vehicle_unlock_overlay as g
    text = data.decode('utf-8-sig')
    changes = []
    for cls in CLASSES:
        canonical = layout['canonical'][cls]
        blocks = {}
        for n, physical in enumerate(canonical):
            a, b = g._egg_span(text, f'{cls}_Car{n+1}')
            blocks[physical] = text[a:b]
        for n, physical in enumerate(layout['class_to_physical_ids'][cls]):
            a, b = g._egg_span(text, f'{cls}_Car{n+1}')
            block = re.sub(r'(<Egg Name=")' + cls + r'_Car\d+(">)',
                           lambda m: m[1] + f'{cls}_Car{n+1}' + m[2], blocks[physical], count=1)
            block = g._replace_value(block, 'X ID', str(n))
            block = g._replace_value(block, 'XPos*', f'Frontend/VehicleSelect/Button{n}XPos')
            changes.append((a, b, block))
    for a, b, block in sorted(changes, reverse=True):
        text = text[:a] + block + text[b:]
    g._parse_xml(text)
    return (b'\xef\xbb\xbf' if data.startswith(b'\xef\xbb\xbf') else b'') + text.encode('utf-8')


def restore_archived_widgets(data, archived, canonical):
    """Recover missing stock widgets from the pinned parent archive, not guesses.

    Older loose overlays can shadow a parent archive's hidden Trooper widget.
    Existing widgets and all their unlock/artwork bindings remain authoritative.
    """
    import prepare_vehicle_unlock_overlay as g
    text=data.decode('utf-8-sig');parent=archived.decode('utf-8-sig');restored=[]
    for cls in CLASSES:
        for n in range(len(canonical[cls])):
            name=f'{cls}_Car{n+1}'
            if f'Name="{name}"' in text:continue
            a,b=g._egg_span(parent,name)
            if n==0:raise ValueError('Missing first stock widget')
            _,end=g._egg_span(text,f'{cls}_Car{n}')
            text=text[:end]+'\r\n'+parent[a:b]+text[end:];restored.append(name)
    g._parse_xml(text)
    return (b'\xef\xbb\xbf' if data.startswith(b'\xef\xbb\xbf') else b'')+text.encode('utf-8'),restored
