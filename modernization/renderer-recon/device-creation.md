# Device construction and resolution lifecycle

**CONFIRMED_BY_EXE:** singleton VA `0x006F9CF0` is built by `0x0053EED0`;
singleton+0x20 owns the device manager. Manager+0x64 is IDirect3D8, +0x68 is
IDirect3DDevice8. Accessor `0x0053F050` returns the latter.

`CreateDevice_0055AB90`, API call VA `0x0055ACD7` (RVA `0x0015ACD7`), takes:

| Argument | Exact source/behavior |
|---|---|
| Adapter | manager+0x18 selected ordinal |
| D3DDEVTYPE | selected 0xFC-byte device record DWORD+0; HAL/REF/SW depend on enumeration/selection, not assumed HAL always |
| hFocusWindow | manager+0x60 |
| Behavior | software VP 0x20; hardware VP 0x40 when selected preference and caps 0x10000 permit; pure hardware 0x50 when caps 0x100000 also permit; **OR 0x4 MULTITHREADED in every case** |
| Parameters | manager+0x28, 13 DWORDs, cleared before population |
| Output | manager+0x68 |

| D3DPRESENT_PARAMETERS | Value/source |
|---|---|
| Width, Height | fullscreen selected mode DWORD0/1; windowed client rectangle manager+0x178..0x184 |
| Format | fullscreen mode+0x18; windowed adapter record+0x438 current desktop format |
| Count | 1 |
| MultiSampleType | selected device record+0xE0; enumeration initializes0 (NONE) at0055976A; active value still needs logging |
| SwapEffect | 3, DISCARD |
| hDeviceWindow | manager+0x5C |
| Windowed | selected device record byte+0xF9 |
| EnableAutoDepthStencil | manager byte+0x194, constructor `0x00558D50` sets 1 |
| AutoDepthStencilFormat | mode's depth-format vector +0x20, selected index +0x40 |
| Flags | 0; no lockable-backbuffer flag here |
| FullScreen_RefreshRateInHz | 0 |
| FullScreen_PresentationInterval | 0, DEFAULT; not proof of vsync being off |

Enumeration `0x00559340` checks adapter modes/type/formats/caps. Depth matching
`0x0055A030` calls CheckDeviceFormat and CheckDepthStencilMatch. Actual selected
depth format is still runtime-dependent. Enumeration reads the candidate list at
VA `0x006E93C8` in order: 80 D16, 73 D15S1, 77 D24X8, 75 D24S8, 79 D24X4S4,
71 D32, then applies the match checks. A proxy must return
real caps/results and preserve this decision process, not hardcode a preferred
format. `0x0055AB00` retries creation with alternate mode-selection helpers.

Options seam `0x00542000` reads DirectX/Mode adapter, width, height, depth,
fullscreen and hardware preferences; width/height/depth fallback is 640/480/16.
`0x005422E0` publishes the selected configuration to Broker. A window constructor
also initializes a 400x300 client-size request; that is a separate startup value,
not the selected game resolution.

`0x0055AD22` is **GetDeviceCaps**, not GetDisplayMode (slot7/+0x1C).
GetBackBuffer/GetDesc populate manager+0x140 surface description after create and
reset, then release the temporary surface. Mode changes may destroy/recreate;
lost-device recovery uses Reset. See [reset](device-reset.md). No widescreen work
or aspect patch participates in this pristine-image analysis.
