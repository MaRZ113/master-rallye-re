# Vehicle Fidelity — completed source / offline milestone

26 October 2026. Branch research/vehicles. Work continues from 1eeb45f;
source/offline milestone completed. This is not gameplay qualification or a new release.

## Owner-requested paint correction

The earlier flat Classic fields removed imported baked shading while adjacent
bonnet, bumper and lamp-surround atlases retained it. Local RGB harmonisation
trials did not remove every visible transition and were not approved.
The reviewed reusable path now separates paint policy from decal selection:
`preserve_source` retains source-import paint atlas bytes, draw RGB/alpha,
UVs and material/environment records. Qualified small sponsor overlay omissions,
approved cover reduction, recessed opaque wheels and selected stock tyre/glass
semantics remain independent. Source red/charcoal artwork replaces the earlier
flat redraw; exact previous graphic pixel equivalence is not claimed.

Studio Paint/Style and the shared CLI/Core offer Recipe default, Preserve source
paint and Regenerate qualified fields. Frozen old recipes keep the old default;
the new pinned Lancer material recipe selects source preservation. Rebuild starts
from immutable source, not a prior trial. Approval remains exact-report gated.

Current version: private fidelity/versions-10/classic-report.json,
SHA256 ff0925d61e160e43504370a6f1326ef5c7d29f9e86e27cd8dfbc63c469047abf.
Resources are byte-identical to versions-09 (120 owned project inputs); the
versions-09 Windows captures therefore show this same resource state.
Owner explicitly approved this exact report. Three isolated candidates are built in private fidelity/t/a, b and c.

## Other implemented work, offline boundaries

- Shadow Studio: original/donor/auto/custom, shared compiler, immutable baseline,
  support threshold/scales/offsets/margins, history/reopen, ground/top guides.
  Texture opacity, game model/collision/physics and shared retail files untouched.
- Exact stock tyre radial/tread mapping with unchanged tyre geometry and hubs;
  stock-derived optical glass pattern with explicit mixed-banner fallback.
  No invented Lancer broken-glass zones. Unknown source surfaces retained.
- Original text-labelled action icons, wrapping button rows, scrollable pages,
  full workspace selectors. Six actual Windows Tk scale/size cases pass;
  OS mixed-monitor DPI and gameplay remain owner checks.
- Native shadow CPU replay: 58 cases each for Lancer/Subaru/stock Pajero.
  Actual Shadow GUI custom/save/reopen/undo/redo/reset/original/auto and foreign
  project guard pass; D3D9 guides captured. Terrain/D3D8 shadows not qualified.
- Classic deterministic conversion, collision/switches, native damage and brake
  diagnostics pass. All-side/alpha/reflection/wireframe/wheel captures produced.
- Full synthetic suite: 894 tests, two skips. Missing exact legacy J.1 bundle
  skips its patch-plan class; missing old V4.11 private wheel fixture skips one
  check. Those obsolete runtime trees were not recreated solely for tests.
  Current 30-entry packages/native launcher preflights are separately verified.
  Audio Studio, Paint/Crew, stock-reference browser and texture zoom Windows
  regressions pass; unchanged Physics/Camera code is covered by Core tests and
  exact resource equality, not a fresh complete Physics GUI build matrix.

## Runtime space / preservation

Restored the removed frozen Subaru base through the existing G1/H2/I1 pipeline;
all three original frozen-base pins match exactly. Those runtimes are active
build dependencies and must be retained. Original EXE/DLL/retail SHA256 match.
An attempt to remove only the five oldest vsdk4d/t/a..e/candidate/runtime trees
was blocked by automatic command policy (`blocked by policy`); nothing was
removed. Do not work around this rejection or claim disk space was freed.
Local validated phase commit is recorded in COMMIT_LEDGER; no push. No proprietary assets in
source review archives; private previews/resources stay under ignored output.

## Candidates and exact differences

| Candidate | Visual version | Shadow |
| --- | --- | --- |
| fidelity/t/a/candidate | Source Fidelity | Original native |
| fidelity/t/b/candidate | Approved Classic, source GT paint | Auto Fit |
| fidelity/t/c/candidate | Same approved Classic | Custom width .95, length .90, Z offset +.05 m |

Each contains Launch-SDK-Roster.cmd. Do not run candidates simultaneously.
All three roster validators and each launcher's verify, graphics-environment
and native-allocation self-test pass; no game was launched. Original EXE is
read-only; hooks are external/in-memory. Short final output paths avoid an
MSBuild FileTracker MAX_PATH failure seen in an initial longer staging path.

Source vs Classic changes 20 resource paths, all inside LancerEvo4. Auto vs
Custom changes ZERO resource bytes: collision, geometry, audio, physics, camera,
UI and other families remain identical. See private t/exact-differences.json.
Original retail, stock, Subaru and accepted Pajero resources remain unchanged.

| Measurement | Source | Classic |
| --- | ---: | ---: |
| car triangles / draws | 2649 / 119 | 2379 / 111 |
| complete triangles / draws | 6333 / 186 | 4563 / 178 |
| wheel triangles / draws | 745 / 16 | 370 / 16 |
| unique referenced textures | 77 | 77 |
| native RGBA cache estimate, bytes | 12199936 | 11508736 |

Counts include the previously approved Classic topology/wheel recipe, not new
silhouette decimation. Material pilot does not move tyres/hubs or change physics.
The front windscreen's mixed banner draw keeps its non-environment pass to avoid
reflective/tinted stickers; source-colour exact optical masking protects banners.
Side/rear panes use the qualified stock glass material. This is an explicit MR
approximation, not a complete reproduction of GT rendering.

Manual shadow author controls from an earlier visual version remain archived
and produce an explicit requalification conflict during Classic rebuild; they
are not silently baked onto changed geometry. The original donor profile follows
the existing strict unchanged-footprint rebase.

## Owner gameplay checklist (pending)

1. Compare a and b in the same location/camera with reflections on/off: bonnet,
   bumper, fender paint, red graphic, retained decals, tyre sidewall/tread and
   wheel inside/outside; inspect front banner and cockpit visibility.
2. Compare a / b / c top-down: original versus auto footprint; custom dimensions
   and offset should affect only shadow, with no wheel/collision/handling change.
3. Brake lights, body damage, race exit/re-entry, Results and AI/audio isolation.
4. Existing Subaru intact/broken front/rear/left/right glass and accepted Pajero.
5. Check real OS/mixed-monitor DPI if desired. Captures use actual Tk Windows
   rendering scales 100/125/150%, desktop DPI unchanged.

No next milestone started. Actual D3D8 gameplay/material/shadow/listening remains
owner verification, independently from the completed source/offline checks.
