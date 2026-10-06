# Findings and corrections retained in this new line

**CONFIRMED_BY_EXE:** normal `d3d8.dll` import; `Direct3DCreate8(120)` at VA
`0x0055905B`, IAT `0x0068F414`. Device creation at `0x0055AB90` uses adapter and
device-type records, DISCARD, one backbuffer, auto-depth, default interval and
MULTITHREADED plus chosen vertex processing. Device loss calls Reset; explicit
mode changes can release/recreate. A substantial engine cache suppresses duplicate
state calls and must be accounted for by future state overrides.

**CONFIRMED_BY_EXE:** common indexed emission `0x00576970` / call `0x00577078`;
alternate fixed-function mesh emission `0x0057F9A0` / call `0x00580242`. Scene
subsystems share the common path. Particle quads use `0x005641C0`, triangle trails
use `0x00571EC0`, UI uses `0x0056D110`, stock textured shadows use `0x00587DB0`.
Application `0x005AFE30` calls frame owner `0x00653080`. Each camera submits
entities, flushes geometry, draws shadows, trails, particles and optional video;
deferred UI and late debug follow all cameras before EndScene/Present.

**STATIC_INFERENCE:** traced material/particle/UI paths use fixed-function
combiners and FVF values. Shader assembler code is linked into the image, but that
alone proves no programmable game draw. Optional assembler validation dynamically
resolves two extra D3D8 exports. A transparent wrapper must not assume those names
are impossible just because they have no IAT entries.

**CONFIRMED_BY_EXE:** renderer parameter setter `0x0056D020` defines near 0.2,
distance scalar 300/400/500, perspective far twice that scalar, and linear fog
start from its span fraction. Sky selection `0x004B1180` chooses cloud resources
and forwards fog color/preset data. Final view/projection is `0x005614A0`.

## Corrections and expansions of read-only sources

1. `research/r-mat1/runtime-material-map.md` says
   "wrapper0053F8B0 (`SetRenderState`, vtable+0xF8)". Fresh receiver/argument
   tracing and instruction `0x0053F921 CALL [..+0xC8]` establish slot 50,
   **+0xC8**. +0xF8 is device GetTextureStageState. The material state/value
   findings still agree with the EXE; the offset correction stays here.
2. `research/r4d_1/texture-stage-map.md` says "No transparent sort pass was
   established" and calls slot1->stage1 a high-confidence inference. These were
   bounded historical findings. Newer read-only R-MAT1
   `transparent-ordering.md` and `texture-stage-binding.md` establish separate
   sorted queues and ordered compiled bindings. This phase reuses that later
   evidence instead of changing the earlier document.
3. PE seed values in state tables are not complete runtime defaults: CRT routines
   `0x0058E6E0` and `0x0058E870` fill additional entries. The new defaults JSON
   preserves both seed and initializer expressions; symbolic source values remain
   unresolved rather than being replaced with assumed zeros.

Read-only sources used: R4D/R4D.1, R-MAT1 runtime/binding/ordering/unknowns,
G1 cameras-executable, R5T render-sort/BSP and foliage correlation notes;
R-EXE1 resource lookup and R-DEV1 editor inventory in the sibling general project.
The last two are external dependencies named in topic files, not copied research.
Retail camera/particle/sky resources were read from the protected external corpus.
Existing tag-100 collision and render-sort planes remain distinct.

Principal unresolved work: semantic object ordering within shared queues;
terrain/road/vegetation ownership;
glass material identity within body resources (body/wheel entity producers now traced);
complete native lighting source; all linked
D3DX call reachability; screenshot path; complete reset recreation callbacks.
These limit completion, not the exact-image facts already established.
