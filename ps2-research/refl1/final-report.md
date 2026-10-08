| Summary | Result |
|---|---|
| Phase |PS2-REFL1 — vehicle/environment reflection static reverse|
| Repository |D:\Game\Master Rallye\master-rallye-re-general|
| Branch |master|
| Starting HEAD |fa32b51e2036f7c44e41f6382225d29b58577f25|
| Ending HEAD |The containing phase commit; exact SHA in archive MANIFEST/local git-closeout receipt/final reply. Resolve: git log -1 --format=%H -- ps2-research/refl1/final-report.md|
| Preflight state |Clean master, ahead5; no existing user changes reset|
| Canonical ELF |3739852bytes; b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2|
| PackFS |Fresh canonical CNF/PAK/000 hashes before/after; existing tngtool; no new decompressor|
| PS2 vehicle cases |TATA/CAR.PSM and KIASPORTAGE/CAR.PSM; genuine distinct geometry;29-CAR bounded name survey|
| Primary body material |Tata root.3/tatabon, $shader(carshiny); Kia root.4/kiaside2 same mode|
| Reflection material classifier |390d98 ->391690/3a6c58 ->3ade58, mode3; glass3ae040,mode20|
| Material-to-mesh binding |Actual visual tag2 strips; source/material offsets; tag7/8 wrappers; terminal101|
| ENVSOURCE64X64 |Static GXI input, handle container49b388; first mix pass|
| RENDERTARGET64X64 |Initialization image plus mutable GS target49b380; body secondary input|
| STATICRENDERTARGET64X64 |Exists; UNUSED_IN_TRACED_PATH, role elsewhere UNKNOWN|
| WINDSCREEN-REFLECT |Static glass highlight, specialized20 handler, same normal coordinates|
| Environment image source |MIXED_STATIC_AND_FRAMEBUFFER, nominal .625*static +.375*flipped screen|
| Dynamic target producer |330780 ->31a518 twice, actual FRAME/TEX0/sprite writes|
| Target update cadence |32f988 reset; first eligible330780 call; split-screen disables; outer live scheduling not captured|
| Texture cache and binding |Shared name2fd7d0 ->mesh+e4 ->312130; producer2fa058 resolves same target descriptor|
| Normal source |Original source vertex+0 ->runtime48 ->cache64 first qword|
| Camera/view source |3387c8/36fc18/36fb28 ->343458 ->42e2b0/2f0; alternate338ab8 fixed context|
| Coordinate space |Local normal through interpolated object/view row product to biased2D texture coordinates|
| Reflection UV/STQ equation |UV=(.5,.5)+normal dot scaled first two columns of O(w)*V(w); no reflection-vector term|
| Body blend |Primary MODULATE/ABE0; environment DECAL/TCC0, ALPHA29 FIX128 ->Cd+Cs|
| Glass/windscreen |Primary RGBA/source-alpha; static highlight ALPHA68 FIX96 ->Cd+.75Cs; both ZMSK1|
| Chrome/trim |Kia chrome-named secondary replaced by body target; no separate chrome shader proved|
| Lighting interaction |322220 local-normal-Y grayscale .225/.4,RGB clamp2..254,A254; empty frame auxiliary|
| GS state |TCC/TFX/ABE/ATE/ZTST/ZMSK and FIX equations recovered; ZTE/DATE and complete live inherited state remain open|
| VU program |Five canonical MPG chunks; selector1 helper408; initialization/upload producer linked independently|
| Packet producer |31f4e0 cache;31d250/31cd98;matrix317470/317770;strip31d7c8/31e010|
| Final submission |Frame ring316b88 ->30ea80 VIF1 QWC/TADR/CHCR stores|
| Live VU residency |LIVE_RESIDENCY_UNKNOWN; LIVE_FRAME_NOT_CAPTURED|
| Second vehicle comparison |Kia different payload/geometry, same body/glass path; rubber exception reproduced|
| PC native comparison |Original CAMERASPACENORMAL and MODULATEALPHA_ADDCOLOR separated from proxy REFLECTIONVECTOR experiment|
| Offline diagnostic |reflection_runtime.py inspect/resources/coordinates/contract; explicit inputs, original data ignored|
| Independent runtime validation |NOT_PERFORMED; no trusted PCSX2 session; precise read-only capture plan|
| Tests |196 unittest PASS;196 pytest +259subtests PASS,0skip; focused20 PASS|
| Compileall |PASS|
| Diff-check |PASS at closeout|
| Original inputs unchanged |PASS repeated four canonical identities|
| PC renderer unchanged |PASS no diff in renderer/proxy reference paths|
| Course SDK unchanged |PASS clean4244fa0c4d878523c9947f54816bf377cdfb2589; read-only|
| Commit |research: reverse PS2 vehicle environment reflections; actual containing SHA in receipt/archive/final reply|
| Push |NOT_RUN|
| Overall status |**PS2-REFL1 STATUS: COMPLETE at static RE level; RUNTIME_VALIDATION: NOT_PERFORMED**|

