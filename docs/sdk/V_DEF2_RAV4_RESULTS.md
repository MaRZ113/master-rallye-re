# V-DEF2 — reusable Demo restoration and canonical RAV4

1 November2026. Baseline f0668154f28a9340a7bb301b6a1227b2484a13a2,
research/vehicles. **RAV4: READY FOR OWNER TEST, not gameplay PASS.**
The owner confirms V-DEF1's corrected Forester is fully working/tested. Its
accepted resources remain untouched and form the restoration reference.

## Private deliverable

`.research-output/vehicles/v-def2/owner-candidate/`:

- `Open-Restoration-Workshop.cmd`: persistent Workshop project, existing studios
  and Configure/Validate/Build workflow.
- `workshop/builds/first/candidate/Launch-SDK-Roster.cmd`: isolated32-record CMD
  candidate, RAV4 on ID31/T2 local11. Forester stays ID30, Trooper29, Lancer28,
  Subaru27 and Mercedes26. Original26 retail records stay independent.
- `author`: ordinary native Heritage author project, not a separate converter.
- `restoration-manifest.json`, source/identity/physics/native-feature/frontend
  reports: exact private inputs and MR adaptation decisions.

No game installation, executable/archive rewrite, wrapper replacement, Randomizer
edit, new DLL/bootstrap deployment or automatic game launch was performed.

## Shared workflow and Forester regression

`addon_sdk/demo_restoration.py` orchestrates existing Heritage source staging,
strict cache repair, native state/reference authoring, historical physics,
frontend-frame alignment, UI composition and actual Workshop builds. The JSON
manifests in `research/vehicles/sdk/restorations/` contain vehicle-specific
source pins, original geometry associations, identity evidence, face/material
ownership, reference resources, physical policy and runtime placement.

`tools/restore_demo_forester.py` is now a compatibility wrapper for its accepted
manifest. Both old flag forms select the current owner-approved retail-physics
policy; the initial historical physics implementation remains in Git and V-DEF1
reports. Existing accepted outputs are never rebuilt in place.

A fresh generic Forester build reproduces all non-seed resources byte-for-byte.
Only the two new PlayerState seed copies differ because the owner has since
played the game. The old345-resource sealed candidate itself still verifies.
Neither its model nor its accepted physics/artwork was changed. Optional common
extensions default to the previous behavior for existing callers.

Root aliases are configurable in a private `roots.json`; manifests have relative
paths and source hashes, not hardcoded installation paths or executable payloads.
Output must be fresh, private, outside original roots and all accepted author/
build directories. Path escapes, links/junctions, texture-alias traversal,
unknown artwork roles and absent/corrupt source pins fail before publication.

## RAV4 authentic source and authoring

Canonical input: `pcg-rebaked/Rav4`, original9.3.1 GXM provenance. It remains
distinct from `NewRav`, `rav4Alpha` and Michelin Car25A RAV4.

| Role | Original rebaked SHA256 | Triangles |
|---|---|---|
| car.dx |75d3a6a37bbeb046408959ddc4e57e31663f6c95fcb39290f01980640e2f0545|1902|
| complete.dx |c45d5da6559c2ab71690105172110ace8a4435227fcd523cd4cb68c2c4e50188|2366|
| wheel.dx |6cb4f708a52dc25b37470697e63a06d0a2781c2bbc71fd622af5a2a3b8c292ea|252|

All three original GXM files match their rebaked sources. Existing typed rev135
validation proves index-order divergence; strict repair changes only the global
index cache in private copies. Source positions, oriented triangles, normals,
colours, UVs, materials and collision fingerprints remain exact. All1902 OFF
triangles survive native state authoring;1944 serialized triangles include the
additional broken/ON alternatives, not duplicated permanent body surfaces.

Five independent wheel parts prove original side-specific mirrored instances.
Hubs X−0.748669/+0.746453, Z−1.263246/+1.290315, Y0; static wheelbase2.553561,
track1.495122. These are preserved source rest measurements, not a settled
suspension claim. No MR replacement wheels, axle movement or global scaling.

The full14-face glass material is separate from doors/pillars. The old GXM
heuristic found11 uniquely matched faces and3 ambiguous ones, so it is not used
to decide the final glass selection. Exact material ownership and all original
DX faces produce6 front,4 left,4 right faces. No separate rear pane is invented.
Intact/off attributes are conserved. Broken texture/planar UVs are explicit MR
adaptations; original Demo damage playback is not claimed.

Rear `blight` has8 exact source-face matches (draw7,faces51–58), two disconnected
lamp components and no nearest-face fallback. Native WOOLDAND contributes its
actual4-triangle white-hot ON core,16-triangle halo and original textures/UVs/
normals/material state. Each lens is fitted independently with uniform scale
about0.8320767; source OFF lens remains underneath. This adapts a qualified MR
effect to different source lens geometry; it does not reconstruct a lost Demo
renderer or select all red texels/headlights as brake lamps.

Frontend-only complete Y is raised+0.38971442 using independently proven retail
Forester car/complete/wheel rest frames. Normals/UVs/topology/collision remain
unchanged; race hubs are not raised. Retail NewRav's wheel-rest proof does not
meet the shared exact-matching gate, so it is not used as a guessed frame.

## Physics: original evidence and explicit compatibility decisions

Demo9.3.1 has no named Rav4 physics family; substituting its Newrav values and
calling them original would be incorrect. Original8.4.1 `Vehicles/Rav4` provides
121 named rows. Owner explicitly selected **compatible Demo fields plus marked
retail substitutions** after being informed of the schema difference.

