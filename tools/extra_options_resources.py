"""Author the native Extra Options page and extend an isolated SDK bundle.

No game-specific binary format is decoded here. Existing native UI objects,
resource manifests and the unchanged roster patch plan are reused.
"""
from __future__ import annotations
import copy
import hashlib
import json
import os
import shutil
import zlib
import xml.etree.ElementTree as ET
from pathlib import Path
import addon_runtime


def native_setup_page(original: bytes) -> bytes:
    root = ET.fromstring(original)
    section = root.find("./EggLists_Version4/List[@Name='VehicleSetup4']")
    if section is None:
        # The shipped fourth page uses the common VehicleSetup list name.
        section = next((s for s in root.iter('List') if s.find("Egg[@Name='ScreenType']") is not None), None)
    if section is None:
        raise ValueError('native Gearbox page is missing')
    eggs = {e.get('Name'): e for e in section.findall('Egg')}
    if not {'ScreenType','GearType','GearTypeText','ResetToDefault'} <= eggs.keys():
        raise ValueError('unsupported Gearbox layout')

    def value(parent, name, text):
        v = parent.find("Value[@Name='%s']" % name)
        if v is None:
            v = ET.SubElement(parent, 'Value', Name=name, Type='Int' if isinstance(text,int) else 'String', Value=str(text))
        else:
            v.set('Value', str(text))

    def position(egg, x, y, scale=1):
        m = egg.find("Value[@Name='en2d Matrix']")
        m.set('Row0', f'{scale:.2f} 0.00 0.00 0.00')
        m.set('Row3', f'{x:.2f} {y:.2f} 0.00 1.00')

    # Keep each stock control and stock ID. Compact only this page to fit two
    # selectors plus explicit actions in the original 640x480 coordinate space.
    moves = {'GearRatio':(40,322), 'GearRatioSlider':(457,336),
             'GearRatioText':(472,360),'BrakeBiasFront':(583,360),
             'BrakeBiasRear':(363,360),'SliderBar1':(362,326),
             'SliderDots1':(369,350),'GearType':(40,277),
             'GearTypeText':(355,285),'GearLeftArrow':(339,287),
             'GearRightArrow':(591,288),'ResetToDefault':(40,232)}
    for name, xy in moves.items():
        position(eggs[name], *xy)
    for name in ('DescriptionText1','DescriptionText2'):
        value(eggs[name], 'en2d Visible', 'False')
    for e in section.findall('Egg'):
        for ai in e.findall('./AI_List/AI'):
            for control in list(ai)[1:]:
                button=control.find("Value[@Name='Button ID']")
                if button is not None and button.get('Value')=='1':
                    value(control,'Up Path',9)
    # ResetToDefault has a popup rather than a normal button component.
    popup=root.find(".//gaFrontendPopupAI")
    value(popup,'Down Path',5)

    def label(egg, text):
        ai=egg.find('./AI_List/AI/enUITextButtonAI')
        value(ai,'Text*','Null');value(ai,'Text ID#',0)
        value(ai,'Text ID Index#',0);value(ai,'Text String',text.upper())

    for name, title, id_, y, key in (
            ('ExtraPaint','Paint / Livery',5,187,'Paint'),
            ('ExtraTires','Tires',6,142,'Tire')):
        e=copy.deepcopy(eggs['GearType']);e.set('Name',name);position(e,40,y);label(e,title)
        control=e.find('.//gaFrontendMultistateAI')
        for n,v in [('Button ID',id_),('Up Path',id_-1),('Down Path',id_+1),
                    ('StringList*',f'Frontend/ExtraOptions/{key}List'),
                    ('Value*',f'Frontend/ExtraOptions/{key}'),
                    ('CurrentText*',f'Frontend/ExtraOptions/{key}Text')]:
            value(control,n,v)
        section.append(e)
        text=copy.deepcopy(eggs['GearTypeText']);text.set('Name',name+'Value');position(text,355,y+8)
        value(text.find('.//enUITextButtonAI'),'Text*',f'Frontend/ExtraOptions/{key}Text')
        section.append(text)
        for side,x in [('Left',339),('Right',591)]:
            arrow=copy.deepcopy(eggs['Gear'+side+'Arrow'])
            arrow.set('Name',name+side+'Arrow');position(arrow,x,y+10)
            value(arrow.find('.//gaFrontendArrowAI'),'Arrow Status*',f'Frontend/ExtraOptions/{key}{side}Arrow')
            section.append(arrow)
    for name,title,id_,x in [('ExtraApply','Apply',7,40),('ExtraCancel','Cancel',8,235),('ExtraDefaults','Defaults',9,430)]:
        e=copy.deepcopy(eggs['ResetToDefault']);e.set('Name',name);position(e,x,97,.62);label(e,title)
        popup_ai=next(a for a in e.findall('./AI_List/AI') if a.get('No')=='1')
        popup_ai.clear();popup_ai.set('No','1')
        ET.SubElement(popup_ai,'Value',Name='AI Name',Type='String',Value='gaFrontendStandardButtonAI')
        popup_ai.append(copy.deepcopy(eggs['GearRatio'].find('.//gaFrontendStandardButtonAI')))
        control=e.find('.//gaFrontendStandardButtonAI')
        for n,v in [('Button ID',id_),('Up Path',id_-1),('Down Path',1 if id_==9 else id_+1),
                    ('Left Path',9 if id_==7 else id_-1),('Right Path',7 if id_==9 else id_+1)]:
            value(control,n,v)
        section.append(e)
    ET.indent(root)
    return ET.tostring(root,encoding='utf-8')+b'\n'


