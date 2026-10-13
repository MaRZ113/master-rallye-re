# One Tata material: original contract and bounded PC approximation

The selected source material remains PS2 `TATA/CAR.PSM`, mesh `root.3`, node
170755, material offset 170849, `$shader(carshiny)` / internal mode 3. Its
authored texture slots are `tatabon-tga` and `whitepaint-tga`; the original PS2
handler replaces the effective secondary resource with the shared
`CommonTextures\rendertarget64x64`. This material is connected to the verified
PC Tata `car.dx` record 19. The existing exact geometry/owner/resource classifier
is retained. The record includes hood and roof regions; its historical
"bonnet" signature identifier is not broadened into other body materials.

PC source SHA-256:
`45b7bfba6938e259c0ac6d79a42a878a8c66b1e53547a53a6d23343092fb34cb`.
Accepted geometry SHA-256:
`f80ae53d8c8691ebb8387680b0555343e10100459949c56e3338c484b680e669`.
The previous [material-source-contract](../reflection-port1/material-source-contract.json)
retains the original source offsets and PackFS provenance.

## The PS2 source is mixed, not an environment camera

The original [REFL1 writer/lifecycle evidence](../../../refl1/environment-target-lifecycle.md)
establishes a shared mutable texture target. At R5900 call windows `0x33257c`
and `0x3325c8`, helper `0x31a518` receives two passes:

| Pass | Image source | FIX | Destination term | Vertical flip |
|---|---|---:|---|---|
| 1 | Verified ENVSOURCE image | 80 | Zero | No |
| 2 | Current framebuffer | 48 | Existing target | Yes |

The nominal RGB result is
`80/128 * ENV + 48/128 * FlipY(current framebuffer)`, subject to PSMCT16
interpretation, filtering, GS rounding and saturation. The original GXI payload
must match SHA-256
`aa15159a5f3f668244dd3b1c5c7b8322d8f41ac626c3a1741222b797252ad1e4`.
It stays local and is excluded from source archives.

The original `0x330780` sequence draws a resolved model and flushes before
checking the shared update latch. The first eligible call rebuilds the target
once in that presentation pass. It is not proved to be a per-vehicle capture,
an extra environment camera, a cube map or a vehicle-excluding scene render.
Exact live producer/consumer generations remain uncaptured.

## Preserve the actual original PC combination

The live target's stage-1 arguments are `COLORARG1=CURRENT` and
`COLORARG2=TEXTURE`. For this argument order:

```text
MODULATEALPHA_ADDCOLOR (18): Current.rgb + Current.alpha * Texture.rgb
ADD (7):                   Current.rgb + Texture.rgb
```

These equations follow the original fixed-function operation definition, not
an interpretation from the texture's filename or alpha channel. Microsoft
documents [the texture operations and selectors](https://learn.microsoft.com/en-us/windows/win32/direct3d9/d3dtextureop).
The selector values and arguments also appear in the original D3D8 headers
and the two captured target calls. The cited operation definition is shared
fixed-function terminology; it is not a claim that the game uses D3D9.

With Current.alpha equal to 1 the two RGB operations coincide before clamping.
With lower Current.alpha, ADD increases the environment contribution.
The native texture's alpha is not the coefficient in this particular RGB
equation. The compiled target's diffuse alpha values are 255, but that alone
does not prove every runtime stage-0 alpha result is 1. Actual source texture
and stage-alpha combination still matter.

## Mode matrix

| ReflectionMode | Stage-1 texture | Stage-1 COLOROP | Target override mask |
|---:|---|---|---:|
| 0 | Original PC | Original PC | 0: no request |
| 1 | Original ENV RGB scaled by floor(channel * 80/128), A=255 | ADD | 3 |
| 2 | Same weighted ENV image | Preserve original (18) | 2: texture only |
| 3 | Original PC image | ADD | 1: COLOROP only |
| 4 | Bounded mixed static/framebuffer target | ADD | 3 |

Mode 1 remains the legacy pilot policy. Modes 2 and 3 isolate its two changes.
Mode 3 does not require the private GXI or a replacement image. Stock stays the
default for missing/invalid configuration, unsupported builds or unresolved
target identity. Modes requiring an image reject missing or incorrect source
data. No texture-only, draw-ordinal or numerical VB/IB-ID classifier is introduced.

## Mixed-source implementation boundary

The intended Mode-4 source reconstructs both nominal image terms using one
bounded GPU copy and a private 64x64 target. The framebuffer is sampled with
vertical flip; its D3D8 byte weight is RGB 96/255, an approximation to 48/128.
That difference, A8R8G8B8 rendering, filtering and saturation must not be
described as exact PS2 GS output. The original PC camera-space-normal coordinate
generator and texture matrix are retained for this selected material.

The PC capture checkpoint is immediately before the first verified target
draw in a frame. The PS2 writer runs after one eligible model draw in a pass.
This scheduling difference is explicit; the current PC image may contain
earlier vehicle draws, and its content is camera-dependent. No generic dynamic
reflection system or exact original pass scheduling is claimed.

CopyRects transfers compatible color surfaces without scaling; the private
composition pass performs reduction to 64x64. The operation's restrictions are
documented in Microsoft's [archived D3D8 CopyRects reference](https://learn.microsoft.com/en-us/previous-versions/ms889283(v=msdn.10)).
That archived page targets Windows CE; desktop driver support must still be
established from the actual device capabilities and HRESULTs. Unsupported
MSAA, color format, copy or target allocation falls back to the unchanged native
draw. The application depth buffer is neither read nor reformatted.

The original main-target draw remains exactly once with its original HRESULT.
Private image composition does not replay the car. Every temporary native state,
texture, render target, depth target and viewport must be restored before that
draw; failure must retain repair state and prevent a false success report.
Reset and device-loss lifecycle validation is separate from live visual parity.

New mixed-source runtime support and PS2 appearance are **pending user testing**.
Build/mock test results belong to the new final report, not this source contract.