## A. Most important discoveries

The target name really denotes written texture storage in the selected system.
The executable combines a static64x64 environment image with a vertically flipped,
downscaled current framebuffer using two GS sprite passes. This is more specific
than “dynamic reflections”: no separate reflection camera or cube-map traversal
was found in this producer. A shared gate allows the first eligible object per
presentation reset to update it; split-screen disables the selected update path.

Vehicle body and glass are independent resource choices. Body mode3 generally
overrides authored paint/chrome secondary images with this target; glass mode20
uses static WINDSCREEN-REFLECT. Both use normal-based second coordinates, with
different primary alpha/depth behavior and secondary addition weights.

## B. What the resources are

ENVSOURCE is a loaded static mix input; RENDERTARGET has an original initialization
image and a proved FRAME writer/TEX0 consumer; WINDSCREEN-REFLECT is a static
material highlight. STATICRENDERTARGET is not referenced by the selected owner or
handlers and has no active role proved here. It is not declared universally unused
or aliased with the active target. Exact hashes, source ranges, dimensions/alpha
and separate loader/consumer evidence are in reflection-resource-inventory.md and
resource-evidence.json. File alpha never substitutes for a GS blend coefficient.

## C. Actual vehicle material pipeline

Two canonical CAR.PSM visual trees bind readable material names to actual tag2
mesh strips. Vehicle-specific tag7 raw names and tag8 indices are decoded as
wrappers; terminal101 and the following undecoded trailer are preserved. The
decoder reuses WATER1's tag2 and vertex reader, leaving its landscape defaults
strict. Tata has3262 source vertices/31mesh records; Kia3559/31. Their shader
counts and selected offset/bounds facts are frozen separately from the evaluator.

390d98's direct shader extraction and interned registry select3ade58/3ae040, which
write mode3/20 and secondary names.3714e0 binds the resulting cache handles.
Tata painted root.3 and Kia root.4 provide concrete body cases; Tata root.0
carflat is a same-model non-environment control. Kia rubber retains its authored
secondary but still uses mode3 normal coordinates. A chrome-named secondary is
replaced by the body target and does not establish a distinct chrome renderer.

## D. Original mathematics and input ownership

The source normal is model-local; cached UVxy belongs to the primary image.
Object matrices come from current/conditionally retained transform state3628c0,
whose rotation retention compares two axes against0.9;3432b8 sends the exact
cache+70/+30 rows. The racing camera helper constructs/inverts an orthogonal
basis and supplies two view matrices via343458. VU matrix helpers interpolate
each pair using319.w and multiply the stored row matrices.408 computes normal
dot products with scaled first/second product columns and adds0.5 bias.