def extend_bundle(bundle: Path, original_page: bytes, *, stock_archive: Path | None = None, stock_loose: Path | None = None) -> dict:
    """Bundle must be an independent private copy; existing plan stays exact."""
    bundle=Path(bundle)
    manifest=json.loads((bundle/'resource-manifest.json').read_text())
    rows=manifest['resources']
    fallback_count=0
    if stock_archive is not None:
        from master_rallye.vehicle_packaging import _open_sma_archive
        with _open_sma_archive(stock_archive) as archive:
            for item in archive.infolist():
                if item.is_dir():continue
                relative=item.filename.replace('\\','/')
                parts=Path(relative).parts
                if not parts or parts[0].casefold() not in ('datagame','datagx','datascene') or '..' in parts:raise ValueError('unsafe stock member')
                target=bundle/'resource-root'/relative
                if target.exists():continue
                target.parent.mkdir(parents=True,exist_ok=True)
                source=stock_loose/relative if stock_loose else None
                if source and source.is_file() and source.stat().st_size==item.file_size and zlib.crc32(source.read_bytes())==item.CRC:
                    os.link(source,target)
                else:target.write_bytes(archive.read(item))
                rows.append({'path':relative,'size':target.stat().st_size,'sha256':addon_runtime.sha256_file(target),
                             'role':'stock-loose-fallback','owner':'extra-set1'})
                fallback_count+=1
    # Accepted SDK test bundles may intentionally disable the native menus.
    # This playable frontend candidate needs the shipped menu switch enabled.
    dev=bundle/'resource-root/DataGame/dev.xml'
    dev_root=ET.fromstring(dev.read_bytes()) if dev.exists() else ET.fromstring(
        '<Game><Broker><Value Name="Menues/Enabled" Type="Bool" Value="True"/></Broker></Game>')
    menus=dev_root.find("./Broker/Value[@Name='Menues/Enabled']")
    if menus is None:raise ValueError('native menu switch missing')
    menus.set('Value','False')
    dev_raw=ET.tostring(dev_root,encoding='utf-8')+b'\n'
    if dev.exists():dev.unlink() # break inherited hardlink
    dev.write_bytes(dev_raw)
    rows=[r for r in rows if r['path'].casefold()!='datagame/dev.xml']
    rows.append({'path':'DataGame/dev.xml','size':len(dev_raw),'sha256':hashlib.sha256(dev_raw).hexdigest(),
                 'role':'native-extra-options-frontend','owner':'extra-set1'})
    # Use the shipped skip-intro switch for this isolated test host. The old
    # movie player can remain in TitleMode=0 with no media completion callback.
    for relative,key in [('DataGame/frontend.xml','Frontend/SkipTitles'),
                         ('DataGame/options.xml','DirectX/Mode/Fullscreen')]:
        path=bundle/'resource-root'/relative
        tree=ET.fromstring(path.read_bytes())
        item=tree.find("./Broker/Value[@Name='%s']"%key)
        if item is None:raise ValueError('native startup setting missing: '+key)
        item.set('Value','True')
        data=ET.tostring(tree,encoding='utf-8')+b'\n'
        path.unlink();path.write_bytes(data)
        for row in rows:
            if row['path'].casefold()==relative.casefold():row.update(size=len(data),sha256=hashlib.sha256(data).hexdigest())
    relative='DataScene/FrontendScreens/VehicleSetup4.xml'
    raw=native_setup_page(original_page)
    target=bundle/'resource-root'/relative
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        # Break an inherited hardlink instead of mutating its accepted source.
        target.unlink()
    target.write_bytes(raw)
    replacement={'path':relative,'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
                 'role':'native-extra-options-frontend','owner':'extra-set1'}
    rows=[r for r in rows if r['path'].lower()!=relative.lower()]+[replacement]
    rows.sort(key=lambda r:r['path'].lower())
    index=addon_runtime._resource_index(rows)
    manifest.update(resources=rows,resource_count=len(rows),index_sha256=hashlib.sha256(index).hexdigest())
    manifest_raw=addon_runtime.canonical_json(manifest)
    (bundle/'resource-manifest.json').write_bytes(manifest_raw)
    (bundle/'resource-index.tsv').write_bytes(index)
    profile=json.loads((bundle/'runtime-profile.json').read_text())
    profile.update(resource_count=len(rows),resource_manifest_sha256=hashlib.sha256(manifest_raw).hexdigest(),
                   resource_index_sha256=hashlib.sha256(index).hexdigest())
    (bundle/'runtime-profile.json').write_bytes(addon_runtime.canonical_json(profile))
    return {'resource_count':len(rows),'page_sha256':replacement['sha256'],
            'stock_page_sha256':hashlib.sha256(original_page).hexdigest(),
            'roster_operations_changed':False,'native_developer_menus_enabled':False,'archive_changed':False,
            'skip_intro':True,'fullscreen':True,
            'stock_loose_fallback_count':fallback_count}
