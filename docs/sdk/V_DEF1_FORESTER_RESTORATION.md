# V-DEF1 — canonical Demo Forester restoration

**Accepted reference:** during V-DEF2 the owner confirmed the corrected Forester
fully working and tested. The owner-fixes/release build is preserved. Earlier
NOT TESTED wording below is historical, not the current owner status.

**Current owner revision:** `V_DEF1_FORESTER_OWNER_REVISION.md` supersedes the
first candidate's Demo physics, derived menu mini icon, brightened-atlas lamp
ON core and zero-height complete frame. Current private root is
`vehicles/v-def1/owner-fixes/release` under `.research-output`.
Owner has shown selection/race entry and confirmed Darren in race. Full race,
Results/re-entry and the corrected candidate remain pending. Original findings
below and the initial provenance JSON are historical evidence, kept intact.

1 November 2026. Baseline `000521f4cf25bd78fac10c66a8cd2792af8fc649`, clean
`research/vehicles`. **Private CMD candidate built through Rally Workshop;
owner D3D8 gameplay NOT TESTED.** DLL/bootstrap work is unchanged.

## Delivered owner workflow

Private root: `.research-output/vehicles/v-def1/release-candidate/`.

* `Open-Forester-Workshop.cmd` opens the persistent `workshop` project.
* `workshop/builds/first/candidate/Launch-SDK-Roster.cmd` runs the isolated
  candidate with the existing original executable and approved D3D8 proxy.
* Configure/Validate/Build remain the existing Workshop services. The project
  was opened in real hidden Windows Tk controls and completed the native D3D9
  refresh. Two actual Workshop builds have identical222 DX/DXT outputs.
* The original30-entry roster is preserved and **one experimental record30**
  is appended: T2 local10 (eleventh T2 entry), classes8/11/12,total31. This is
  a bounded owner test, not a newly qualified engine maximum. ID29 is unchanged.

No replacement game executable, installed mod, new DLL, proxy or original archive
was written. Candidate resources/launcher are private. Ordinary retail startup
remains the way to disable this test; do not copy candidate saves into retail.
See [the owner checklist](V_DEF1_FORESTER_OWNER_TEST.md).

## Canonical source and authoring qualification

Use `pcg-rebaked/Forester`, authenticated against original9.3.1 GXM and the
completed Demo audit. The ambiguous `Original/Forester/car.dx` is not used.

| Resource | Original SHA256 | Rebuilt cache positions |
|---|---|---:|
|car.dx|fbe8d15af205a3cbe95773d5241372352729f7fbcef21e61386123209a80a423|5449|
|complete.dx|72a3b98f616d55e66e43bf0bbc2702bdb5ff464406ae7e14338cc3c4a5a4ee15|6644|
|wheel.dx|191009bd708ed20fd0d46c00572e8d8ba833ff5cff5c5f8f92b6772bd1d9a328|675|

All three inputs pass the existing structural rev135 validator's **oriented
triangle multiset/order-divergence** proof. A new optional strict cache-repair
policy requires that proof before deriving an authoring copy, rejects ambiguous
overlapping ownership/unowned ranges and rewrites only the stored global cache.
Source positional, UV, normal/color, material, draw-state and collision
fingerprints are unchanged. Original files and `native-import` snapshots remain
immutable. The legacy explicit local-authoritative repair still works for its
existing callers; it is not silently restricted to this one new policy.

The common native compiler emits the qualified restored car/complete/wheel bytes
unchanged; there is no new Forester DX compiler. The car's original1864 OFF
triangles, attributes/materials and collision are conserved by native_states.
Additional triangles belong to explicit alternate glass/lamp states and halo.
No global two-sided/alpha override, repaint, body scaling or new crew is used.
OFF geometry comparison gives1864 source/restored triangles with identical
position/UV/normal/color/material fingerprints and bounds. WOOLDAND has1807
OFF triangles; source extent X/Y/Z is2.281113/1.536268/4.692441 versus donor
2.192519/1.569374/4.324554. No nonuniform fit is used to make the bodies match.

## WOOLDAND evidence and native adaptation

Retail registry ID8 `Forester` / `SUBPELKA WOOLDAND` is strictly the technical
donor. Its body, artwork and physical tuning do not replace the Demo vehicle.
Original donor DX/material/texture bindings and switch records are inventoried
in `release-validation.json`.

| Native donor mechanism | Original observations | Restored Demo policy |
|---|---|---|
|screenfront|6 triangles per case; same positions,8 changed normals/UV entries|6 exact original Demo pane triangles, native screenfront controller|
|screenleft/right|5 triangles per case; positions/UV unchanged,7 changed normals each|5 exact source pane triangles on each side|
|screenrear|2 triangles per case,case2 serialized first;4 UV entries change|No separate source rear pane is qualified; opaque original rear artwork stays intact|
|blight OFF|4 lens triangles, lights64/perspex,flags0/0/1/1,state7|12 source blight triangles selected from original GXM/TXT|
|blight ON lens|4 triangles,breaklightson/perspex,flags0/0/0/1,state5|Source lens geometry/UV; explicitly brightened source lens atlas; donor unlit/environment material semantics|
|blight ON halo|Separate16-triangle geometry,breaklightsonglow/perspex,flags1/0/0/1,state5|Actual donor halo topology/UV/normals/colors and original textures, individually fitted to the two source lenses|

