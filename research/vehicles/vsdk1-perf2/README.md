# V-SDK1-PERF2 + V-PAJERO2 delivery

2026-10-24, `research/vehicles`. Original game executables, frozen Subaru/Lancer
resources and UI/audio remain unchanged. All paths below are local private
research outputs relative to the checkout. No retail/GT assets are in the source
handoff archive. No commit or publication was performed.

## Findings and implementation

- Native cached DXT loading issued one four-byte `ReadFile` per pixel. The
  source-hash/preimage-guarded adapter changes only call00558CBA, reads the same
  raw pixels contiguously, and retains native allocation, upload, mip generation
  and ownership. Unknown/archive streams fall back to the original path.
  See [native evidence and failure controls](dxt-bulk-read.md).
- Owner-labelled Lancer re-entry intervals: DXT inclusive4323.4438 ms /81 loads
  before versus72.1251 ms /71 loads after. Both saw611 LRU releases and no texture
  manager clears. The latter directly attests the installed bulk reader. Earlier
  captures predate that attestation; preserve their explicit evidence boundary.
  Counts/actions differ: no60x total-menu or FPS claim. Warm/Pajero after-captures
  remain uncollected. GPU conversion/mips did not dominate these windows.
- Reusable explicit texture quality presets preserve source data and record
  source hashes, dimensions, UV/detail risks and each lossy decision. Final
  Balanced retains256-pixel sponsor/number atlases. [Budget caveats](texture-quality.md).
  Native32 MiB cache is unchanged; no speculative cache retention/size patch.
- Pajero paint coverage follows source-qualified environment pairs. Selected
  unreflected paint area5.5871 ->0 m2 and neighboring mismatches race20/menu25 ->0.
  Glass, rubber, lights and separate overlays are not blanket-reflective.
- Approved headlamp keepout removes only liner/lens intersections. Both lamps
  now have explicit dark open-front housings derived from source aperture/lens
  bounds. The housing is a documented MR approximation, not recovered GT4 mesh;
  oblique silhouette/depth still need gameplay inspection.
- Beta CarModel scalar tween callbacks are now explicitly qualified by original
  ELF hash, VM context and callback indices. This restores the12 original race
  taillamp triangles previously rejected as an unresolved spatial transform.
  Other callbacks remain fail-closed. [Materials/source evidence](../vpajero2/materials.md).
- Front mudflaps22/23 both resolve the original32x32 very dark rubber texture,
  mirrored UVs and morph endpoints. Isolated previews show it on both. No texture
  substitution/UV flip was justified: the reported one-side appearance remains
  open for exact marked-face comparison. Rear lamps' visibility is restored;
  new Pajero native brake/glow qualification is not claimed.

## Candidates

Each final candidate contains the existing30-entry roster: Subaru27, Lancer28,
Pajero29 and the preserved existing entries. Run one candidate at a time.

| Local path under `.research-output/vehicles/` | Purpose |
| --- | --- |
| `vsdk1-perf2/c-perf/Launch-SDK-Roster.cmd` | Original30 resources + profiler, scalar reader control |
| `vsdk1-perf2/c-fast/Launch-SDK-Roster.cmd` | Same364 resources + profiler + bulk reader; measured by owner |
| `vpajero2/c-final-mat/Launch-SDK-Roster.cmd` | New Balanced Pajero materials only; previous donor physics, original reader |
| `vpajero2/c-final-ride/Launch-SDK-Roster.cmd` | Recommended combined check: same new materials, source rest-height datum, bulk reader |
| `vpajero2/c-final-fit/Launch-SDK-Roster.cmd` | Optional: previous row plus source wheelbase/tracks/radii |
| `vsdk1-perf2/c-29/Launch-SDK-Roster.cmd` | Fresh clean29-entry bulk-reader control without Pajero |

Final combined candidates have no frontend profiler. Capture helpers on c-perf
and c-fast explicitly select their own sealed runtime. Performance-only c-fast
preserves all364 control game resources byte-for-byte.

### Fitment boundary

GT4 rest hubs haveY=+0.1452 m. The original Navara50/50 mm setup places hubs at
Y=-0.05 m. A registry-bound reference of-0.1952 m corrects this datum without
changing donor spring rates, mass, engine, steering or XML dimensions. This is
an unloaded attachment comparison, not a settled suspension simulation. Start
with50/50 mm setup and note any saved per-player setup overrides.

