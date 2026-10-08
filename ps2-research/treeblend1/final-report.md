Phase: PS2-TREEBLEND1
Repository: D:/Game/Master Rallye/master-rallye-re-general
Branch: master
Starting HEAD: b87d7cf43ed6ab6dd3ef8ace9c268593c4cc2332
Ending HEAD: local phase commit containing this report; exact hash in final Git output and handoff MANIFEST.source_commit
Preflight: CLEAN after user restored master; reference SDK CLEAN

Canonical ELF: b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2,3739852 bytes, fresh verified
PackFS provenance: canonical PAK/000/CNF hashes verified; reused existing extractor; original inputs read-only

tree shader registration: 003a75b8 /name00487610 /vtable00487d08
treeblend shader registration: 003a7468 /name004875e0 /vtable00487d68

tree material handler: 003ae710, mesh mode6
treeblend material handler: 003ae618, mesh mode2

Shared rendering helpers: 391d38/391690,3714e0,3bca80,361a58,31f4e0,31d250,31cd98,312610,311c50,31c438
Principal behavioral difference: tree alpha>64/KEEP,ABE0,ZMSK0; treeblend ATE0,source-alpha blend,ABE1,ZMSK1

TURKEY3 /TURshrub2: node3620664,256 authored visual faces,16 geometric components; no plant-count claim
ITALY_S1 /pinus2: node3706566,64 visual faces,4 shared-edge components; no selected world-coordinate PC match
FRANCE1 control: pinetree3550808,62/80 exact at0.001,80/80 at0.01; original PC source redundancy preserved
Second treeblend course: France1 bush013509209,24/24 strict PC source match, PS2 treeblend/PC tree material difference
Opaque negative control: Turkey3 rustic Hut3429766,139 source faces,object mode15

Vertex attributes: normal/control,UV4,XYZ and sourceRRGGBBAA; loader clamp2..254, cache×0.5,VU FTOI0
Source geometry handling: authored strips,ADC suppression,ordinary matrices/projection/clipping; no foliage generator
Texture resources: five exact original course GXIs; loader/handle/state producer connected; live descriptor/CLUT/alpha conversion unknown

Alpha test: tree GREATER64/KEEP; treeblend disabled; source marker does not describe final GS state
Alpha blend: treeblend (Cs−Cd)×As/128+Cd; tree/object ABE0
Depth test: ZTST2/GEQUAL selected; ZTE inherited
Depth write: tree/object ZMSK0 permitted; treeblend ZMSK1 masked
Draw order: bucket0 before1 within one31cd98 drain; no global opaque/transparent order or distance sort proved

Billboard behavior: specialized billboarding not found in handler/cache/selector0 path
Camera-dependent transform: ordinary object/view/projection and inherited visibility; no foliage-facing basis
LOD/conditional relation: inherited DRESSING1 hierarchy; no tree/treeblend crossfade proved; live selected set UNKNOWN
Wind/animation: time/wind/scroll not found in traced handler/cache/selector0; bounded negative result

VU program: five embedded MPG chunks; selector0/MSCAL0xf; original initialization→upload producer confirmed
CPU packet: cached64-byte vertices; REF/UNPACK four qwords; selector/bounds/state inputs
GS submission: embedded STQ/RGBAQ/XYZF2/XGKICK contract;316b88→30ea80 VIF1 QWC/TADR/CHCR producer
Live VU residency: UNKNOWN; no selected live frame captured

PC geometry counterpart: strict France bush01 match; France pinetree tolerance-controlled match; A/B instance placement unresolved
PC material counterpart: France bush01 tree versus PS2 treeblend; raw PC tag2 flags1/1/1/1 predict generic_alphatest, live course handler not captured
Portability assessment: shared PC surfaces/images can be reused selectively; material identities, alpha conversion,ownership/LOD/live state remain interfaces to resolve

Offline diagnostics: foliage_runtime.py states/cases; original-source compact metadata, no invented geometry
Independent runtime validation: NOT_PERFORMED

Unittest: PASS270 tests,0 failure/error/skip,60.380s
Pytest: PASS270 tests+286 subtests,0 failure/skip,61.04s
Compileall: PASS
Diff-check: PASS; isolated handoff234 tests successful,36 explicit dependencies skipped under pytest
Determinism: identical repeated-case JSON SHA f9c100752acf2f9542ba34f3e88464859a0a0e885add37d21af11093bc871c80

Original files unchanged: PASS,14 original-file hash checks; full canonical container identities preserved
Course SDK unchanged: reference HEAD4244fa0c4d878523c9947f54816bf377cdfb2589, final clean status checked
PC renderer unchanged: no modifications; scoped Git closeout

Commit: local research commit, actual hash in final response/archive manifest; no self-referential hash embedded in its own tracked report
Push: NOT_PERFORMED
Overall status: PS2-TREEBLEND1 STATUS: COMPLETE — bounded static/executable RE

# A. Major discoveries

Treeblend is an actual source-alpha blending mode with depth writes masked. Tree is an alpha-cutout mode with depth writes permitted. Both render existing authored visual strip data through the same cache and common VU path. The source names alone could not establish this; distinct callback fields and original GS bit operations now do.

Neither shader creates billboard rectangles, an LOD transition or animated wind in the traced chain. Camera projection/culling and source hierarchy remain relevant, but they are inherited mesh operations. Sixteen TURshrub2 components and four pinus2 components remain geometric groupings, not plant populations.

