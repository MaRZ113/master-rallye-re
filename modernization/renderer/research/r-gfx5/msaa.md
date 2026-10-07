# Native D3D8 MSAA and preservation risk

R-GFX5-1 **MSAA4 CONFIRMED_BY_RUNTIME**: the human saw smoother vehicle/preview/wheel edges. Session20261007-025535-12772 has successful CreateDevice, 8 successful Reset records, 640x480 / 1920x1027 and effective samples4/DISCARD1. [Hashed current audit](continuation-runtime-evidence.json). This does not validate the new Borderless interaction.

R-GFX5-2 retains the sample selection, format/depth checks, DISCARD/count/flags and bounded native AA fallback algorithm. It removes the whole-image gate from generic AA, integrates the post-native HWND transaction and improves diagnostics. No appearance tuning or new AA method.

`Mode=Stock` ignores `Samples=4`; that value alone never enables AA. Use `Mode=MSAA` and `Samples=4` for a 4x request. Example comments now say this explicitly. Startup quality metadata contains requested mode/samples, effective mode/samples, named swap effect and reason. Caps use the **effective** Windowed flag and color/depth pair after display planning, including Borderless TRUE.

ModeStock forwards original AA. MSAA2/4/8 opt-in checks actual adapter,D3DDEVTYPE,effective color format,Windowed. CheckDeviceType,automatic-depth CheckDeviceFormat/CheckDepthStencilMatch and CheckDeviceMultiSampleType for both color/depth must succeed. Highest8/4/2 <=request chosen; unsupported pairStock. No forced substitute depth/vertex-processing mode.

Pinned D3D8 ABI: numeric sample types2/4/8, D3DSWAPEFFECT_DISCARD=1, COPY=3; 52-byte PP with no D3D9 quality field. Wine primary [D3D8 implementation](https://github.com/wine-mirror/wine/blob/master/dlls/d3d8/device.c) converts those parameters and reserves multisample quality for D3D9; its [D3D8 tests](https://github.com/wine-mirror/wine/blob/master/dlls/d3d8/tests/device.c) check mode-specific caps and Reset multisampling with DISCARD. This supports the API path, not this GPU's support.

Conservative candidate DISCARD1,count1,no LOCKABLE_BACKBUFFER; native Create/Reset remains final legality gate. Ordinary rejection retries Stock AA preserving display, then Stock display: bounded3calls. DEVICELOST/DEVICENOTRESET do not retry. Capability sample descent precedes creation. Fallback uses original AA/swap/count/flags even after echoed effective Reset. No post-process AA/compositor.

Correction: old renderer-recon/device-creation.md calls numeric3 DISCARD. It is **COPY3**. Existing R-GFX4 session requested COPY3,MSAA0,color22(X8R8G8B8),depth77(D15S1). Retained exact depth may limit supported AA; positive synthetic test uses D16 and mock4x, not a hardware claim.

Existing B-ai-multicar,C-ai-edge,frame-5952-d1-00064234 each have one full color/depth Clear(count0,flags3) and one Present(all four argumentsnull). [Hash/count audit](input-evidence.json). Tested normal frames support fully redrawn DISCARD candidate; all frontend/partial updates/backbuffer preservation are not proved. Human E/F must examine world/HUD/menu.

Non-null Present source/destination/HWND/dirty with MSAA forwards real HRESULT, logs msaa_present_hazard and suppresses our AA on next Reset. No fabricated Reset/success. Artifact/partial-update reliance requires AAStock/restart; absent future Reset is not immediate recovery. Surface GetDesc records actual dimensions/format/sample type and releases all references before Reset.

PASS: actual chosen native samples plus clean image/task switching/Reset. Safe unsupported fallback is valid but cannot be called MSAA enabled. Geometry edges may improve while alpha-test foliage texture edges remain jagged. Textures, vertex diffuse, TCI/material appearance and lighting untouched.
