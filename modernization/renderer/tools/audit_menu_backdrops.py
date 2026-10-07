"""Read-only XML -> DXB -> DXT backdrop identity manifest; never a draw-order guess.

The manifest is the replacement seam for later upload/content correlation. This
pass does not replace textures or declare a matching native draw from its size.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import xml.etree.ElementTree as ET

SCREENS = ('MainMenu', 'QuickRace', 'QuickModeSelect', 'RaceResults')


def texture_identity(data):
    if len(data) < 20:
        raise ValueError('Short DXT header')
    magic, version, opaque_word, width, height = struct.unpack_from('<5I', data)
    if magic != 0xFEED or not 0 < width <= 16384 or not 0 < height <= 16384:
        raise ValueError('Unsupported DXT header')
    if len(data) != 20 + width * height * 4:
        raise ValueError('DXT payload size mismatch')
    return dict(width=width, height=height, version=version, opaque_word=opaque_word,
                sha256=hashlib.sha256(data).hexdigest(),
                upload_bgra_sha256=hashlib.sha256(data[20:]).hexdigest(),
                alpha_values=sorted(set(data[23::4])))


def bank_references(data):
    if len(data) > 1024 * 1024 or len(data) < 8 or struct.unpack_from('<2I', data) != (0xF001, 125):
        raise ValueError('Unsupported image bank')
    # Identity evidence only: do not claim an unverified generic DXB geometry parser.
    return sorted(set(m.decode('ascii') for m in re.findall(rb'[A-Za-z0-9_]+_000_[0-9]{3}\x00', data)),
                  key=lambda s: s.rstrip('\x00'))


def screen_manifest(corpus, name):
    path = corpus / 'DataScene/FrontendScreens' / (name + '.xml')
    if path.stat().st_size > 4 * 1024 * 1024:
        raise ValueError('Screen XML too large')
    tree = ET.parse(path)
    backgrounds = []
    for egg in tree.iter('Egg'):
        fields = {v.get('Name'): v for v in egg.findall('Value')}
        model = fields.get('en2d Model Name')
        if model is None:
            continue
        resource = model.get('Value', '').replace('\\', '/')
        if not resource.lower().startswith('frontend/backgrounds/'):
            continue
        if '..' in resource.split('/'):
            raise ValueError('Unsafe resource path')
        bank = corpus / 'DataGx' / (resource + '.dxb')
        data = bank.read_bytes()
        tiles = []
        for reference in bank_references(data):
            texture = bank.with_name(reference.rstrip('\x00') + '.dxt')
            tiles.append(dict(resource=texture.relative_to(corpus).as_posix(),
                              **texture_identity(texture.read_bytes())))
        backgrounds.append(dict(role='UI_MENU_BACKDROP', resource=resource,
                                bank_sha256=hashlib.sha256(data).hexdigest(),
                                egg=egg.get('Name'), matrix=fields['en2d Matrix'].attrib,
                                draw_priority=fields.get('Draw Priority').get('Value'), tiles=tiles,
                                native_texture_generation_association='UNKNOWN',
                                evidence_grade='CONFIRMED_BY_ASSET_XML_AND_CONTENT'))
    return dict(screen=name, xml_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), backgrounds=backgrounds)


def extension_layout(aspect):
    if not 1 <= aspect <= 4:
        raise ValueError('Unsupported aspect')
    width = 480 * aspect
    half = (width - 640) / 2
    return dict(canvas=[-half, 0, 640 + half, 480], central_art=[0, 0, 640, 480],
                central_scale=[1, 1], requires_extension=abs(half) > 1e-6)


def audit(corpus):
    return dict(status='BACKDROP_ASSET_EXTENSION_REQUIRED', runtime_extension=False,
                native_draw_role='UNKNOWN_UNTIL_RESOURCE_CONTENT_AND_GENERATION_CORRELATED',
                candidate_owner_va='0x0056D110', candidate_draw_return_rva='0x0016D7C4',
                source='Retail XML, image-bank references, exact DXT content; shared packet owner from pristine Ghidra',
                screens=[screen_manifest(corpus, n) for n in SCREENS],
                replacement_contract=extension_layout(16 / 9),
                constraints=['No horizontal stretch of central art', 'No clipping of buttons or decorations',
                             'No runtime texture writes in this pass', 'No role promotion from draw order alone'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('corpus', type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.corpus), indent=2))


if __name__ == '__main__':
    main()
