"""Exact retail, read-only PE and indirect-call inventory. No runtime hooks.

Dependencies: pefile, capstone. Offset matches alone are HYPOTHESIS, never COM
proof. Reviewed receiver bindings are independently checked against EXE bytes.
"""
from __future__ import annotations
import argparse
import collections
import datetime
import hashlib
import json
from pathlib import Path

SHA256 = 'bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4'
ROOT = Path(__file__).resolve().parents[1]
METHODS = {
    'IDirect3D8': ('QueryInterface AddRef Release RegisterSoftwareDevice '
        'GetAdapterCount GetAdapterIdentifier GetAdapterModeCount EnumAdapterModes '
        'GetAdapterDisplayMode CheckDeviceType CheckDeviceFormat '
        'CheckDeviceMultiSampleType CheckDepthStencilMatch GetDeviceCaps '
        'GetAdapterMonitor CreateDevice').split(),
    'IDirect3DDevice8': ('QueryInterface AddRef Release TestCooperativeLevel '
        'GetAvailableTextureMem ResourceManagerDiscardBytes GetDirect3D GetDeviceCaps '
        'GetDisplayMode GetCreationParameters SetCursorProperties SetCursorPosition '
        'ShowCursor CreateAdditionalSwapChain Reset Present GetBackBuffer GetRasterStatus '
        'SetGammaRamp GetGammaRamp CreateTexture CreateVolumeTexture CreateCubeTexture '
        'CreateVertexBuffer CreateIndexBuffer CreateRenderTarget CreateDepthStencilSurface '
        'CreateImageSurface CopyRects UpdateTexture GetFrontBuffer SetRenderTarget '
        'GetRenderTarget GetDepthStencilSurface BeginScene EndScene Clear SetTransform '
        'GetTransform MultiplyTransform SetViewport GetViewport SetMaterial GetMaterial '
        'SetLight GetLight LightEnable GetLightEnable SetClipPlane GetClipPlane '
        'SetRenderState GetRenderState BeginStateBlock EndStateBlock ApplyStateBlock '
        'CaptureStateBlock DeleteStateBlock CreateStateBlock SetClipStatus GetClipStatus '
        'GetTexture SetTexture GetTextureStageState SetTextureStageState ValidateDevice '
        'GetInfo SetPaletteEntries GetPaletteEntries SetCurrentTexturePalette '
        'GetCurrentTexturePalette DrawPrimitive DrawIndexedPrimitive DrawPrimitiveUP '
        'DrawIndexedPrimitiveUP ProcessVertices CreateVertexShader SetVertexShader '
        'GetVertexShader DeleteVertexShader SetVertexShaderConstant GetVertexShaderConstant '
        'GetVertexShaderDeclaration GetVertexShaderFunction SetStreamSource GetStreamSource '
        'SetIndices GetIndices CreatePixelShader SetPixelShader GetPixelShader '
        'DeletePixelShader SetPixelShaderConstant GetPixelShaderConstant '
        'GetPixelShaderFunction DrawRectPatch DrawTriPatch DeletePatch').split(),
}

def guarded_output(path):
    p = Path(path).resolve()
    if p == ROOT or not p.is_relative_to(ROOT):
        raise ValueError('Output must be a subdirectory of renderer-recon')
    return p

def require_build(blob):
    digest = hashlib.sha256(blob).hexdigest()
    if digest != SHA256:
        raise ValueError('Wrong build: ' + digest)
    return digest

def hx(value):
    return '0x%08X' % value