The optional fit candidate additionally changes exactly five Pajero XML fields:
wheelbase2.50 m, front/rear tracks1.40/1.38 m, radii0.3652/0.3652 m. These are
source-supported **physical geometry changes**, not harmless visual offsets;
contact/weight-transfer/handling must be compared separately. Unloaded source
hub error is approximately numerical zero, versus293.6 mm maximum donor error.
Donor collision remains unchanged and overhangs the shell; do not claim it fitted.
See [fitment diagnosis and reproducible overlays](../vpajero2/fitment.md).

## Offline acceptance

- Full synthetic suite:766 tests,765 passed,1 skipped; log
  `.research-output/vehicles/vsdk1-perf2/tests-delivery.txt`.
- Each final package passes source reproduction, sealed resource verification
  and all three launcher preflights. Each contains366 sealed resources.
- Actual delivered30-entry helpers pass x86 emulation with controlled native
  call mocks; fresh29-entry control passes separately. Shared allocation remains
  bounded262144 bytes with separate RX code and RW/NX state.
- Actual delivered damage dispatcher passes original-deformer comparisons for
  36 controlled impacts per model; positions/RGB/returns agree, only owned alpha
  is restored. This does not reproduce full gameplay collision sequences.
- Bulk-reader replay preserves pixels for206 old delivered DXT payloads and79
  final Pajero payloads;12 controlled native success/failure/fallback cases pass.
- Final immutable-resource audit preserves283 non-Pajero resources in mat/ride;
  fit preserves282 and changes only vehicles.xml's five Pajero fields. Frozen
  Subaru/Lancer families, all UI/audio and Pajero wheel bytes match the old30
  baseline. Original MRallye.exe and d3d8.dll hashes match the entry snapshot.
- Previewer built and GPU smoke checks passed (handedness, UV vertical direction,
  culling, transparency/depth). Final bundled Balanced captures were inspected:
  `.research-output/vehicles/vpajero2/delivery/` contains front, rear, reflections
  disabled and ride/fit side views. They show unloaded native attachments, not
  dynamic race suspension or native renderer equivalence.
- A pre-existing old29 candidate has a Modifications.xml manifest mismatch
  (mtime12:47, before this work). It was left untouched; integrity was not relaxed.
  Use the newly built c-29 control. The untouched old30 bundle still verifies.

Detailed private evidence: `vpajero2/final-*-regression.json`,
`final-native-capacity.json`, `final-delivered-damage-dispatch.json`,
`final-original-damage.json`, `final-texture-bulk-replay.json`,
`delivery-preservation.json`; `vsdk1-perf2/evidence/benchmark-qualified.json`.

## Owner gameplay check

1. Compare c-final-mat and c-final-ride in Vehicle Select: both headlamp backings,
   no former wedge, body reflection continuity ON/OFF, small lettering/UI.
2. Race Pajero: both lower rear lamps, both sides of the front mudflaps, intact
   and damaged body/reflections, wheels at50/50 mm setup. Mark the exact mudflap
   face if the one-side problem remains. Check the rectangular housing edge at
   oblique angles; it is a fallback shell, not an exact GT4 housing reconstruction.
3. Compare optional c-final-fit separately for track/wheelbase/radius and driving;
   retain c-final-ride if those physical changes are undesirable.
4. Stock/Subaru/Lancer: select/re-enter, race with mixed AI, finish/Results,
   repeated race entry, audio isolation, brakes, crew and damage. Existing SCALE1
   gameplay qualification does not automatically qualify these new packages.
5. Texture residency is tight under the synthetic8 MiB reserve. Record any
   track-specific stutter; do not assume the prediction guarantees every race.

## Reuse

`python tools/vehicle_sdk.py --help` exposes resource/fitment/reflection diagnostics,
frontend captures/comparison and explicit texture normalization. Roster settings
`frontend_profiler` and `frontend_bulk_read` are strict optional booleans; unknown
EXE preimages fail closed. See the linked material/fitment reports for explicit
source-pinned per-car geometry/profile declarations. No numeric MatN-based rules
or hardcoded Pajero branch was added to the shared converter.