France bush01 gives a particularly useful control: all24 unsigned PS2 faces match PC already at the strict profile, yet the PS2 material is treeblend and the PC material is tree. The image also differs,64×64/89 stored alpha values on PS2 versus128×128/15 on PC. Italy pinus2 and France pinetree images, conversely, are identical after the explicitly declared PC row conversion.

# B. Shader semantics

The `$shader` extractor390d98, material resolver391690 and registry3a6c58 select registered callbacks3ae710/tree and3ae618/treeblend. Actual values are mesh+28=6/2,queue+2c=0/1,texture option+3c=0/1,mip coefficient+44=0.20/0.15. +44 is consumed with strip scale by31b8c8; it is not opacity. `$alphatest()` in the material text does not override mode2's later alpha-test-disabled GS state.

See [registration and fields](shader-registration.md) and [side-by-side states](tree-vs-treeblend.md). The inventory preserves original VAs/bounds and interior switch labels separately.

# C. Material-to-mesh chain

Original PSM tag2 owns the material string, texture names and strips. The established hierarchy loader391d38/material resolver391690 and virtual shader callback update that real runtime mesh. Original texture names flow through3714e0/2fd7d0 to cached handles, then through3bca80 and queued keys to311c50. This is materially stronger than printable strings or a texture inventory.

The [five case studies](course-case-studies.md) retain exact nodes/material offsets and source representation. Source triangles are not collision triangles or necessarily simultaneously visible runtime draws.

# D. Vertex and geometry contract

52-byte source vertices become48-byte runtime records and64-byte cache records. Source packed color is RRGGBBAA; runtime channel setters clamp2..254; cache scales by0.5; VU FTOI0 emits RGBAQ integers. NormalXYZ is cached but not used by selector0's coordinate/color path. UVxy,XYZ/control and source tint are consumed; the common secondary geometry stream is NOP.

Authored strips and ADC suppression remain intact. Common clipping can generate clipped vertices without being a plant generator. [Geometry/attributes](foliage-geometry.md) gives the layouts and bounded float32 evaluator.

# E. Transparency, depth and submission

Mode6 writes alpha-testGREATER64/KEEP,ABE0,ZMSK0; mode2 writesATE0,ABE1,ZMSK1. The blend selectors yield `(Cs−Cd)×As/128+Cd`. Both select TCC1/TFXMODULATE and ZTSTGEQUAL, while retaining ZTE and other inherited state. File alpha, runtime texture conversion, vertex alpha, alpha testing and blending are kept separate. The global bit at42df10 is FBA_1, not PABE.

The cache→queue→mode/texture state→REF/UNPACK/MSCAL chain is proved for both modes. Original graphics initialization calls the embedded VU upload producer; selected selector0 bytes transform positions and emit STQ/RGBAQ/XYZF2 with XGKICK. VIF1 hardware submission is an actual QWC/TADR/CHCR producer. [Draw pipeline](draw-pipeline.md) records upload hashes and the exact live-residency boundary.

# F. Billboards, LOD and animation

No specialized billboard basis, distance fade, crossfade or time/wind input exists in the traced callbacks/cache/selector0. Shared region/bound/child selection remains DRESSING1 infrastructure; exact live active sets and all parent predicates are not solved. [Camera/LOD/animation](camera-lod-and-animation.md) states the scope of these negative findings.

# G. Course/PC controls

Turkey3 mode2 and Italy mode6 connect the mandatory source groups to the recovered paths. France pinetree tests tolerance sensitivity and pixel reuse. France bush01 independently verifies another treeblend course and a strict shared-surface material delta. Ordinary hut/object mode15 distinguishes shared renderer machinery from special foliage alpha/depth state.

PC draw54 has48 records but24 unique unsigned triangles; draw283 has320 records but80 unique triangles, all represented in both windings. Those are topology redundancies, not extra trees. PC base alpha-state evidence is original retail research; its application to selected course flags remains a static prediction, not a proxy experiment or live confirmation. See [PC comparison](pc-comparison.md).

# H. Portability implications

Existing PC surfaces and identical images can be reused for selected France/pinus cases. France bush01 would require a material-state distinction plus a deliberate image/alpha choice, not automatically a new mesh. Turkey's unmatched group and Italy's selected placement need separate ownership/LOD work before any transfer. A proxy still needs a reliable material identity interface; alpha textures alone cannot supply it.

Readiness is split into geometry,material,texture,instance,LOD,render-path and runtime categories in [portability notes](portability-notes.md). No PC renderer/SDK/content implementation occurred.

# I. Exact unknowns

* Downstream format/CLUT/alpha meaning of the negated cache-creation option from mesh+3c; filename cache reuse may precede option-sensitive creation.
* Selected live TEX0/CLAMP/mips/TEXA, sampled alpha, PABE/FRAME/ZTE/DATE/DATM and remaining global AD identities at42dea0/42deb0.
* Complete inherited conditional predicates/live child set, independent plant ownership, live global draw sorting/culling and PC course shader invocation.
* Actual live VU micro-RAM residency and a captured visible frame tied to these source meshes; no visual-parity or runtime PASS.

These are explicit precision/runtime/ownership boundaries. They do not substitute speculative billboards, wind, generation or an LOD pair for the recovered authored-strip material path.

# J. Single next phase

Recommend **PS2-AMBIENT2**, a bounded BirdManager spawning/flight/visual presentation reverse. The current material contract is statically closed, while the project priority remains broad PS2 presentation coverage. The next phase is not begun. [next.md](next.md) answers the requested readiness questions.