A verified common automatic-zone bug was fixed: wide windshield corners were
classified as side glass based on their X position despite forward-facing
normals. The source16 glass triangles now divide **6 front /5 left /5 right**,
with complete original GXM/TXT correspondence and zero nearest-match guesses.
Accepted projects retain their already-authored explicit recipes/resources.

`native_effect_reference` is a reusable, source-pinned effect transfer. It
requires exactly two disconnected source lenses, donor lenses and native halos,
rejects ambiguous material spans/prefixes and fits each side with a bounded
**uniform** scale. Here the scales are1.344480/1.344479; XY lens centers and rear
lens planes anchor the transforms. No body or wheel geometry is transformed.
The effect's16 triangles are separate ON geometry, not enlarged body polygons.
The original intact/OFF state is independently conserved.

These are MR-native adaptations, not recovered original Demo damage playback.
The cracked texture comes from WOOLDAND. Broken UVs use the existing explicit
planar MR approximation; donor broken-normal/UV changes are documented and are
not claimed to have been copied exactly. Intact pane attributes stay original.
The brightened source ON lens atlas is a derived interpretation, not the
original retail ON atlas assigned across incompatible source UVs. Halo size,
brightness, visibility at angles and actual damage triggers require owner tests.

## Original identity and CarSheet bindings

Original9.3.1 EXE SHA256:
`611526d30be94879012efe54c56ceff428cb4d20a4bd49173370a4ebfe31a728`.
REA/Ghidra12.1.4 finds Forester registration at original ID8 /classT2 in
`0044D360`; original instruction bytes near`0044D4A0` independently corroborate
its arguments. Original source records are not copied into retail's different
registry layout; existing typed SDK registration is reused.

* PC localized records: category52,index8 → `FORESTER`; category53,index8 →
  `SUBARU FORESTER`, each in two original tables.
* Original `DataScene/FrontendScreens/Wjd/VehicleSelect.xml`, widget
  `T2_Car2`: class/local X/Y1/1 and image-bank frame1. The original22-frame
  `carsheet.dxb` resolves it to `carsheet_001_000.dxt`, the actual pink Forester.
  This exact artwork supplies the new private project frame; no model render
  is substituted. Runtime Vehicle Select frame35 is appended, not overwritten.
* PS2 `SLES_509.06` SHA256
  `b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2`:
  six original localized triples link category52,index8 to`FORESTER` at
  VA4530F0 and category57,index8 to`DARREN SUTHERLAND` at VA453AC8.
  Exact file offsets are recorded. This is original **ELF data-table** evidence,
  not PS2 instruction emulation or a newly recovered PC driver literal.
* Display is **SUBARU FORESTER**, Results driver **DARREN SUTHERLAND**;
  original source stats6/7/5/4 are retained. Source crew geometry stays intact;
  no claim that a generic source head texture identifies Darren is made.
* Results icon frame33 is an explicitly derived32x16 fit of the authenticated
  Demo CarSheet, not a recovered separate original Results frame.

Native research is private under`vehicles_scratch/vdef1/`, including the retained
REA snapshot/evidence. No executable/decompiler payload is in source archives.

## Independent physics, wheels and other systems

All150 original named source physics rows are represented:137 common base
parameters are transferred by type;13 original zero modification defaults map
to both players (26 rows). No source fields are silently dropped. Ten retail-only
solver fields remain explicit technical defaults: aerodynamic downforce fields,
vertical suspension application offsets and additional gearbox-damage fields.
This preserves source parameters in the retail solver; it does not emulate the
older solver. WOOLDAND tuning is not silently used as the full vehicle profile.

The identical-looking harddirt reference concealed five source/retail coefficient
differences. The private **DefForesterTyre** clone retains all24 original tyre
coefficients;36 additional retail-only tyre fields are explicit technical
defaults. Both axle references are deliberately rebound to that owned prefix.
Global stock tyre tables stay byte/value unchanged. Generic typed cloning,
publication and collision tests protect this ownership; no global grip retune
is performed. See owned-tyres-validation.json. This late verified defect
justified a final full regression after the shared physics change.

Examples retained from Demo: track1.70 rather than retail1.60,peak torque350
rather than285,rev limit7000 rather than6500,final drive3.82 rather than3.72.
Mass1340 and original source suspension/damping values are preserved.
`historical_physics` is reusable and fails on unknown fields/type changes or
unsupported retail schema/count edits. No suspension retuning was performed.