This contains no vertex-to-eye vector, normalized reflected vector, sphere-map
division or inverse-transpose correction. Projection is used elsewhere for
position output. The embedded initialization sets319.w=0; another updater exists
but its CPU invocation/cadence was not established. The diagnostic requires an
explicit weight and matrices, rather than inventing live defaults. Translation
does not enter the normal direction equation; moving through the world can still
alter the framebuffer source image independently. See environment-coordinate-math.md
for equations, original instruction addresses and numerical precision boundaries.

## E. Static and dynamic source chain

32f988 resets42dd38 and sets42dd34=!SplitScreen.330780's first eligible model call
resolves source49b388/target49b380, drains initial image uploads, then emits31a518
sprites. The first pass uses FIX80,D=zero; the second uses FIX48,D=destination and
flipY. Actual EE arguments select PSMCT16, not a guessed flag from3b2190.
The target is sampled by the material name overridden at load. The nominal color
mix is0.625static+0.375screen, with GS conversion/filter/saturation still relevant.

This is a global cached target within the traced owner, not a proved per-car target
or ping-pong resource. Exact live allocation, target contents, callback teardown,
outer frame schedule and which generation a given draw sees remain unconfirmed.

## F. Body, glass, trim and lighting distinctions

Body RGB preparation is a local-normal-Y grayscale calculation in322220, using
(.225*ny+.4)*255 with clamp2..254 andA254;31f4e0 halves byte colors for GS input.
Its empty per-frame auxiliary does not implement a view/light specular computation.
The primary paint is modulated by prepared RGB. Secondary DECAL/TCC0 is added
using ALPHA29/FIX128. Glass instead has an alpha primary and a static highlight
added with FIX96; both its passes mask depth writes. Texture alpha data, alpha
testing, blend coefficients and depth writing are kept distinct.

## G. GS/VU contract and proof boundary

Mode3/20 and mesh+dc/+e4 feed the shared mesh-cache/queue pipeline. CPU templates
312610/311c50/312130 are serialized into primary/secondary state packets, selector1,
matrix packets and source strips. The original uploaded five-MPG program matches
the selected normal helper, GIF output and XGKICK, while frame-chain316b88/30ea80
reaches actual VIF1 DMA register stores. These are executable producer/consumer
links, not an attribution based solely on nearby VU bytes.

Complete inherited GS state, live VU code/residency, frame packet and exact converted
texture pixels have not been captured. Reporting them UNKNOWN does not erase the
strong static material/source/math/submission chain. gs-state-and-blending.md and
draw-pipeline.md specify forced versus inherited fields and upload status explicitly.

## H. PC comparison and future portability

Native PC evidence uses CAMERASPACENORMAL and a stage1 color addition weighted by
current alpha. The proxy's ViewDependent2D/REFLECTIONVECTOR was an experiment,
not the retail PS2 mechanism. PS2 source feedback, prepared colors and FIX-based
addition are concrete differences; visual strength attribution still requires a
controlled comparison. The existing PC study does not establish its image producer
merely by recording a2D environment stage.

A future port may need source image conversion, vehicle material identity, draw-local
blend/color rules and the correct feedback timing. Normal-coordinate machinery
already has a related PC native counterpart, so switching to reflection-vector
coordinates is not automatically faithful. Missing identity/timing interfaces are
documented; no D3D8/vehicle/SDK implementation was performed.

## I. Exact remaining questions

Live interpolation319.w/its updater invocation; target allocation and callback
teardown330770/330778; actual frame before/after33257c/3325c8; full inherited
CLAMP/TEXA/FRAME/ZTE/DATE; named-child/LOD/player/opponent activation; live VU
residency; source/target converted pixels and visible parity. The undecoded vehicle
trailer and broader STATICRENDERTARGET/rear texture consumers remain outside scope.
No screenshot or synthetic preview upgrades any of these to runtime confirmation.

## J. Single next phase

**PS2-GEOM1**, read-only cross-platform visual geometry reconstruction/delta mapping.
This best serves the current breadth-first presentation survey using WATER1's
landscape and REFL1's vehicle foundation. Targeted live reflection validation stays
deferred. No next phase has begun; see next.md for the decision and dependencies.
