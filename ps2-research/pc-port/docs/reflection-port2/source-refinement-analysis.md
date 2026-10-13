# PS2-REFLECTION-PORT2 bounded source/refinement audit

This is an analysis input to the integration owner. It does not change the renderer,
accepted Mode4, source assets or live game memory. No new broad executable analysis
was required: the questions are answered by REFL1 original instruction evidence,
source bytes and the existing PC runtime traces.

## Verified Mode4 starting point

The current local session `session-20261013-045023-13620.jsonl` independently
contains successful Mode4 frame310: exact Tata geometry accepted, capture/copy/
capture restoration/apply/native draw/final restoration HRESULTs all0, two private
composition draws, X8R8G8B8 source640x480, no MSAA. The later F10 frame1250 has
the known55-face target call and its native material observations.
`mode4-runtime-witness.json` preserves file hashes and a compact exact event/matrix
window. This is PC runtime proof of execution, not PS2 pixel parity or a new live
probe. Captured pointer values and draw arguments must never become classifier keys.

## Refinement matrix

| Dimension | Original PS2 REFL1 contract | Accepted PC Mode4 | Bounded decision |
|---|---|---|---|
|RGB source|0.625 ENV+0.375 vertically flipped framebuffer|floor(ENV RGB*80/128)+frameRGB*96/255|Retain original coefficients; no arbitrary reflection gain|
|Framebuffer coefficient|48/128=.375|96/255=.376470588|Difference +.001470588, maximum .375 of one8-bit channel before rounding; disclose rather than claim exact|
|Image format|source/destination PSM argument2, PSMCT16|32-bit source, A8R8G8B8 target|A1R5G5B5 destination may approximate target quantization only; capability-gate and retain32-bit fallback|
|Image alpha|writer/body second layer TCC0; FIX-based RGB|target alpha255, stage1 ADD|Do not derive reflection strength from GXI stored alpha|
|Body contribution|base MODULATE then environment DECAL+FIX128 addition|stage0 nativeMODULATE; stage1 ADD|ADD is supported RGB approximation; PC diffuse/lighting remain different|
|Source color|PS2 carshiny auxiliary overwrites RGB by local-normalY gradient|PC original diffuse retained|Do not silently overwrite VBs; this remains an explicit appearance difference|
|Coordinates|normal O*V, U=.5+.5nx',V=.5-.5ny'|CAMERASPACENORMAL+COUNT2; F10 matrix U=.5+.5nx',V=.5+.5ny'|Positive PC Y is observed; sign equivalence across PS2/PC view bases is unproved. Preserve accepted coordinate fallback|
|Projection|position projection separate from env-normal calculation|existing effectivePC projection|Do not introduce reflectionvector/projection-based modern mapping|
|Timing|after first eligible resolved-model draw/flush, shared latch|before first verified material draw each frame|Keep safe checkpoint until exact model boundary exists; a car-panel draw is not the whole model boundary|
|Camera dependence|orientation changes normal mapping; movement may change feedback image|orientation and source framebuffer change|Use same bookmark plus second rotation in A/B; movement/image dependency separated from UV dependency|
|Reset|PS2 cache callbacks/lifecycle partially recovered|release DEFAULT targets/references, realReset reinitialize, echo distinction preserved|Exercise realReset/device loss plus window-mode echo; never reuse oldframe image|
|MSAA|PS2 framebuffer path not desktop MSAA|currentD3D8 copier rejects anyMSAA|Safe compatibility means explicit Stock fallback. Do not invent CopyRects resolve support|

A refined16-bit target is a useful narrow control, but is not exact PSMCT16:
D3D expansion/rounding, filtering, source quantization, PS2 GS dithering/saturation
and effective alpha differ. It must retain Mode4 unchanged and fall back safely if
allocation/caps/native copy or restoration fails. A second material should use the
same single per-frame capture so coverage does not introduce per-car full copies.

An optional Y-sign comparison also needs an independent mode/control and full
native texture-matrix restoration. Flipping the framebuffer source vertically and
flipping the normal-coordinate Y are distinct operations; neither substitutes for
the other. Do not combine every refinement in one A/B and then assign causality.

## Additional verified vehicle: Kia Sportage bonnet

`vehicle-material-audit.json` was freshly regenerated from the original cached
PS2 payload (SHA checked against PackFS provenance) and protected PC retail DX,
using existing REFL1 visual strips/ADC handling and read-only Course SDK.

PS2 KIASPORTAGE/CAR.PSM `root.5`, node186540, material186634 is
`$shader(carshiny)` mode3, authored `kiabon2-tga`+`whitepaint-tga`, effective
secondary shared mutable target. PC KiaSportage/car.dx record14 offset108516 has
234 vertices/618indices/206triangles, same authored slots and flags00000101.
All206 source triangles correspond in both directions at0.001 model-local units.
Its whole-draw bitwise XYZ digest is unique across78 protected-retail vehicleDX
files; six records with one of the two tested index counts were checked.
No parse failures were suppressed.

The additional side material record13 has442PCfaces, all matched to522PS2faces;
80PS2faces have no matching PC triangle under this bounded test. It is a useful
source-control witness but not necessary to broaden the first new vehicle pilot.
Neither source count is a live/selectedLOD polygon total.

### Exact live acceptance requirements

Replace only the hardcoded55faces/48vertices *prefilter* by a small source-derived
layout allowlist including Kia206/234. Preserve all subsequent gates:
current CPU mirrors/generations/revisions, exact XYZ digest, exact-build/camera race
certificate, already-proved native vehicle body semantics, Stock coordinate policy,
opaque material states, exact original texture-stage operations, current2D textures
and known native/effective texture matrix. Cache by generation/revision/range and
clear on Reset. Shape uniqueness cannot replace body/scene ownership.

Do not accept arbitrary206-face meshes, any `kiabon2` texture, historical VB/IB IDs,
preview models, glass, chrome, rubber, wheels or a common callsite. Keep the
carshiny `rubber` exception excluded. Source per-vehicle identity is defined by
resource+record+digest; live player versus opponent identity is a separate oracle.
The existing `reflection_native_integration::snapshot` currently rejects any
non55/48 draw, and the diagnostic currently emits only the Tata digest; both must
be intentionally generalized by the integration owner, not bypassed.

Kia live stage/native-body compatibility remains **pending user runtime**. Its
source flags and PS2 shared handler make it a justified opt-in candidate, not a
runtime-confirmed override. If original live pipeline differs, fail Stock and
retain the exact rejection rather than relaxing stages.

## Suggested one user A/B

Use unchanged game Reflections=ON and renderer VehicleReflections=Stock. Foliage
Mode0/PixelProbe0; keep same course/lighting/car paint/FreeCamera bookmark. For Tata,
compare Stock0 vs acceptedMode4 vs separately declared refinedcontrol. Repeat
Stock/refined for KiaSportage, checking one accepted per-vehicle event and all
HRESULTs. Also check wheels/glass/HUD unchanged, race restart/menu return, one
window-mode toggle and MSAA enabled (expected fallback if unsupported). Save one
F10 per condition; obtain comparable PS2 Tata/Kia screenshots before pixel-parity
claims. No automatic deployment.

## Reproducibility

Executed source audit:
`python ps2-research/pc-port/docs/reflection-port2/source-audit.py`.
The helper uses private cached PS2 payloads and protected PC assets read-only;
report contains only hashes/counts/source offsets/materials/bounds. It needs the
existing read-only Course SDK. No original full mesh arrays or texture bytes are
committed. No native build was performed by this analysis agent.
