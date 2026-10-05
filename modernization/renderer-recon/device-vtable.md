# Receiver-reviewed D3D8 vtable inventory

Exact retail: 224 reviewed call sites; 145 game-path and 79 linked-helper sites.

Offsets are x86 COM byte offsets including IUnknown. Receiver provenance and exact
call bytes are in [JSON](data/d3d8-callmap.json) and [TSV](data/d3d8-callmap.tsv).
A matching offset on an engine object is not a D3D API. All listed sites are
CONFIRMED_BY_EXE code; linked-helper presence does not prove game use.

| Interface | Method | Slot / offset | Game sites | Linked helper sites | First VA / RVA |
|---|---|---|---|---|---|
| IDirect3D8 | CheckDepthStencilMatch | 12 / 0x00000030 | 1 | 0 | 0x0055A074 / 0x0015A074 |
| IDirect3D8 | CheckDeviceFormat | 10 / 0x00000028 | 2 | 0 | 0x00559865 / 0x00159865 |
| IDirect3D8 | CheckDeviceType | 9 / 0x00000024 | 1 | 0 | 0x005597D8 / 0x001597D8 |
| IDirect3D8 | CreateDevice | 15 / 0x0000003C | 1 | 0 | 0x0055ACD7 / 0x0015ACD7 |
| IDirect3D8 | EnumAdapterModes | 7 / 0x0000001C | 1 | 0 | 0x0055951B / 0x0015951B |
| IDirect3D8 | GetAdapterCount | 4 / 0x00000010 | 1 | 0 | 0x005593A9 / 0x001593A9 |
| IDirect3D8 | GetAdapterDisplayMode | 8 / 0x00000020 | 2 | 0 | 0x00559425 / 0x00159425 |
| IDirect3D8 | GetAdapterIdentifier | 5 / 0x00000014 | 1 | 0 | 0x00559414 / 0x00159414 |
| IDirect3D8 | GetAdapterModeCount | 6 / 0x00000018 | 1 | 0 | 0x0055947A / 0x0015947A |
| IDirect3D8 | GetDeviceCaps | 13 / 0x00000034 | 1 | 0 | 0x0055972D / 0x0015972D |
| IDirect3D8 | Release | 2 / 0x00000008 | 1 | 0 | 0x00559094 / 0x00159094 |
| IDirect3DDevice8 | ApplyStateBlock | 54 / 0x000000D8 | 0 | 3 | 0x005E006E / 0x001E006E |
| IDirect3DDevice8 | BeginScene | 34 / 0x00000088 | 1 | 2 | 0x0056BA23 / 0x0016BA23 |
| IDirect3DDevice8 | BeginStateBlock | 52 / 0x000000D0 | 0 | 4 | 0x005DFDE6 / 0x001DFDE6 |
| IDirect3DDevice8 | CaptureStateBlock | 55 / 0x000000DC | 0 | 3 | 0x005E005F / 0x001E005F |
| IDirect3DDevice8 | Clear | 36 / 0x00000090 | 1 | 0 | 0x0056BA1A / 0x0016BA1A |
| IDirect3DDevice8 | CopyRects | 28 / 0x00000070 | 0 | 2 | 0x005E0839 / 0x001E0839 |
| IDirect3DDevice8 | CreateCubeTexture | 22 / 0x00000058 | 0 | 2 | 0x005D9E01 / 0x001D9E01 |
| IDirect3DDevice8 | CreateDepthStencilSurface | 26 / 0x00000068 | 0 | 2 | 0x005E06F7 / 0x001E06F7 |
| IDirect3DDevice8 | CreateIndexBuffer | 24 / 0x00000060 | 3 | 0 | 0x00587958 / 0x00187958 |
| IDirect3DDevice8 | CreateRenderTarget | 25 / 0x00000064 | 0 | 2 | 0x005E06CF / 0x001E06CF |
| IDirect3DDevice8 | CreateTexture | 20 / 0x00000050 | 1 | 4 | 0x005589CD / 0x001589CD |
| IDirect3DDevice8 | CreateVertexBuffer | 23 / 0x0000005C | 3 | 0 | 0x005849B5 / 0x001849B5 |
| IDirect3DDevice8 | DrawIndexedPrimitive | 71 / 0x0000011C | 2 | 0 | 0x00577078 / 0x00177078 |
| IDirect3DDevice8 | DrawPrimitive | 70 / 0x00000118 | 17 | 0 | 0x00564ECA / 0x00164ECA |
| IDirect3DDevice8 | DrawPrimitiveUP | 72 / 0x00000120 | 0 | 1 | 0x005E0490 / 0x001E0490 |
| IDirect3DDevice8 | EndScene | 35 / 0x0000008C | 1 | 2 | 0x0056CE60 / 0x0016CE60 |
| IDirect3DDevice8 | EndStateBlock | 53 / 0x000000D4 | 0 | 4 | 0x005DFFF6 / 0x001DFFF6 |
| IDirect3DDevice8 | GetBackBuffer | 16 / 0x00000040 | 2 | 0 | 0x0055AD3C / 0x0015AD3C |
| IDirect3DDevice8 | GetCreationParameters | 9 / 0x00000024 | 0 | 1 | 0x005EC5F2 / 0x001EC5F2 |
| IDirect3DDevice8 | GetDepthStencilSurface | 33 / 0x00000084 | 0 | 2 | 0x005E0778 / 0x001E0778 |
| IDirect3DDevice8 | GetDeviceCaps | 7 / 0x0000001C | 1 | 1 | 0x0055AD22 / 0x0015AD22 |
| IDirect3DDevice8 | GetRenderTarget | 32 / 0x00000080 | 0 | 2 | 0x005E076B / 0x001E076B |
| IDirect3DDevice8 | Present | 15 / 0x0000003C | 1 | 0 | 0x0055B0DE / 0x0015B0DE |
| IDirect3DDevice8 | Release | 2 / 0x00000008 | 1 | 0 | 0x0055B11A / 0x0015B11A |
| IDirect3DDevice8 | Reset | 14 / 0x00000038 | 1 | 0 | 0x0055AE57 / 0x0015AE57 |
| IDirect3DDevice8 | SetIndices | 85 / 0x00000154 | 3 | 0 | 0x005770C6 / 0x001770C6 |
| IDirect3DDevice8 | SetRenderState | 50 / 0x000000C8 | 19 | 14 | 0x0053F7DD / 0x0013F7DD |
| IDirect3DDevice8 | SetRenderTarget | 31 / 0x0000007C | 0 | 3 | 0x005E0796 / 0x001E0796 |
| IDirect3DDevice8 | SetStreamSource | 83 / 0x0000014C | 7 | 1 | 0x00564F99 / 0x00164F99 |
| IDirect3DDevice8 | SetTexture | 61 / 0x000000F4 | 5 | 2 | 0x00564F4E / 0x00164F4E |
| IDirect3DDevice8 | SetTextureStageState | 63 / 0x000000FC | 37 | 15 | 0x0053F6E9 / 0x0013F6E9 |
| IDirect3DDevice8 | SetTransform | 37 / 0x00000094 | 13 | 0 | 0x0053FA6F / 0x0013FA6F |
| IDirect3DDevice8 | SetVertexShader | 76 / 0x00000130 | 7 | 1 | 0x00564FD7 / 0x00164FD7 |
| IDirect3DDevice8 | SetViewport | 40 / 0x000000A0 | 3 | 4 | 0x0056148B / 0x0016148B |
| IDirect3DDevice8 | ShowCursor | 12 / 0x00000030 | 2 | 0 | 0x0055AD7E / 0x0015AD7E |
| IDirect3DDevice8 | TestCooperativeLevel | 3 / 0x0000000C | 1 | 0 | 0x0055AFB3 / 0x0015AFB3 |
| IDirect3DDevice8 | UpdateTexture | 29 / 0x00000074 | 0 | 2 | 0x005D9AE3 / 0x001D9AE3 |