def method_candidates(offset):
    if offset < 0 or offset % 4:
        return []
    return [{'interface': interface, 'method': names[offset // 4],
             'vtable_slot': offset // 4, 'vtable_offset': hx(offset)}
            for interface, names in METHODS.items() if offset // 4 < len(names)]

def decode_indirect(blob, start):
    import capstone as cs
    md = cs.Cs(cs.CS_ARCH_X86, cs.CS_MODE_32)
    md.detail = True
    md.skipdata = True
    context = collections.deque(maxlen=12)
    for ins in md.disasm(blob, start):
        if ins.id and ins.mnemonic == 'call' and ins.operands:
            op = ins.operands[0]
            if op.type == cs.x86.X86_OP_MEM and op.mem.base and not op.mem.index:
                matches = method_candidates(op.mem.disp)
                if matches:
                    yield {'va': hx(ins.address), 'bytes': ins.bytes.hex(),
                           'asm': ins.mnemonic + ' ' + ins.op_str,
                           'candidates': matches, 'evidence_grade': 'HYPOTHESIS',
                           'context': list(context)}
        context.append({'va': hx(ins.address), 'asm': ins.mnemonic + ' ' + ins.op_str})

def validate_review(pe, blob, review):
    import capstone as cs
    from capstone.x86 import X86_OP_MEM
    va = int(review['va'], 16)
    slot = METHODS[review['interface']].index(review['method'])
    raw = pe.get_offset_from_rva(va - pe.OPTIONAL_HEADER.ImageBase)
    wanted = bytes.fromhex(review['bytes'])
    if blob[raw:raw + len(wanted)] != wanted:
        raise ValueError('Stale reviewed bytes at ' + review['va'])
    md = cs.Cs(cs.CS_ARCH_X86, cs.CS_MODE_32)
    md.detail = True
    ins = next(md.disasm(wanted, va), None)
    if (ins is None or ins.size != len(wanted) or ins.mnemonic != 'call'
            or ins.operands[0].type != X86_OP_MEM
            or not ins.operands[0].mem.base or ins.operands[0].mem.index
            or ins.operands[0].mem.disp != slot * 4):
        raise ValueError('Review is not the claimed vtable call at ' + review['va'])
    if not review.get('receiver_evidence'):
        raise ValueError('Receiver evidence required')
    extra = {}
    if review.get('owner'):
        extra['owner_rva'] = hx(int(review['owner'], 16) - pe.OPTIONAL_HEADER.ImageBase)
    return dict(review, rva=hx(va - pe.OPTIONAL_HEADER.ImageBase), **extra,
                return_va=hx(va + len(wanted)),
                return_rva=hx(va + len(wanted) - pe.OPTIONAL_HEADER.ImageBase),
                vtable_slot=slot, vtable_offset=hx(slot * 4),
                evidence_grade='CONFIRMED_BY_EXE', source='pristine PE + reviewed Ghidra receiver flow')

def pe_identity(pe, blob, filename):
    base = pe.OPTIONAL_HEADER.ImageBase
    return {'filename': filename, 'size': len(blob), 'sha256': require_build(blob),
            'image_base': hx(base), 'entry_point_rva': hx(pe.OPTIONAL_HEADER.AddressOfEntryPoint),
            'entry_point_va': hx(base + pe.OPTIONAL_HEADER.AddressOfEntryPoint),
            'pe_timestamp': pe.FILE_HEADER.TimeDateStamp,
            'pe_timestamp_utc': datetime.datetime.fromtimestamp(
                pe.FILE_HEADER.TimeDateStamp, datetime.timezone.utc).isoformat(),
            'machine': hx(pe.FILE_HEADER.Machine),
            'sections': [{'name': s.Name.rstrip(b'\0').decode('ascii'),
                'va': hx(base + s.VirtualAddress), 'rva': hx(s.VirtualAddress),
                'virtual_size': s.Misc_VirtualSize, 'raw_offset': s.PointerToRawData,
                'raw_size': s.SizeOfRawData, 'characteristics': hx(s.Characteristics)}
                for s in pe.sections],
            'imported_dlls': [e.dll.decode('ascii') for e in pe.DIRECTORY_ENTRY_IMPORT],
            'evidence_grade': 'CONFIRMED_BY_EXE', 'source': 'PE headers and SHA256'}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('binary', type=Path)
    ap.add_argument('--output', type=guarded_output, required=True)
    ap.add_argument('--reviews', type=Path, default=ROOT / 'data/reviewed-calls.json')
    ap.add_argument('--candidates', action='store_true', help='Also write untyped candidates (large; use .analysis)')
    a = ap.parse_args()
    blob = a.binary.read_bytes()
    require_build(blob)  # Reject before any output or PE parsing.
    import pefile
    pe = pefile.PE(data=blob)
    base = pe.OPTIONAL_HEADER.ImageBase
    reviews = json.loads(a.reviews.read_text(encoding='utf-8'))
    calls = sorted((validate_review(pe, blob, r) for r in reviews), key=lambda r: r['va'])
    if len({r['va'] for r in calls}) != len(calls):
        raise ValueError('Duplicate reviewed call site')
    imports = []
    for entry in pe.DIRECTORY_ENTRY_IMPORT:
        for imp in entry.imports:
            imports.append({'dll': entry.dll.decode('ascii'),
                'name': imp.name.decode('ascii') if imp.name else 'ordinal:' + str(imp.ordinal),
                'iat_va': hx(imp.address), 'iat_rva': hx(imp.address - base),
                'evidence_grade': 'CONFIRMED_BY_EXE', 'source': 'PE import directory'})
    candidates = []
    for s in pe.sections:
        if s.Characteristics & 0x20000000:
            candidates.extend(decode_indirect(s.get_data(), base + s.VirtualAddress))
    a.output.mkdir(parents=True, exist_ok=True)
    def save(name, value):
        (a.output / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    save('build.json', pe_identity(pe, blob, a.binary.name))
    save('imports.json', imports)
    summary = {'schema_version': 1, 'build_sha256': SHA256,
        'coverage': {'scan': 'linear x86 decode of executable sections; skipdata enabled',
            'offset_candidates': len(candidates), 'reviewed_call_sites': len(calls),
            'limitations': 'Not a proof of complete disassembly. Register calls, unanalysed code and child-resource calls may remain. Offset matches alone are not interface identity.'},
        'calls': calls,
        'methods': [{'interface': i, 'method': m,
            'vtable_slot': METHODS[i].index(m), 'vtable_offset': hx(METHODS[i].index(m) * 4),
            'call_sites': [r['va'] for r in calls if r['interface'] == i and r['method'] == m],
            'game_call_sites': [r['va'] for r in calls if r['interface'] == i and r['method'] == m
                                and r.get('usage_scope') == 'game_renderer'],
            'linked_helper_call_sites': [r['va'] for r in calls if r['interface'] == i and r['method'] == m
                                         and r.get('usage_scope') != 'game_renderer'],
            'evidence_grade': 'CONFIRMED_BY_EXE', 'source': 'receiver-reviewed call records below'}
            for i, m in sorted({(r['interface'], r['method']) for r in calls})]}
    save('d3d8-callmap.json', summary)
    if a.candidates:
        save('untyped-candidates.json', candidates)
    lines = ['interface\tmethod\tslot\toffset\tVA\tRVA\treturnVA\treturnRVA\towner\trole']
    lines.extend('\t'.join(str(r[k]) for k in ('interface','method','vtable_slot',
        'vtable_offset','va','rva','return_va','return_rva','owner','role')) for r in calls)
    (a.output / 'd3d8-callmap.tsv').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('Verified retail; %d reviewed calls, %d ambiguous offset candidates' % (len(calls), len(candidates)))

if __name__ == '__main__':
    main()
