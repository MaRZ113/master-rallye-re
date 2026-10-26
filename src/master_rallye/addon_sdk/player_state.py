"""Seed a fresh isolated runtime from a local, unchanged player save.

PlayerState remains an existing mutable runtime-state exception, not an asset
integrity exception. This never changes progression or manufactures unlocks.
"""
import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET

MAX_BYTES=4*1024*1024


def seed_player_state(game_root,resource_root):
    source=Path(game_root)/'DataGame/PlayerState.xml'
    for part in (source,*source.parents):
        if part.is_symlink()or getattr(part,'is_junction',lambda:False)():raise ValueError('Linked player save source rejected')
    if not source.exists():return {'status':'NO_LOCAL_PLAYER_STATE','source':str(source),'copied':False}
    if not source.is_file()or not 1<=source.stat().st_size<=MAX_BYTES:raise ValueError('Player save must be a regular bounded XML file')
    with source.open('rb')as stream:raw=stream.read(MAX_BYTES+1)
    if not 1<=len(raw)<=MAX_BYTES:raise ValueError('Unsupported player save XML')
    try:
        text=raw.decode('utf-8-sig')
        if '\0'in text or '<!DOCTYPE'in text.upper()or '<!ENTITY'in text.upper():raise ValueError('Unsupported player save XML declarations/encoding')
        root=ET.fromstring(raw)
    except (UnicodeError,ET.ParseError)as exc:raise ValueError('Malformed or unsupported UTF-8 player save XML')from exc
    if root.tag!='Game'or root.find('Broker')is None:raise ValueError('Not a qualified Game/Broker player save')
    target=Path(resource_root)/'DataGame/PlayerState.xml'
    for part in (target.parent,*target.parent.parents):
        if part.is_symlink()or getattr(part,'is_junction',lambda:False)():raise ValueError('Linked player save destination rejected')
    target.parent.mkdir(parents=True,exist_ok=True)
    # Fresh builds only: never replace a save from an existing candidate.
    with target.open('xb')as stream:stream.write(raw)
    digest=hashlib.sha256(raw).hexdigest()
    if hashlib.sha256(target.read_bytes()).hexdigest()!=digest:raise ValueError('Player save copy verification failed')
    return {'status':'COPIED_LOCAL_PLAYER_STATE','source':str(source.resolve()),'destination':'DataGame/PlayerState.xml','bytes':len(raw),'sha256':digest,'copied':True,'boundary':'Unchanged local progression snapshot; mutable existing runtime-state path. Unlock availability depends on the supplied save; no progression edited.'}
