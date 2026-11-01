# V-DEF1 — Forester owner corrections

1 November2026. Baseline ce0cd68929aca4a0c0048b74aff367a5fe000461 on
research/vehicles. Owner screenshots demonstrate selection and race entry.
The owner separately confirms **Darren Sutherland displays correctly in race**.
Full race completion/Results/re-entry are not thereby confirmed.

The Wildcat collection change is intentional: owner replaced misleading
Simmbugghini files with original9.3.1 Wildcat. Keep the previous audit snapshot
and its raw difference report as history; do not roll back the collection.

## Current private workflow

Root: `.research-output/vehicles/v-def1/owner-fixes/release`.
Open `Open-Forester-Workshop.cmd`, or launch
`workshop/builds/first/candidate/Launch-SDK-Roster.cmd`.
Previous `v-def1/release-candidate` is untouched and remains rollback baseline.
The same experimental ID30 and31-record roster are used, with no additional
registration hooks, slot changes, DLL/bootstrap edits or installed-file edits.

## Four corrections

**Physics:** create_author's ordinary independent RETAIL Forester/WOOLDAND clone
is now the active profile. Overrides are empty. All147 vehicle fields and26
modification fields equal the retail donor after family-prefix renaming. There
is no DefForesterTyre clone in this candidate: it references stock retail tyres.
The original150 Demo rows and24 tyre coefficients remain historical evidence;
they are not appropriate to infer original physics behavior in the retail solver.
Historical profile/report live in `historical-physics-reference.json`.
This is the requested complete retail fallback, not a wear-only guessed retune.

**Lamps:** the first candidate used actual donor halo geometry but brightened
the Demo source atlas for its ON surface. That omitted the retail white hot
centre, visible in the owner's comparison. Optional shared reference authoring
now transfers original WOOLDAND ON geometry (4tri), UVs, colours, normals and
`breaklightson-tga` /perspex material, with exactly the same per-side uniform
fit as its original16tri halo. The original12tri Demo OFF lens remains below
the native core in ON as well as in OFF. No door/body triangles are selected;
glass states, race body and wheels are preserved. No global unlit/transparency
policy or modified source atlas is introduced. D3D9 shows the restored white
centre; brightness, depth and oblique-angle behavior still need owner D3D8 review.

**Mini icon:** inspected original Demo banks independently. Demo9.3.1
`RaceResults/smallcarsheet_001_000.dxt` contains64x32 three-quarter pink Forester
art. Demo9.10.0 `RaceResults/smallcarsheet_004_000.dxt` contains the separate32x16
SIDE-view pink Forester icon needed here; its original bank references frame4.
This source is distinct from the128x128 menu CarSheet. Use its exact original
RGBA, without crop, tone, exposure or rescale. Shared `source-pixels-v1` packaging
requires exact native dimensions and checks the resulting native pixels.
Visual identification and bank membership are established; original executable
registry IDs across Demo editions are not claimed identical.

**Menu height:** independent body/wheel matching proves Demo car→complete
translation0 and retail Forester→complete translation+0.38971441984176636Y.
Rebase only derived complete Y positions by that measured difference; regenerate
terminal bounds with the shared bounds code. Every other byte, including indices,
normals, colours, UV/material records and collision, is conserved. Original
native-import, car.dx, wheel.dx and race hub positions remain unchanged. Static
native projection bottom NDC changes−0.827812→−0.689876; reference−0.679644.
The residual is from the actual different wheel/body geometry, not a reason to
scale or level the source model. In-game menu rotation/framing needs owner review.

## Validation and exact scope

54 focused tests PASS. Full Windows1315 tests PASS with2 existing fixture skips
(J.2 private reentry fixture and private wheel fixture). New regressions reproduce
the missing native ON core, inappropriate icon recomposition and frontend-origin
conservation requirements. No extra full regression was run for documentation or
capture-only changes after this successful suite.

Two actual Workshop builds yield222 identical DX/DXT resources. All308 accepted
30-roster resources and prior bank records/physics values remain unchanged.
The old owner candidate's345 sealed resources still match its manifest.58
canonical source/mini pins verify. Actual composed native helper emulation still
passes for31 mappings; native game lifecycle and GPU are not emulated.

Exact nine-path resource difference is pinned in
`V_DEF1_FORESTER_OWNER_REVISION.json` and private `resource-difference-report.json`:
vehicles, modifications and two candidate PlayerState seed files; new mini
frame33; derived car/complete; unused old auto-lit texture removal and original
donor ON texture addition. Candidate PlayerState seed values follow the retail
profile. No installed/player-owned save is edited. Other resources remain exact.

Private `previews` contains31 actual D3D9 source/restored/donor captures.
`final-comparison` adds9 previous/current/WOOLDAND captures and a comparison
sheet. Frontend uses one fixed inspection camera, not an original animated-menu
runtime claim. Numeric native projection measurements are recorded separately.
The separate Demo icon contact sheets show both editions' authentic artwork.

Use the four-point retest in `V_DEF1_FORESTER_OWNER_TEST.md`. Corrections are
**READY FOR OWNER TEST**, not gameplay PASS. Glass behavior, crew, original
identity/name, audio, cameras and shadow were not retuned. No other donor/import,
CarID expansion, DLL work or public asset packaging is part of this revision.

## Reproduction

```powershell
python tools/restore_demo_forester.py --demo ../corpora/demo-9.3.1 --rebaked "D:/Game/Master Rallye PCG104AXMAS01/DataGx/Vehicles/Forester" --retail-sma ../corpora/retail/Data.sma --ps2 "D:/Game/Master Rallye PS2/SLES_509.06" --roster-config .research-output/vehicles/heritage/roster/roster-config.json --output .research-output/vehicles/v-def1/owner-fixes/repro --retail-corrections --mini-icon ../corpora/demo-9.10.0/DataGx/Frontend/RaceResults/smallcarsheet_004_000.dxt
```

Choose a fresh private output. Use `validate_forester_restoration.py` with
`--repeat` and optional existing private Unicorn/Capstone environment for
`--emulate`; use `capture_forester_owner_revision.py` for fixed comparisons.
Only committed source/documentation/tests enter review ZIPs; models, textures,
original shader/executable payloads and preview images stay private.