100 compatible typed fields are transferred to independent `DefRav4`, based on
the retail `Newrav` schema. Examples: mass1500, wheelbase2.4, tracks1.6,
peak torque425 and original gearbox/suspension values. The source rest hub
wheelbase differs from physical2.4; neither is silently fitted to the other.
Actual tyre/contact/handling behavior requires owner testing.

21 original fields remain source-only with full values and reasons:

- Original8-point torque curve plus count: retain the complete supported retail
  6-point curve as one group, never a truncated original curve with count8.
- Two vector suspension-application offsets: no guessed vector→scalar mapping.
- Eight old damage thresholds/multipliers: no claim of old/retail event parity.
- Two original Slicks references: retain stock retail harddirt tables, avoiding
  the source tyre-wear failure already seen with Forester.

Original XML and every excluded record remain pinned evidence. Retail-only
fields/default player modifications remain explicit, original shared tyres and
other vehicle families untouched. `historical_physics.source_only` is optional;
unknown fields still fail by default. Count/point groups cannot be half-retained.

## Identity, generated artwork and unresolved driver

An original8.4.1 XML widget `Toyota_RAV4` references CarSheet frame5. Original
9.3.1 smallcarsheet5 contains visually related old artwork. These images show
an older green/white livery and are not qualified artwork for the recovered
white/blue PERFORCE/AIWA car. The owner rejected these candidates; they are kept
as research only and **are not installed in the final candidate**.

The existing Workshop model renderer generates a three-quarter CarSheet and a
separate orthographic SIDE HUD image from the authentic complete model/textures.
MR-native UI composition produces128x128 and32x16 assets respectively. These are
new derived images, not recovered historical artwork. Original UV/texture data
is not repainted. Render cameras, PNG/resource hashes and provenance are pinned.

No original driver assignment for the retired Rav4 was found. The PC8.4.1
strings `TOYOTA RAV4`/`RAV4 PICKUP` do not prove this mesh's driver. PS2's
REECE RUSSELL/PICKUP belongs to the later Newrav association and is not copied.
Source crew texture names are not Results-driver evidence. Results deliberately
shows **TOYOTA RAV4**, not a fabricated person. Original driver remains WARN.
Frontend ratings are explicitly neutral SDK placeholders, not recovered stats.
Audio8/13 assignments in the manifests are retail technical fallbacks, not a
claim of recovered original engine-audio behavior.

## Runtime boundary, validation and proxy interoperability

The distinct `sdk-multi-addon-roster-experimental-32` profile admits exactly four
additional author entries and contiguous IDs28–31, using the existing SCALE1
compiler. The twelve-position T2 frontend guard stays unchanged: local11 is its
last admitted position. Ordinary29/30 and explicit31 profiles retain their own
guards;33 or arbitrary counts are rejected. This is not an engine maximum claim.

All32 forward/reverse mappings, initializers, name/Results/unlock/audio helper
ABIs and T2 pools27/28/29/30/31 pass actual-payload CPU emulation. Broker/native
allocator/loop calls are mocked; no GPU, collision, race, AI or save lifecycle
is emulated. The payload remains within the existing262144-byte allocation.

Two original Workshop builds yield258 byte-identical DX/DXT files.340 prior
resources,6078 vehicle rows,962 modification rows and all prior UI bank records
are conserved.72 original input pins verify. Source body/wheel/material OFF
fingerprints are exact. Three actual launcher preflights pass; no game launched.
Actual hidden Windows Tk project opening and native D3D9 refresh also pass on
ID31 (observed2.76s). This tests open/render, not every Studio edit operation.

Full Windows1323 tests pass with2 pre-existing optional fixture skips.66 final
focused tests additionally cover the final nested texture-alias/artwork-role
rejection guard. Earlier full runs predate owner-requested artwork changes and
remain historical evidence, not the current visual result.

The owner-local d3d8.dll changed externally twice while this task ran. Exact
build artifacts, SHA256SUMS and local distribution/build provenance qualify
collision-debug1 (`c21343e4…`) and collision-debug2 (`2d80609f…`) as this renderer
family. These exact builds are added to the existing launcher's approved proxy
list; unknown DLLs still fail closed. No proxy/INI/Randomizer is installed,
rewritten or disabled. This narrow admission is not universal DLL compatibility
or owner gameplay proof with the new renderer. Current CMD targets the already
qualified retail executable; broader executable adapters remain separate work.

Private D3D9 captures in `final-previews` show original/restored/reference scenes
and manually selected glass/ON states. Their geometry and texture resources
match the owner candidate; generated artwork is shown separately in
`generated-artwork.png`. Do not confuse D3D9 captures with actual damage triggers
or an original Demo renderer comparison. Follow `V_DEF2_RAV4_OWNER_TEST.md`.

Stop here: no next demo vehicle, fleet import, roster/class expansion or DLL work.

## Reproduction

```powershell
python tools/restore_demo_vehicle.py --manifest research/vehicles/sdk/restorations/rav4-931.json --roots .research-output/vehicles/v-def2/roots.json --roster-config .research-output/vehicles/v-def2/accepted-31.json --output .research-output/vehicles/v-def2/repro
```

Use fresh output; root aliases refer to existing installations/corpora. The
previous31 config points at the accepted Forester's frozen snapshot/build.
Use `validate_demo_restoration.py --repeat --emulate` with the existing private
Unicorn/Capstone dependency location, and `capture_demo_restoration.py` for views.
Review archives contain committed source/manifests/docs/tests only; extracted
models, textures, native fixture payloads and preview images remain private.
