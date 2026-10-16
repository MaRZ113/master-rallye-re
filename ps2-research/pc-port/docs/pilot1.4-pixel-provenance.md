> Historical checkpoint: old build paths/hashes below are preserved provenance. For current builds use overlay/README.md and dist/current/build-report.json.

# PC-VISUAL-PILOT1.4 — Targeted Pixel Provenance

Status: `IMPLEMENTED_PENDING_USER_RUNTIME`

The exact France1 `bush01` geometry classifier now arms a one-frame, one-pixel
color probe. It records color immediately before and after the first matching
native draw, optionally after one later indexed draw, and at the boundary before
`Present`. The diagnostic does not change device state, draw ordering, textures,
assets, or geometry. It does not identify the cause of the visibility loss; the
Z-write/overdraw and alpha/texture hypotheses remain open until the game produces
readable checkpoint colors.

## Bounded readback design

The probe accepts only Mode 0 (Stock) and Mode 3 (Z-write-only off). Pixel
coordinates use the active backbuffer's top-left origin. The target continues to
use the established live-course, geometry-signature, resource-generation and
upload-revision classifier; the diagnostic does not use a draw ordinal, texture
name or VB/IB numeric identifier to identify the bush.

At device setup, it checks device caps, the active color surface, format and
scratch-surface creation. At each checkpoint it verifies that the active render
target is the default backbuffer by comparing canonical `IUnknown` identities
from `GetRenderTarget` and `GetBackBuffer`. It fails closed for a non-backbuffer
target, unsupported format, missing capability or any failed HRESULT.

The only color source copies are 1×1 `CopyRects` operations into different
pixels of a private 4×1 non-multisampled render target. There are at most four:
before target, after target, one optional later indexed draw and before Present.
After the scene ends, the probe copies that 4×1 scratch surface to a matching
system-memory image surface, locks only the 4×1 image and decodes only slots
whose source copy succeeded. No full frame is copied or locked. The driver may
still synchronize for a copy; the amount of copied data and the number of
checkpoint calls are bounded, but a zero-stall guarantee is not claimed.

The implementation records only the first matching target draw after it is
armed. Pixel readback is attempted only when `D3DCAPS2_NO2DDURING3DSCENE` is
clear. It also checks the active color format and surface dimensions at every
checkpoint. If the user's live device fails any of these checks, the JSON status
states the failed operation and no fallback readback path is attempted.

The probe reads no depth values. It records the bound depth surface descriptor
when available. The common D24X8 path is reported as not CPU-readable through
`CopyRects`, and `LockRect` is never attempted on the application's depth
surface. D3D8 `CopyRects` excludes depth/stencil surfaces. This diagnostic does
not alter the application's depth format or add a depth readback mechanism.
See Microsoft's [Direct3D 8 `CopyRects` reference](https://learn.microsoft.com/en-us/previous-versions/ms889283%28v%3Dmsdn.10%29).

## Feasibility evidence and limits

A standalone D3D8 feasibility executable was run with the device parameters
recorded for the current setup: HAL, 1920×1080 X8R8G8B8 backbuffer, 4× MSAA,
D24X8 4× depth. It reported `Caps2=0x200a0000` with
`NO2DDURING3DSCENE=0`; creation of a 4×1 scratch render target and matching
image surface succeeded; a 1×1 copy inside `BeginScene` and the final
scratch-to-system-memory copy/lock succeeded. The known test color came back as
`0xff336699`.

That probe verifies API feasibility for the tested device configuration. It is
not a capture from the running game and does not establish that the game's
current render target is the same surface. The injected diagnostic repeats the
capability, surface identity, format, and HRESULT checks against the actual
game device. A live result remains pending.

## Recorded evidence

The one `ps2_pixel_probe_config` event records the requested/effective mode,
pixel, optional later draw ordinal, caps, color/depth surface descriptors, and
scratch allocation HRESULTs. The one `ps2_pixel_probe` event records:

- frame and renderer device identity;
- exact target geometry hash, current buffer generations/revisions, draw
  arguments, target draw HRESULT, mode, requested/applied override mask;
- checkpoint frame and indexed-draw sequence boundary;
- active render target/backbuffer identity and surface format;
- view and projection matrices, viewport and their HRESULTs;
- alpha-test, alpha-blend, blend-factor, Z and color-write render states with
  their HRESULTs;
- texture stages 0–1: color/alpha operations and arguments, texcoord/transform
  state, bound resource identity/type and level-0 descriptor where available;
- depth surface descriptor and explicit depth CPU-read status;
- per-pixel copy, final copy, lock/unlock HRESULTs and decoded RGBA values.

