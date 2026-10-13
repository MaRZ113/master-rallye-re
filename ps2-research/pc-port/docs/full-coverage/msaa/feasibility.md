# D3D8 Mode 4 multisample capture feasibility

Status: IMPLEMENTATION_FEASIBLE_WITH_DRIVER_GATE. Actual 2x/4x game execution is NOT_PERFORMED by this read-only audit. A successful mock call is not native resolve proof.

## Actual existing path

`renderer/reflection_capture.cpp` copies the current main backbuffer into a private single-sample render-target texture, then composes the weighted static environment and flipped framebuffer into a 64x64 texture. The body is drawn once after restoration. `reflection_native_integration.hpp` requests this during the original BeginScene interval, before the first accepted body draw of a frame. Existing code rejects every multisampled source before attempting CopyRects. This rejection is an implementation policy; it does not establish that D3D8 never supports a resolve copy.

The original renderer's `src/quality.cpp` already checks color and optional depth support for 8/4/2 samples and creates a DISCARD swap chain. Reflection capture must neither modify that request nor silently turn multisampling off. Record effective samples, because the existing quality policy may select a lower supported count than requested.

## API evidence and its limits

[Microsoft D3D8 CopyRects documentation](https://learn.microsoft.com/en-us/previous-versions/ms889283(v=msdn.10)) documents a whole-surface copy when the source-rectangle pointer is NULL. Formats must match; stretching, clipping and format conversion are unsupported. This archived Microsoft page is the CE version, so it does not establish unconditional desktop-driver multisample support.

The primary [Wine D3D8 conformance test](https://github.com/wine-mirror/wine/blob/master/dlls/d3d8/tests/visual.c#L8096-L8126) creates a 2-sample backbuffer and a same-size single-sample render target. It expects CopyRects with NULL/0/NULL arguments to succeed and verifies copied color. This supports testing the native API rather than rejecting solely by sample count. That test executes after Present, outside BeginScene, and its destination is a standalone lockable render target. It does not prove the game's inside-scene texture-level destination works on this driver.

The D3D8 device interface has no StretchRect method. [d3d8to9's own implementation](https://github.com/crosire/d3d8to9/blob/main/source/d3d8to9_device.cpp#L410-L494) translates default-pool CopyRects to D3D9 StretchRect. This is translation-layer evidence only. It is not authority to call D3D9 methods on a native D3D8 device or add proxy chaining.

The original Microsoft [GetFrontBuffer documentation](https://alpyne.me/archive/dx8/directx_cpp/graphics/reference/cpp/d3d/interfaces/idirect3ddevice8/getfrontbuffer.htm), reproduced in the DX8.1 SDK archive, concerns a system-memory copy of the presented front buffer. Using it would change the current pre-body framebuffer source, add CPU transfer cost, and potentially capture HUD/desktop content. It is excluded from this iteration.

## Smallest safe implementation

1. Preserve all existing course, material, geometry, resource-generation, main-backbuffer, render-thread and state-block admission gates.
2. Accept only NONE, 2_SAMPLES and 4_SAMPLES in this iteration. Report other sample counts explicitly; do not alter the application device.
3. Preserve the existing NONE path unchanged.
4. For 2x/4x require matching source/destination color format, a single-sample private texture surface, and exact width/height equality. The texture-layout caps/budget checks remain mandatory. If power-of-two/square restrictions require padding, report `msaa_exact_size_copy_unavailable`; no guessed partial resolve or stretch.
5. Issue `CopyRects(source, nullptr, 0, destination, nullptr)` at the existing pre-body checkpoint. Whole-surface arguments and exact dimensions are conservative implementation constraints; Microsoft does not document them as a universal D3D8 resolve capability promise.
6. Only a successful native HRESULT permits composition and material override. On INVALIDCALL/NOTAVAILABLE, report the actual failure and disable further MSAA attempts for this device configuration until a real reset. No old/partially written destination becomes a bound reflection source.
7. Treat DEVICELOST separately from unsupported configuration. No copies/composition on a lost device; existing real-reset cleanup clears target/resource and cached capability state. A window-mode reset echo must not masquerade as capability revalidation.
8. Preserve 16-bit versus 32-bit *composition target* options independently. The resolve destination must keep the source backbuffer format. A1R5G5B5 conversion occurs only through the existing GPU composition draw; CopyRects must not convert a 32-bit source into a 16-bit destination.

This adds no state mutation for the copy itself, no scene break, no CPU readback, no extra original body draw and at most one attempted copy per relevant frame after admission. Composition still requires the existing complete render-target/depth/viewport/texture/stage/shader/stream transaction. Any restoration failure blocks unsafe follow-on behavior through the existing repair contract.

## Required tests and native evidence

Focused mocks: NONE regression; 2x/4x successful whole-surface copy; source/destination dimensions mismatch; unsupported sample count; CopyRects failure before private draws; no repeated failure attempts; no stale ready texture; 16/32-bit composition; loss/reset/resource release; exact native state restoration; original body count and HRESULT.

Human matrix: same vehicle/camera, AA OFF/2x/4x, precision 0/1, windowed and fullscreen where already supported. Log requested/effective samples, source/destination dimensions/formats, copy HRESULT, capture reason, private composition count, original draw count and restore HRESULT. A native successful copy plus expected reflected framebuffer contribution is required before marking a row runtime-confirmed. Capture timing remains the existing first accepted body checkpoint and is not claimed equal to original PS2 timing.

## Local inventory

Read-only inventory found AMD Radeon RX 6600, driver 32.0.21045.5002, plus virtual display devices. Win32 system D3D8 is `C:/Windows/SysWOW64/d3d8.dll`, file version 10.0.26100.9278, SHA256 `d61d6c890592e992804fb5a1ed5fc2ce3413177c9ee67f9babaf1d4955884bb4`. Hardware naming does not prove CheckDeviceMultiSampleType or the inside-scene copy result. No game was launched, no memory was changed, and no source/build was modified by this audit.

Precise remaining blocker if native CopyRects fails: this actual driver/device does not admit the same-format, same-size, inside-scene multisample-to-texture copy needed by the current source timing. GetFrontBuffer or breaking the application's scene would be a different design and is deliberately deferred.

## Subsequent integration and native test

The main agent implemented the exact-size, same-format whole-surface CopyRects
path and tested the production MixedReflectionCapture on a hidden own640x480
native D3D8 device. All six NONE/2x/4x ×16/32-bit cases returned S_OK for capture,
copy, composition, restore and bounded output readback. Actual source samples
matched requested samples; uniform synthetic pixels matched each same-precision
NONE control. See native-smoke-results.json and run_native_smoke.py.

This closes the inside-BeginScene texture-level API feasibility question on the
current driver. Game visuals and performance, otherdrivers/resolutions and
MSAA edge quality remain separate pending checks. The game implementation has
no CPU image readback. The standalone diagnostic's64x64 output readback neither
accesses the game nor reads its depth buffer.