Not receiver-confirmed here: Get/SetLight, LightEnable, Get/SetMaterial,
GetTransform/GetRenderState/GetTexture/GetTextureStageState,
CreateVolumeTexture, DrawIndexedPrimitiveUP, SetPixelShader/CreatePixelShader/
CreateVertexShader, SetGammaRamp, ResourceManagerDiscardBytes, GetFrontBuffer.
CheckDeviceMultiSampleType and GetAdapterMonitor are also not recovered as root
interface calls. These are bounded NOT OBSERVED findings, not a prohibition on
runtime use. GetCreationParameters/CubeTexture/RT/depth/CopyRects/UpdateTexture/
DrawPrimitiveUP/state blocks are present in linked helpers with unproved reachability.

Candidate scan: 4,434 untyped offset matches; Ghidra listing inventory: 5,027
memory-indirect CALL instructions. Different disassembly coverage accounts for
different counts. Register dispatch and unanalysed code remain outside complete
proof. Every used method has per-site owner/role/receiver/VA/RVA; the summary table
does not replace those records. A proxy still needs a complete 16/97-slot ABI.

`va` identifies the CALL instruction. `return_va`/`return_rva` identify its next
instruction, independently computed from the verified call bytes. A future proxy's
return-PC log must match those return fields, not compare directly with CALL VA.
