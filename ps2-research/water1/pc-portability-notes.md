# Future PC portability; research only

| Recovered feature | Planning categories | Required interface |
|---|---|---|
| Turkey3 authored puddle surfaces absent from compared PC landscape |COURSE_DATA_PORT,COURSE_SDK_EXTENSION|Validated PS2 visual strip conversion, scene transform/LOD and explicit material assignment|
| Italy shared water geometry classified as PS2 puddle |D3D8_PROXY_RENDER_FEATURE,PC_RUNTIME_HOOK|Stable original course/material identity; geometry already exists|
| France shared water/waterfall surfaces |ASSET_REUSE,D3D8_PROXY_RENDER_FEATURE|Per-surface mode9/10/19, first/second resources and draw state|
| Water/puddle common image and waterfall pair |ASSET_REUSE|Supported GXI conversion with original alpha/texture semantics|
| Puddle UV/color preparation and cache update |PC_RUNTIME_HOOK,REQUIRES_DEEPER_RE|Source normals/XYZ, spatial ground-height query, phase/basis ownership|
| Missing inherited state/live VU confirmation |REQUIRES_DEEPER_RE|Bounded packet/micro-RAM capture before claiming visual parity|

The decoded water surface source is authored geometry, so WATER1 provides no
reason to choose RUNTIME_GEOMETRY_GENERATION for Turkey3 puddle placement.
Generating substitute planes from material names would replace original content
with an invented mechanism.

A proxy cannot reliably recover `puddle` simply from a flat polygon or a
water-colored map. The current PC draw interface does not universally expose
original landscape material strings. France/Italy correspondence supplies
offline identity evidence, not an implemented runtime material identifier.
Future work may need a Course SDK surface/material channel and/or engine hook
in addition to rendering. The final architectural choice is deferred.

Turkey3 is a content-plus-material problem; Italy is primarily a renderer/material
interpretation problem on shared surfaces. A texture-only change cannot restore
Turkey3's missing compiled mesh groups. A wholesale course conversion is also
unnecessary for every course with PS2 puddle metadata.

This phase changes no PC renderer, SDK, course data, wet-surface handling,
weather, physics or game executable. Bounds/counts/addresses and future
classifications are evidence/planning outputs only.
