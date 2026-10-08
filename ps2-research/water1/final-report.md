| Summary | Result |
|---|---|
| Phase |PS2-WATER1 — water/puddle source content and static rendering contract|
| Repository |D:\Game\Master Rallye\master-rallye-re-general|
| Branch |master|
| Starting HEAD |309fdfd34becdfca3603e626509a697fcaec2ab6|
| Ending HEAD |The commit containing this report; actual SHA in local git-closeout.json/archive manifest and final reply. Resolve: git log -1 --format=%H -- ps2-research/water1/final-report.md|
| Preflight state |Clean master, ahead4 of origin/master; no existing user changes reset|
| Canonical ELF |3739852bytes; b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2|
| TNG corpus |Fresh canonical PAK/000/CNF SHA and size checks; existing PackFS; all values in case-evidence.json|
| PC Course SDK reference |4244fa0c4d878523c9947f54816bf377cdfb2589; research/r5t-course-archaeology,clean/read-only|
| Water material parser |390d98 ->391690 ->3a6c58; direct authored shader extraction/interned registry|
| Puddle shader classification |3aea50, mesh+28=9|
| Water shader classification |3ae9a0, mesh+28=10|
| Waterfall/waterall handling |Separate accepted registrations/handlers; both mode19 and common waterfall maps|
| Surfacetype(water) interpretation |Separate spatial surface identity; narrow puddle ground-color query connection; no blend selection inferred|
| Turkey3 PS2 material |water $surfacetype(water) $shader(puddle), first ASCII offset3429472|
| Turkey3 PS2 geometry |17visual mesh records/51strips/745faces/537distinct XYZ/11diagnostic components|
| Turkey3 PC geometry |939draws/54589vertices/42237triangles; baseline hash reproduced|
| Turkey3 comparison result |0/745 face matches,0/537 vertex matches,0coplanar centroid hits within.001 against all PC draws|
| Additional puddle explanation |Extra authored PS2 visual surfaces within compared compiled landscape, plus mode9 renderer; live frame correlation pending|
| France1 comparison |3586/3586 matched source faces;12puddle+2water+2waterfall meshes|
| ItalyS1 comparison |1329/1329 matched source faces;PS2puddle vs PCwater on corresponding geometry|
| Turkey1 negative control |No local water-related visual mesh or PC candidate; no universal absence claim|
| SpainS2 spelling control |PS2waterfall vs PCwaterall; PS2 ELF accepts both; no silent normalization|
| WATERSURFACE2 |64x64 RGBA candidate,alpha4..131/128values; actual static secondary resource chain proved|
| Course water textures |Retained first water/puddle maps; selected WATER-TGA images opaque at file level|
| Texture bindings |3714e0 ->mesh+dc/+e4 ->3bca80/31d1f8 ->311c50/312130 GS templates|
| UV scrolling |Puddle per-counter cached UV; waterfall two hardcoded scrolling layers; authored +1 not linked to speed|
| Water deformation |No XYZ wave writes in traced auxiliaries; authored surfaces/static coordinate source|
| Alpha blending |Primary44 source-alpha; puddle secondary68/FIX56 additive,TCC0;water secondary44,TCC1|
| Depth test/write |ZTST GEQUAL and ATE0 forced; ZTE inherited;primary ZMSK0,water/puddle secondary ZMSK1|
| Render order |Queue grouping/state-before-geometry proved; global terrain/water ordering not established|
| Water draw path |Mesh/cache ->64-byte records ->mode10/two handles ->VIF packets ->frame chain ->VIF1 DMA|
| Puddle draw path |Same source chain with mode9 and per-frame UV auxiliary; concrete GS template differences|
| Reflection dependency |Static second image and normal-dependent UVs proved; dynamic environment capture not connected; basis ownership UNKNOWN|
| Offline diagnostic |water_runtime.py inspect/compare/contract/waterfall-uv; original geometry remains ignored|
| Independent runtime evidence |NOT_PERFORMED; user Turkey3 observation preserved separately|
| Tests |176 unittest PASS,0skip;176 pytest+184subtests PASS,0skip; includes all prior PS2 tracks|
| Compileall |PASS|
| Diff-check |PASS at closeout|
| Original inputs unchanged |PASS canonical hashes and selected PC source hashes|
| Course SDK unchanged |PASS identical HEAD/clean status; imports suppress bytecode writes|
| PC renderer unchanged |PASS no PC paths changed|
| Commit |research: reverse PS2 water and puddle rendering; actual containing SHA in closeout/final reply|
| Push |NOT_RUN|
| Overall status |**PS2-WATER1 STATUS: COMPLETE at static RE level; runtime NOT_PERFORMED**|

## A. Most important findings

The Turkey3 discrepancy is now grounded in **visual** geometry. The PSM render
tree owns explicit puddle strips and shared vertices, beyond the material-string
survey and beyond GRASS1's spatial triangles. All-PC-draw correspondence plus
an independent surface-height test supports additional authored PS2 landscape
surfaces. This does not infer the visible population from strings or screenshots.

The renderer differentiates ordinary water and puddle using actual modes10/9,
different auxiliary update behavior, secondary alpha combine and blend state.
Both use a course primary texture and common WATERSURFACE2. Waterfall and
waterall are both accepted and override two common images.

## B. Turkey3 explanation

The exact named canonical Turkey3 PSM contains17 puddle mesh records with51
strips. After source control-bit suppression and a declared degeneracy tolerance,
there are745 horizontal source faces and537 distinct positions, forming11
shared-edge components. The first ASCII material offset3429472 reproduces
CDELTA1, but the new result connects that string to an owning mesh/strip range.

