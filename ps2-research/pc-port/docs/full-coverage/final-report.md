Phase: PS2 Visual Parity — Full Vehicle & Course Coverage
Repository: D:/Game/Master Rallye/master-rallye-re-general
Branch: master
Starting HEAD: f9673101b94d2d04407b314de87cac6b08efb4c9
Ending HEAD: recorded by release-provenance.json in the handoff
Preflight: five previously modified documentation files and existing untracked research preserved
Frozen renderer tree: e33386bcf682db6983380c499e4928726c758fe0; unchanged
Staging source: immutable commit0bddf7c7bc5e95831f98714ff6231da05ab073ea
PS2 ELF: b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2
PC EXE: bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4
Course SDK: 4244fa0c4d878523c9947f54816bf377cdfb2589; clean, read-only
Vehicle audit:29 PS2 models,26 PC families,78 PC DX files
Reflection admission:174 exact source signatures,24 compatible PC families
Paint/other reflective groups:99/75
Vegetation admission:36 courses,72 verified category resources
Source terrain matches:194771/197088 eligible faces;2317 nonexact faces excluded
Derived points:8914029, no density thinning
Artifact bytes:113814796
MSAA: native API NONE/2x/4x with both16/32-bit targets and output readback,6/6 PASS
Game MSAA/new-car/new-course A/B: PENDING_USER
Baseline/PS2 builds: Win32 Release, serial --parallel1, PASS
CTest:24/24 baseline,30/30 PS2-enabled; all private resources configured
Port unittest/pytest:112/112;258 pytest subtests
Research unittest/pytest:345/345;290 pytest subtests
Vehicle/course focused audits:6/8 PASS
Frozen renderer Python:188 PASS,1 import ERROR (missing external pefile)
Exports/generator determinism/compileall/diff-check: PASS
Native resource test performance:1.104seconds; sampled peak working set125501440bytes
Game menu/race FPS: PENDING_USER
Baseline DLL SHA256:011dd9a94155d216d0c0dde28e0af97f5b72226aae5be97016f2d767ebdf7138
PS2-enabled DLL SHA256:d8ca8584afe7285af7a087419b9af1c578e67aa8c7396345caa50e9db77bbdf4
Original assets/renderer/Course SDK modified: NO
Physics/HUD implementation: PAUSED
Deployment/push: NONE
Overall status: IMPLEMENTED_FULL_VERIFIED_SOURCE_COVERAGE_PENDING_GAME_AB

## Reflection coverage

Independent agents audited every available original PS2 car model and PC family.
`vehicles/coverage.md` is the complete matrix; `registry-candidates.json` retains
PC draw ownership, original flags/slots, source offsets/hashes, PS2 material
association, exact triangle correspondence and corpus-wide uniqueness.

Every accepted group uses original PS2 carshiny mode3 and the common render-target
secondary source. All PC faces match an unconditional PS2 material mesh at .001.
The 75 non-paint groups are genuine carshiny regions, sometimes actual body
panels, as well as trim/decals/wheel-associated geometry. They are not admitted by
chrome/perspex names. All174 exact float32 geometry hashes are unique to their
vehicle family across78 PC models. Tata/Kia signatures remain unchanged.

ReflectionCoverage=0 retains the original Tata-only pilot;1 enables the full
registry. Stock is still ReflectionMode=0. Current race/body owner, VB/IB resource
generation and revision, exact layout, native/effective states, native camera
coordinate policy and current texture generations remain mandatory. No source
draw ordinal is a persistent runtime identity. The bounded geometry cache grew
from16 to256 slots and includes primitive count in its generation-sensitive key.
Logs are bounded per vehicle and report genuine generic source groups instead
of incorrectly labeling every new group as Tata.

Forester has only partial geometric correspondence:13/400 side,28/71 rear,8/54
light faces. Forklift's untyped body/metal1 materials lack a proved carshiny
interpretation. Both are excluded. MoonBuggy/Tank/Wooldand have no exact PC
counterpart. No increased tolerance, guessed alias or texture-only admission.

