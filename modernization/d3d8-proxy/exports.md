# Relevant D3D8 exports

The inspected x86 Windows runtime SHA256 is
`d61d6c890592e992804fb5a1ed5fc2ce3413177c9ee67f9babaf1d4955884bb4`
(737280 bytes, I386/PE32). These native ordinals were read from its export table;
they are not assumed universal for every replacement runtime.

| Proxy export | Ordinal | Signature | Target evidence |
|---|---:|---|---|
| Direct3DCreate8 | 5 | `IDirect3D8* WINAPI(UINT SDKVersion)` | Static import, IAT VA 0x0068F414 / RVA 0x0028F414; call VA 0x0055905B / RVA 0x0015905B, SDK120 |
| ValidatePixelShader | 2 | `HRESULT WINAPI(const DWORD*, const D3DCAPS8*, BOOL, char**)` | Linked assembler dynamically requests it; game reachability is unproved |
| ValidateVertexShader | 3 | `HRESULT WINAPI(const DWORD*, const DWORD*, const D3DCAPS8*, BOOL, char**)` | Same linked assembler helper |

Factory and validators resolve by name in the explicitly loaded system module.
The .def file assigns the inspected relevant ordinals and exports undecorated
names with x86 stdcall implementation aliases. Arguments/validator outputs and
HRESULTs pass through unchanged. Missing runtime/exports return null for factory
or D3DERR_NOTAVAILABLE for a validator; no fallback renderer is fabricated.

Signature sources: [Wine d3d8.spec](https://github.com/wine-mirror/wine/blob/master/dlls/d3d8/d3d8.spec),
[Wine d3d8_main.c](https://github.com/wine-mirror/wine/blob/master/dlls/d3d8/d3d8_main.c),
and the pinned SDK declaration for the factory. The new read-only Ghidra query of
VA 0x005E311F / RVA 0x001E311F confirms both validator-name lookup paths.
No Wine renderer code is copied.

The host additionally exports @1 Direct3D8EnableMaximizedWindowedModeShim and
@4 DebugSetMute. Neither has target-required evidence and neither is exposed in
this bounded proxy. This is the complete relevant Master Rallye surface, not a
promise of drop-in compatibility for every arbitrary D3D8 program.

`verify_proxy.py` rejects a self import and requires the three named direct
exports with these ordinals. Build verification is not a runtime forwarding test.
