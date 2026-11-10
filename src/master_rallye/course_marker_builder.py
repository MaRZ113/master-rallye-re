"""Template-based marker inventory edits with exact preservation of old XML.

New records reuse the selected Course's native structures. Runtime acceptance
of an added inventory remains a candidate gate, independent of lexical safety.
"""
from __future__ import annotations
import math
import re
from xml.parsers import expat

from .course_race_authoring import CourseRaceLogicAuthoring, _read_start_tag_end


def _spans(raw):
    parser=expat.ParserCreate();records=[];stack=[]
    def start(tag,attrs):
        at=parser.CurrentByteIndex;end=_read_start_tag_end(raw,at)
        records.append(dict(tag=tag,attrs=attrs,start=at,open_end=end,parent=stack[-1] if stack else None))
        stack.append(len(records)-1)
    def end(tag):
        row=records[stack.pop()]
        if raw[row['open_end']-2:row['open_end']]==b'/>':
            row.update(close=row['open_end']-2,end=row['open_end'])
        else:
            at=parser.CurrentByteIndex;row.update(close=at,end=_read_start_tag_end(raw,at))
    parser.StartElementHandler=start;parser.EndElementHandler=end;parser.Parse(raw,True)
    return records


def _unique(records, tag, name=None):
    choices=[r for r in records if r['tag']==tag and (name is None or r['attrs'].get('Name')==name)]
    if len(choices)!=1:raise ValueError(f'Need one unambiguous {tag} {name}: found {len(choices)}')
    return choices[0]


def add_split(raw, center, *, radius=None, template_id=None):
    """Append one native trigger and its existing visual companion templates."""
    editor=CourseRaceLogicAuthoring(raw)
    options=[s for s in editor.split_status if s.supported and (template_id is None or s.split_id==template_id)]
    if not options:raise ValueError('No supported native SplitTime template')
    template=options[-1];ids=[s.split_id for s in editor.split_status]
    if None in ids or len(set(ids))!=len(ids):raise ValueError('Repair Split IDs before adding a checkpoint')
    new_id=max(ids,default=-1)+1;name=f'SplitTime{new_id}'
    records=_spans(raw);container=_unique(records,'List','SplitTimes')
    names={r['attrs'].get('Name') for r in records if r['tag']=='Egg'}
    if name in names:raise ValueError('New checkpoint Egg name already exists')
    old=template.egg_name
    selected=[r for r in records if r['tag']=='Egg' and (r['attrs'].get('Name')==old or re.fullmatch(re.escape(old)+r'-[0-3]',r['attrs'].get('Name','')))]
    if not selected:raise ValueError('Split template has no lexical Egg span')
    additions=[]
    for row in selected:
        # Changes are confined to newly cloned records; every old byte survives.
        fragment=raw[row['start']:row['end']]
        fragment=fragment.replace(old.encode('ascii'),name.encode('ascii'))
        additions.append(fragment)
    at=container['close'];result=raw[:at]+b'\n'+b'\n'.join(additions)+b'\n'+raw[at:]
    changed=CourseRaceLogicAuthoring(result)
    added=[s for s in changed.split_status if s.egg_name==name]
    if len(added)!=1 or not added[0].supported:raise ValueError('Cloned checkpoint failed native authoring binding')
    status=added[0];changed.set_split_id(status.identity,new_id);changed.set_split_center(status.identity,center)
    if radius is not None:changed.set_split_radius(status.identity,radius)
    delta=tuple(float(center[k])-template.center[k] for k in range(3))
    for visual in changed.visual_companion_status:
        if visual.split_identity==status.identity and visual.supported:
            changed.set_split_visual_companion_position(status.identity,visual.source_identity,tuple(visual.position[k]+delta[k] for k in range(3)))
    return changed.export()[0],dict(action='add_split_template',egg=name,split_id=new_id,template=old,
                                  extra_time='source template value preserved; semantics UNKNOWN',runtime='REQUIRES_OWNER_TEST')


def remove_split(raw, split_id):
    editor=CourseRaceLogicAuthoring(raw)
    selected=[s for s in editor.split_status if s.split_id==split_id and s.supported]
    if len(selected)!=1:raise ValueError('Select one supported split ID')
    name=selected[0].egg_name;records=_spans(raw)
    rows=[r for r in records if r['tag']=='Egg' and (r['attrs'].get('Name')==name or re.fullmatch(re.escape(name)+r'-[0-3]',r['attrs'].get('Name','')))]
    for row in sorted(rows,key=lambda r:r['start'],reverse=True):raw=raw[:row['start']]+raw[row['end']:]
    return raw,dict(action='remove_split',egg=name,split_id=split_id,unknown_outside_removed_eggs='byte-preserved')


def place_area(raw, name, center, *, half_width=15.0, half_depth=5.0):
    if name not in ('StartArea','FinishArea'):raise ValueError('Unsupported area')
    if not all(math.isfinite(v) for v in (*center,half_width,half_depth)) or half_width<=0 or half_depth<=0:
        raise ValueError('Area dimensions must be positive and finite')
    editor=CourseRaceLogicAuthoring(raw);status=next(s for s in editor.area_status if s.name==name)
    created=False
    if not status.present:
        opposite='FinishArea' if name=='StartArea' else 'StartArea'
        other=next(s for s in editor.area_status if s.name==opposite)
        if not other.supported:raise ValueError('Creating an area requires a supported four-marker native template')
        spans=_spans(raw);template=_unique(spans,'List',opposite);container=_unique(spans,'MarkerLists')
        fragment=raw[template['start']:template['end']].replace(opposite.encode(),name.encode(),1)
        at=container['close'];raw=raw[:at]+b'\n'+fragment+b'\n'+raw[at:]
        editor=CourseRaceLogicAuthoring(raw);created=True
    setter=editor.set_start_marker if name=='StartArea' else editor.set_finish_marker
    for i,(dx,dz) in enumerate(((-half_width,-half_depth),(half_width,-half_depth),(half_width,half_depth),(-half_width,half_depth))):
        setter(i,(center[0]+dx,center[1],center[2]+dz))
    return editor.export()[0],dict(action='create_area' if created else 'place_existing_area',area=name,
                                   native_fields='four Marker Pos fields; Marker Dir preserved',runtime='REQUIRES_OWNER_TEST')


def reorder_split_ids(raw):
    editor=CourseRaceLogicAuthoring(raw)
    for index,status in enumerate(editor.split_status):
        if not status.supported:raise ValueError('Unsupported split binding')
        editor.set_split_id(status.identity,index)
    return editor.export()[0],dict(action='reorder_split_ids',order='existing XML source order',egg_names_and_unknowns='preserved')