The PC SDK independently reproduces939 draws,54589 vertices,42237 triangles
and DX SHA724a69da708a124f7dbfd666b7ad8d391bcaf22ff94bd2c91143e305749cf7f8.
No texture/material candidate is found; more importantly, every PC draw is
included in geometric matching. There are zero matching faces or puddle
positions at.001 coordinate tolerance.22679 other PS2 coordinate positions
match PC, validating the identity alignment without fitting.

All745 puddle centroids project into some PC triangle footprint, yet no PC
surface there is coplanar within.001. Their nearest height gaps have mixed
signs, so it would be wrong to call every face an above-road overlay or visible
puddle. The supported classification is **EXTRA_PS2_VISUAL_GEOMETRY within the
compared compiled landscape**. Live visibility and an unexamined PC runtime or
entity surface are not universally excluded.

The engine does not synthesize these XYZ surfaces in the traced water handlers.
It classifies the authored mesh, modifies color/UV and submits its cached strip
packet. This establishes a content requirement as well as a renderer requirement
for any future Turkey3 reproduction. Full metrics/method/limits are standalone
in [turkey3-delta.md](turkey3-delta.md).

## C. Water material contract

The parser extracts `$shader` directly, interns the literal argument and selects
registered virtual handlers. Waterall is an accepted separately registered name,
not a diagnostic spelling correction. Unknown names retain generic map defaults;
no universal water fallback is invented. `$surfacetype(water)` has a separate
spatial identity path and only a bounded height/color connection to puddles.
See [water-material-contract.md](water-material-contract.md).

## D. Geometry and comparison

The selected visual grammar ends exactly before the separately validated
tag103 spatial block. Materials belong to node2 mesh records and strips directly;
source and runtime vertex layouts are supported by ELF readers/consumers.
The decoder distinguishes VISUAL_SOURCE_STRIP, SPATIAL_SOURCE_TRIANGLE and
ACTUAL_RUNTIME_DRAW. The last category requires live scene/packet evidence.

France1's3586 source faces and Italy_S1's1329 faces all match independent PC
draw geometry. Italy therefore demonstrates different shader behavior on shared
content, while Turkey3 demonstrates extra surfaces. Turkey1 supplies a local
negative, Spain_S2 a literal spelling control. See [geometry](psm-water-geometry.md),
[binding](material-to-draw.md) and [course comparisons](course-comparisons.md).

## E. Water rendering contract

Shader output names reach cached mesh texture handles through3714e0. Mesh draw
sets the same mode/handles and queues a64-byte-per-vertex strip packet. Queue
drain binds textures, selects312610's concrete GS templates, commits them with
eleven-qword VIF state packets and links geometry into the frame chain.
316b88 finalizes the ring;30ea80 writes the actual VIF1 DMA address and start.
317208 writes the upload CALL address442170, linking the embedded VU bytes to
a real CPU upload producer. Live micro-RAM residency is separately uncaptured.

Puddle primary blending uses source alpha; its second layer adds source color
at56/128 with TCC0. Ordinary water's second layer uses alpha and TCC1. Alpha
testing is disabled by these mode templates, while depth enable is inherited;
depth writes are permitted in the first layer and masked in the second for
water/puddle. Waterfall permits writes in both. UV callbacks alter appearance,
not authored XYZ. Actual clock units, basis ownership and final inherited
FRAME/TEXA/ZTE values remain open. See [draw pipeline](draw-pipeline.md),
[state](alpha-depth-and-blend.md), [textures](texture-binding.md),
[animation](uv-and-animation.md) and [owner](water-owner-and-lifecycle.md).

## F. Visual comparison

The user's extra PS2 Turkey3 puddles are consistent with the new source-content
finding, but no controlled screenshot-to-batch correlation was performed.
The secondary additive layer and normal-dependent UVs can explain a distinctive
visual contribution; brightness/reflection appearance alone does not prove a
dynamic mirror or an offscreen water render target. No screenshot-derived
geometry or modern shader approximation is introduced.

## G. Future portability

Turkey3 needs authored surface delivery/material identity plus renderer behavior.
France/Italy already offer matching PC surfaces, making their future work mainly
material/runtime/render handling. A final D3D8 proxy draw does not universally
expose the required original material identity. Course SDK metadata delivery or
an engine hook remains a planning choice, not an implemented feature.
See [pc-portability-notes.md](pc-portability-notes.md).

## H. Exact unknowns and validation

The missing evidence is live scene instance/LOD and visible subset, actual VU
residency, final inherited GS fields, global puddle UV basis ownership, caller
clock units/FCSR, and complete missing-named-texture fallback. These do not undo
the proved authored-content and CPU mode/texture/packet/DMA contracts; they do
prevent a runtime-parity claim.69 function contracts and original word probes
are committed. Full original-corpus regression passed; the targeted runtime
procedure and19-gate matrix are in [validation.md](validation.md).

The focused tool and standalone handoff preserve external input dependencies,
small UI2 metadata fixtures and per-file hashes. Proprietary coordinates, images,
raw decompilations and emulator data remain ignored. No PC/SDK/game assets are
modified, no push occurs, and no other phase begins.

## I. Single recommendation

**PS2-REFL1 — vehicle/environment reflection pipeline**, to survey another major
visual family and resolve wider environment-resource/basis ownership. A later
small water runtime capture would help implementation, but broad graphics/content
survey remains the priority. [next.md](next.md) records the decision. Stop here.