`PixelLaterDrawOrdinal=-1` disables the intermediate checkpoint. A configured
ordinal is zero-based among indexed draws on that device in that frame. The
`before_present` sample reports the draw-count boundary rather than a draw
ordinal. If all four sample slots are used, the finalizer still runs; sample
capacity no longer suppresses the final readback. A real device reset invalidates
pending samples and scratch contents, then re-arms the diagnostic after reset.
Window-mode reset echoes remain outside the extension reset hooks.

## Mode policy

| `FoliageMode` | State request | Effective target-draw change |
| --- | --- | --- |
| `0` | no request, mask `0x00` | Stock; no foliage state override |
| `3` | mask `0x10` | Set only `D3DRS_ZWRITEENABLE=FALSE`; preserve alpha test, alpha blend, source/destination blend and all other native states |

For both modes, the same native target draw is submitted once and the existing
draw-local state transaction restores any overridden state. The probe itself
only reads state and copies one color pixel. Diagnostics are opt-in. No root
cause or PS2 visual equivalence is claimed.

## A/B runtime procedure

1. Use a disposable PC test installation with the PS2-enabled `d3d8.dll` below;
   retain the current proxy so it can be restored manually. No automatic
   installation was performed. Place `PS2Port.ini` beside the renderer INI.
2. Use the same France1 Free Camera bookmark, resolution, camera, game state and
   graphics settings for both runs. Choose one backbuffer pixel one or two
   pixels inside a solid-looking part of the confirmed bush, away from its
   transparent silhouette edge. Use the same coordinate in both runs.
3. First run with `FoliageMode=0`; then repeat with `FoliageMode=3`. Keep
   `PixelProbe=1`, the same `PixelX`/`PixelY`, and
   `PixelLaterDrawOrdinal=-1`. Keep ordinary verbose draw diagnostics off.
   Each run emits a single probe record after the first matching bush draw.
4. Compare `before_target_draw` and `after_target_draw` first. Then compare
   `before_present`. If the target changes the pixel but the later sample does
   not, set `PixelLaterDrawOrdinal` to an indexed draw between those boundaries
   and repeat the same bookmark. Narrow the interval in additional one-frame
   runs; name a specific covering draw only after the sampled pixel changes at
   that measured draw boundary.
5. If the pixel does not change immediately after the target, inspect the
   recorded alpha-test, Z-test, color-write, texture-stage and framebuffer
   metadata. An unchanged single pixel alone does not prove the full bush
   contributed no color; the selected coordinate may miss covered texels or
   fall on a rejected fragment.

Do not compare samples unless their view/projection matrices, viewport, course,
pixel and relevant draw data agree. No alpha amplification, sorting, replay,
extra pass, texture replacement or asset edit is part of this test.

## Build and validation

Locked renderer baseline: `master` at
`3f837f4ddcb27ee1034a4b0753634c92009360ec`. The deterministic overlay stages
from that exact revision; the frozen renderer files were not modified. The
baseline and PS2-enabled variants were built separately with MSBuild parallelism
1. The interface generator ran twice for each variant and was deterministic;
no checked-in generated outputs were rewritten.

| Check | Result |
| --- | --- |
| Baseline Release build | PASS |
| Baseline CTest | PASS, 24/24 |
| Baseline proxy export verification | PASS |
| PS2-enabled Release build | PASS |
| PS2-enabled CTest | PASS, 25/25 (includes `ps2_port_extension_contracts`) |
| PS2 port Python tests | PASS, 10/10 |
| Python compileall | PASS |
| Interface generator, both variants | PASS, deterministic |
| Diff check | PASS |
| In-game checkpoint readback | PENDING USER RUN |

Final PS2-enabled DLL:

`ps2-research/pc-port/.build-overlay-pilot14-final4/ps2-enabled/build/Release/d3d8.dll`

SHA-256: `715314c58edc621b3c0405394b94ca008dc9874febbea684563841506f1da7f8`

The DLL is a PE32 x86 D3D8 proxy and passed export verification for
`Direct3DCreate8`, `ValidatePixelShader` and `ValidateVertexShader`. The build
report is [build-report.json](../overlay/build-report.json). The baseline
renderer SHA is `b4ca8ecf159c8f2c964bd611aca24977247e10ac0c64f17de7e34311d1aea75d`;
the two build outputs are distinct.

The visual-occlusion cause remains unresolved. Current status is
`IMPLEMENTED_PENDING_USER_RUNTIME`; the readback configuration and target
backbuffer identity must be confirmed by the next France1 game capture.
