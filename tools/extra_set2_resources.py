"""EXTRA-SET2 private bundle extension (replaces the EXTRA-SET1 GEARBOX page edit).

Same contract as master-rallye-re-vehicles/tools/extra_options_resources.extend_bundle: the bundle
is an independent private copy, missing stock resources come from the archive, the shipped
Menues/SkipTitles/Fullscreen switches are set for the isolated host, and the resource manifest,
index and runtime profile are rewritten. The only difference is the page set: callers pass the
loose pages to add (GENERAL, Vehicle Select, Ghost Mode select); VehicleSetup4.xml stays stock.
"""
from __future__ import annotations

import hashlib
import json
import os
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path


def extend_bundle(bundle: Path, pages: dict[str, bytes], *, stock_archive: Path, stock_loose: Path | None,
                  sdk_tools) -> dict:
    addon_runtime = sdk_tools
    from master_rallye.vehicle_packaging import _open_sma_archive
    bundle = Path(bundle)
    manifest = json.loads((bundle / 'resource-manifest.json').read_text())
    rows = manifest['resources']
    fallback = 0
    with _open_sma_archive(stock_archive) as archive:
        for item in archive.infolist():
            if item.is_dir():
                continue
            relative = item.filename.replace('\\', '/')
            parts = Path(relative).parts
            if not parts or parts[0].casefold() not in ('datagame', 'datagx', 'datascene') or '..' in parts:
                raise ValueError('unsafe stock member')
            target = bundle / 'resource-root' / relative
            if target.exists():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            source = stock_loose / relative if stock_loose else None
            if source and source.is_file() and source.stat().st_size == item.file_size and zlib.crc32(source.read_bytes()) == item.CRC:
                os.link(source, target)
            else:
                target.write_bytes(archive.read(item))
            rows.append({'path': relative, 'size': target.stat().st_size, 'sha256': addon_runtime.sha256_file(target),
                         'role': 'stock-loose-fallback', 'owner': 'extra-set2'})
            fallback += 1

    def replace(relative: str, raw: bytes, role: str) -> None:
        nonlocal rows
        target = bundle / 'resource-root' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            target.unlink()  # break an inherited hardlink instead of mutating its source
        target.write_bytes(raw)
        rows = [r for r in rows if r['path'].casefold() != relative.casefold()]
        rows.append({'path': relative, 'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'role': role, 'owner': 'extra-set2'})

    def switch(relative: str, key: str, value: str, default: bytes | None = None) -> None:
        path = bundle / 'resource-root' / relative
        root = ET.fromstring(path.read_bytes() if path.exists() else default)
        item = root.find(f"./Broker/Value[@Name='{key}']")
        if item is None:
            raise ValueError(f'native setting missing: {key}')
        item.set('Value', value)
        replace(relative, ET.tostring(root, encoding='utf-8') + b'\n', 'native-startup-setting')

    # Developer menus off; shipped skip-intro and fullscreen switches for the isolated host.
    switch('DataGame/dev.xml', 'Menues/Enabled', 'False',
           b'<Game><Broker><Value Name="Menues/Enabled" Type="Bool" Value="True"/></Broker></Game>')
    switch('DataGame/frontend.xml', 'Frontend/SkipTitles', 'True')
    switch('DataGame/options.xml', 'DirectX/Mode/Fullscreen', 'True')
    page_hashes = {}
    for relative, raw in pages.items():
        previous = bundle / 'resource-root' / relative
        if previous.is_file():
            page_hashes[relative + ' (base)'] = hashlib.sha256(previous.read_bytes()).hexdigest()
        replace(relative, raw, 'native-extra-options-frontend')
        page_hashes[relative] = hashlib.sha256(raw).hexdigest()
    gearbox = 'DataScene/FrontendScreens/VehicleSetup4.xml'
    for r in rows:
        if r['path'].casefold() == gearbox.casefold() and r.get('owner') not in ('extra-set2', None) and r.get('role') == 'native-extra-options-frontend':
            raise ValueError('inherited EXTRA-SET1 GEARBOX page must not be carried forward')
    rows.sort(key=lambda r: r['path'].lower())
    index = addon_runtime._resource_index(rows)
    manifest.update(resources=rows, resource_count=len(rows), index_sha256=hashlib.sha256(index).hexdigest())
    manifest_raw = addon_runtime.canonical_json(manifest)
    (bundle / 'resource-manifest.json').write_bytes(manifest_raw)
    (bundle / 'resource-index.tsv').write_bytes(index)
    profile = json.loads((bundle / 'runtime-profile.json').read_text())
    profile.update(resource_count=len(rows), resource_manifest_sha256=hashlib.sha256(manifest_raw).hexdigest(),
                   resource_index_sha256=hashlib.sha256(index).hexdigest())
    (bundle / 'runtime-profile.json').write_bytes(addon_runtime.canonical_json(profile))
    return {'resource_count': len(rows), 'pages': page_hashes, 'gearbox_page': 'stock', 'roster_operations_changed': False,
            'archive_changed': False, 'skip_intro': True, 'fullscreen': True, 'stock_loose_fallback_count': fallback}