Presentation wheel geometry/UV/topology yields four exact source rest instances
in five independent parts; max positional correspondence error2.19e-7 native
units. Static hub X positions are−0.823737/+0.822918; Z positions−1.472294/
+1.468217 (wheelbase2.940511,track1.646655). The supplied source front-left Y
is0 while the other three are−0.034095. These original static differences are
recorded, not visually leveled. Original physics wheelbase2.90,track1.70 and
wheel radii0.38 remain unchanged; settled suspension/contact are owner tests.

Retail-compatible audio profile8 and standard MR camera/shadow behavior are
technical gameplay fallbacks, not newly recovered Demo audio or camera parity.
Original source crew/interior are preserved. Physics/Camera/Audio/Shadow and
other supported Workshop controls remain available; no unrelated tuning was
added. Challenge/Invitation eligibility remains the existing SDK restriction.

## Runtime and validation boundary

The common roster compiler has a separately named, explicit
`sdk-multi-addon-roster-experimental-31` profile. Three appended projects require
`experimental_record_count:31`; ordinary29/30 configurations and their launcher
guards remain unchanged. No arbitrary counts, silent slot reuse or new hook
implementation is introduced. The existing SCALE1 emitter expands the registry,
RaceTest relocation, lifecycle counts, dense maps, UI, names, audio and T2 pools.

* Native bundle:345 indexed resources,259 operations,183248-byte payload in the
  existing bounded262144-byte allocation. All31 mappings and the three
  T2 AI pools are verified with Unicorn/Capstone against the actual composed
  payload. Native Broker/allocator/string/loop calls are mocked; this is not a race.
* All three actual launcher checks pass: verify, launch-environment and private
  allocation self-test. The approved installed D3D8 proxy is recognized.
  Self-test explicitly reports`game_launched=false` and`code_executed=false`.
* Target AppDir has no dinput8.dll. Randomizer is neither installed nor altered;
  its coexistence/F3 conflict investigation stays separate. This CMD proof
  targets the already-qualified retail build, not a claim of new universal
  executable adapters or ordinary DLL startup.
* Two Workshop builds:222 DX/DXT resources byte-identical.308 accepted30-roster
  resources unchanged; existing UI records and physics values preserved.
* Real hidden Tk open/native refresh passes for ID30 (2.14s observed).
 31 D3D9 views cover original/restored/WOOLDAND six views,frontend,ON and
  manually selected broken glass. See private`release-previews/comparison.png`.
* Focused52 tests PASS. Full Windows1312 tests PASS,2 optional skips.
  Original D3D8 vehicle selection/race/Results/re-entry remain **NOT TESTED**.

## Preservation and outstanding findings

Canonical Forester input pins are unchanged. The independent historical asset
check passes for11500 files /15,448,297,600 bytes. Source/accepted inventory
checks are recorded in the provenance index; no accepted project was rewritten.

The previous complete-Demo audit manifest now detects **34 unrelated changed or
missing files only in Nov2001/Vehicles/Wildcat**. Current car.gxm matches the
authentic original9.3.1/9.10 Wildcat, whereas the earlier snapshot matched
Simmbugghini. This restoration never writes that tree and does not roll it back.
The raw legacy comparison remains FAIL;5296 other audited files are unchanged.
Do not relabel the entire old baseline PASS or silently replace its history.

Owner review gates:31-record lifecycle/save behavior; wheel contact/steering/
suspension in the retail solver; actual pane/damage events; rear ON/glow angles;
Results driver/artwork; menu return and race re-entry. No gameplay success,
Forester rear-glass damage, DLL compatibility, additional demo import or new
capacity maximum is claimed. Stop at this candidate for owner feedback.


## Reproduction and archive boundary

```powershell
python tools/restore_demo_forester.py --demo "../corpora/demo-9.3.1" --rebaked "D:/Game/Master Rallye PCG104AXMAS01/DataGx/Vehicles/Forester" --retail-sma "../corpora/retail/Data.sma" --ps2 "D:/Game/Master Rallye PS2/SLES_509.06" --roster-config .research-output/vehicles/heritage/roster/roster-config.json --output .research-output/vehicles/v-def1/reproduced
python tools/validate_forester_restoration.py --restoration .research-output/vehicles/v-def1/reproduced --accepted-config .research-output/vehicles/heritage/roster/roster-config.json --retail "../corpora/retail/Data.sma_unpacked" --output .research-output/vehicles/v-def1/reproduced-validation.json --repeat
```

Optional`--emulate` on the validator uses existing Unicorn plus Capstone; the
local validation used private capstone5.0.6 under`v-def1/python-deps` on PYTHONPATH.
It is not required by the game or Workshop. `capture_forester_restoration.py`
recreates the fixed views from supplied originals and the candidate. Choose
fresh ignored outputs. `V_DEF1_FORESTER_PROVENANCE.json` pins reports,source and
native package hashes. Review archives contain committed sources/tests/docs;
all meshes,textures,shader/executable bytes,captures and private candidates stay
outside them. Local scoped commit only; no push,publication or release.