The working Mode4 coefficients, native coordinates and framebuffer capture
timing are preserved. Existing GS-to-D3D color normalization, native coordinate
basis and capture cadence differences remain approximations; this release does
not establish pixel-level PS2 parity.

## MSAA

The existing blanket MSAA rejection was replaced by a bounded same-format
whole-surface native CopyRects attempt for2x/4x. Source and copy texture dimensions
must be identical; padded power-of-two layouts and other sample counts are
explicitly unsupported. There is no front-buffer substitution, CPU framebuffer
readback in the game, extra body draw, D3D9 call or automatic AA change.

Driver INVALIDCALL/NOTAVAILABLE failures prohibit further resolve attempts until
real Reset. Device loss remains repair/reset controlled. Existing copy, private
composition, target lifetime, native-state repair and original draw HRESULT
contracts remain unchanged.16-bit allocation has the established explicit32-bit
fallback with diagnostic reporting.

`msaa/native-smoke-results.json` proves production capture on the current native
D3D8 driver in a hidden own640x480 device. All six NONE/2x/4x ×16/32-bit cases
returned successful copy/composition/restoration and CPU readback. Uniform
synthetic output matched the same-precision non-MSAA control. It confirms this
API configuration, not game visuals, antialias edge quality or every driver and
resolution. The game must still report actual samples, target format and HRESULT.

## Course coverage and performance

All36 original courses contain verified grass/shrub source directives. Each now
has two separately hash-pinned resources and an exact authored certificate ID.
Independent route evidence and source transforms establish game coordinates;
only eligible source faces with exact compiled PC triangle correspondence are
used.2317 nonexact faces are excluded, not silently moved onto similar terrain.
Existing Turkey3/France1/ItalyS1 artifacts reproduce byte-exactly.

The two global originals GRASS1/BUSH1 are retained, along with original source
scale/lift and float32 placement. FranceW and FranceWFlip require the tightly
raised300000-point file cap; maximum288863. Visible guard16384 remains unchanged.
All9x9 spatial-bin windows are conservatively below2997 points/category. No
thinning or course-position copying. Original incremental PS2 placement history,
VU output and billboard mapping are still known approximation boundaries.

The existing preload/caching lifecycle is retained: opted-in resources load and
validate once at startup, then persist across course switches/restarts/resets;
GPU texture changes occur only at source switches/reset. This costs108.5MiB of
derived files, but introduces no source scans or disk reads on the render-frame
path. A metadata-only/lazy loader was considered; it would introduce new race
thread loading/admission behavior, so it is not part of this bounded expansion.
The complete native mock resource/reset test measured1.104seconds and~120MiB
peak working set. Actual menu/race FPS and resource behavior require user runs.
The existing menu preflight, HUD cache, foliage/water and Free Camera paths were
preserved. Physics and HUD replacement were not resumed.

## Validation, handoff and next action

Exact overlay patches and both generator outputs remain deterministic. Both
ordinary and PS2-enabled builds use the same reusable roots; baseline source
tree and DLL hash remain unchanged. Native tests cover all174 registry entries,
fail-closed owner/state/resource cases, partial setters and exact restoration,
all36 course switches, resets and MSAA success/rejection/failure paths.

The independent Python renderer suite retains its pre-existing missing-pefile
import failure; it was not hidden or repaired through frozen-source changes.
All applicable PS2 research/port suites passed, with external corpora declared
and used. Full logs reside under the ignored `.build/logs/`; compact results
and executed commands are included in the handoff.

`coverage-matrix.json`, `validation.json`, `runtime-ab.md` and the preset provide
reviewable source coverage and one manual A/B procedure. The compact archive
contains sources/tests/patches/evidence and both DLLs, with SHA-256 manifest,
but no original meshes/textures or private grass assets. Those72 assets remain
locally available under `.assets/grass/` for manual use.

Next: controlled full-coverage in-game A/B, beginning with a new reflective car
and FranceWFlip plus2x/4x AA. Do not begin another material, physics or HUD port
until these runtime observations have been assessed.
