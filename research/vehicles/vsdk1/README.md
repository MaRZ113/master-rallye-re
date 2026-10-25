# V-SDK1 — combined imports and shared authoring

2026-10-24 · `master-rallye-re-vehicles`, `research/vehicles`.

**Ready for human testing:** independently sealed 29- and 30-entry candidates.
The owner has already confirmed SCALE1 29/30 through loading, AI, finishing,
Results and re-entry. That qualifies the capacity mechanism; this task does
not claim that the new combined models/audio have received gameplay testing.

## Delivered private candidates

Under `.research-output/vehicles/vsdk1/`:

| Candidate | Additional identities, beyond stock IDs 0–25 |
|---|---|
| `candidate-29-final/Launch-SDK-Roster.cmd` | 26 Mercedes (preserved), **27 Subaru**, **28 Lancer** |
| `candidate-30-final/Launch-SDK-Roster.cmd` | the above plus **29 GT4 Pajero Rally Raid '85** |

Both use the actual original `D:/Game/Master Rallye/MRallye.exe` and approved
existing graphics proxy. Nothing patches either file on disk. The separate
source configs are `roster-29.json` / `roster-30.json`; each candidate carries
its exact `roster-config.json`, sealed runtime, matched launcher and validation.
Earlier failed/intermediate output directories are not the delivery.

| Imported vehicle | Runtime family | T2 local slot | UI select/results frame | Physics/audio |
|---|---|---:|---|---|
| Subaru V-MESH4.13 | `ImprezaProto` | 7 | 32 / 30 | frozen independent family, existing stock audio routing |
| Lancer V-LANCER6 + current fitment/audio FIX3 | `LancerEvo4` | 8 | 33 / 31 | unchanged current physics, `lancer_evo4` engine/whine/spool/BOV namespace |
| GT4 Pajero Rally Raid '85 | `SdkPajero85` | 9 | 34 / 32 | independent Navara-derived initial profile, separate `pajero85` engine resource |

Local slots are zero-based. Standalone author projects may use their admitted
author slot27; the collection performs an explicit recorded **27→28 / 27→29
runtime binding**, without rewriting frozen projects or geometry. Audio physical
IDs are rebound in the native profile; original author provenance is preserved.
The resource stem, family, physics values and source wave stay independent.

## Implemented shared architecture

`tools/build_sdk_roster.py` verifies the frozen Subaru bootstrap and every
standalone project through the existing strict author-build verifier. It then:

1. Reserves global IDs and class-local slots using the shared tombstone-aware
   allocator. Family, namespace, resource and ID conflicts fail closed.
2. Copies validated owned model/audio resources. Appends only each new physics
   family's serialized values, preserving all existing values and stock bytes.
3. Composes UI banks using the existing bank parser/append helper. Existing
   records and textures are untouched; new frames are assigned to registry and
   Vehicle Select together. No original atlas is overwritten in the game.
4. Builds one reference image and **one 256 KiB private allocation**, starting
   at the existing admitted address `0x10000000`. Source-bound damage dispatch,
   physics reference, engine audio, shadow, supplemental audio and mechanical
   appenders are each emitted once with lists of applicable profiles. Capacity
   code is relocated into its own aligned segment in that same allocation.
5. Rejects overlapping native hook owners. One dedicated 4096-byte RW/NX page
   holds audio state; code/constants stay RX. The launcher retains exact hashes,
   resource-set checks, occupied-address rejection and bounded layout admission.

The larger allocation is allowed only for the explicit combined 29/30 layout;
unknown/larger counts and unknown profile kinds remain rejected. This is not
new engine capacity research or a claim of unlimited vehicles. Additional T1/T3
layouts and counts above30 need separate native/gameplay qualification.

### Native multi-car repairs

Damage now supports multiple uniquely identified source models while calling
the original native deformation **once per dispatch**. Full XYZ/UV identity,
vector lengths, native return and coverage-alpha ownership are preserved.
Ambiguous/duplicate model identities are rejected rather than guessed.

Audio owners have separate voices and pressure/retrigger state. The previous
global map clear on every construct/destruct was unsafe for simultaneous addon
actors. Each 44-byte owner slot now records its public-state key; intermediate
cleanup removes only that owner's association, and last-owner cleanup clears
remaining race state. Other live owners survive construction/destruction.
The read-only voice inspector supports both old40/new44-byte layouts.

The qualified SCALE audio lookup still chains its parent once. Stock/Subaru
audio passes through; Lancer and Pajero receive their own resource names using
physical CarID, not a shared current-player global. See [native audit](native-audit.md).

## Third independent source

The third import is genuine **GT4 Beta `mits0038`**, Mitsubishi Pajero Rally Raid
Car '85, with a substantially different SUV body. It uses the same GT4 decoder,
assembly, material translator, DX writer, author builder and UI generator.
Per-model selections and identity remain profile data.

Two source assumptions were corrected generically: no-colour/no-depth GS
alpha-only preparation passes are recorded as unsupported effects rather than
misclassified visible surfaces; a genuine CAR4 embedded rim need not be byte
identical to a separate wheel bank. Both sources remain hashed/qualified.
Peugeot206 was considered first but correctly rejected for unqualified packed
UV data. It was not replaced silently or force-rendered opaque.

Pajero's optional deterministic texture normalization reduces family residency
from **13,393,920 to 3,170,304 bytes**. Thirty-seven images are downsampled;
DX bytes, geometry, normals, UVs and material references remain unchanged.
Original full-resolution assets/project remain separate. This is an explicit
lossy authoring choice, not a more accurate GT decoder. The current Lancer and
Subaru resources are not resampled. [Third source details and previews](third-vehicle.md).

This first Pajero candidate does **not** claim tuned suspension/collision,
fitted crew, native state-dependent brake-light conversion or full GT4 visual
parity. Source day lamp states and donor-derived physical/audio defaults are
retained. Its independent engine uses a private stock MR source, not an alleged
GT4 Pajero recording. These limitations do not change the two frozen imports.

## Optional authentic audio sources

GT3/GT4 named `turbine`, `turbine2`, `b_off` and GT4 `shift_change` events were
inventoried with exact local source provenance. A reusable optional GT4 INST
program/split inventory and nominal-rate PCM audition tool was added. Event
token→bank/sample/note/pitch attribution is still unqualified; anonymous waves
are **not** relabelled authentic turbo/BOV/whine. Lancer's working synthetic
layers are preserved. No proprietary sound is bundled.
[Findings and local audition commands](audio-sources.md).

## Camera research, independent of integration

Native follow cameras add **full model-bounds height and half-length** to shared
camera presets. Emitted Lancer race height is 2.01947 m versus Megane1.48964 m;
a tiny upper feature consistent with the roof antenna determines the top. Race
half-length also retains a donor/collision-derived 2.61983 m versus rendered
2.24780 m. These are verified automatic framing contributions, not proof that
they fully explain a particular live camera/FOV/terrain state.

`vehicle_camera_diagnostics.py` compares actual models and replays the original
initializer. [Camera map, native parameters and proposed schema](camera.md)
distinguish shared settings, local extent terms, follow/fixed modes, renderer
FOV behavior and unresolved dynamics. A true camera-target→physical-CarID owner
binding is not yet qualified. Therefore there is **no global camera change or
speculative per-car runtime override** in either candidate. Camera Studio remains
a future consumer of the qualified native parameter contract, not a new GUI.

## Simple authoring workflow

Use `python tools/vehicle_sdk.py --help` as a small command hub over existing
tools, with editable project/physics/audio JSON as the source of truth:

```powershell
$env:PYTHONPATH='src;tools;.;.research-output/vehicles/scale1/python-tools'
python tools/vehicle_sdk.py create --name "My vehicle" --class T2 --donor Navara --family MyVehicle --donor-source PRIVATE_NAVARA --output NEW_PROJECT
python tools/vehicle_sdk.py import-gt4 --source-root PRIVATE_GT4 --profile SOURCE_PROFILE.json --donor PRIVATE_NAVARA --output NEW_CONVERTED
python tools/vehicle_sdk.py author-gt4 --candidate NEW_CONVERTED --donor PRIVATE_NAVARA --profile SOURCE_PROFILE.json --output NEW_AUTHOR
python tools/vehicle_sdk.py validate NEW_AUTHOR/project --retail-data-sma PRIVATE_RETAIL_DATA --retail-data-root PRIVATE_RETAIL_ROOT
python tools/vehicle_sdk.py build-project NEW_AUTHOR/project --retail-data-sma PRIVATE_RETAIL_DATA --retail-data-root PRIVATE_RETAIL_ROOT --output NEW_AUTHOR_BUILD
python tools/vehicle_sdk.py preview NEW_AUTHOR_BUILD/DataGx/Vehicles/MyVehicle/complete.dx
python tools/vehicle_sdk.py roster-build --config MY_ROSTER.json --output NEW_ROSTER
python tools/vehicle_sdk.py roster-validate --config MY_ROSTER.json --candidate NEW_ROSTER
```

`create` is a generic scaffold; `author-gt4` creates its own imported project, so
these are alternative starting paths. The source profile chooses the family.
Keep source/converter profiles and optional physics/audio sidecars editable.
`normalize-textures`, `audio-preview` and `camera-diagnose` expose the existing
optional diagnostic tools; each command has its own `--help`. Blender is not
required. The MR Previewer can reload converted resources after a rebuild.

A roster declaration names validated author projects/builds and explicit runtime
IDs, plus the frozen bootstrap and optionally the previous reservation lock:

```json
{
  "sdk_roster_version": 1,
  "base_runtime": "PRIVATE_FROZEN_SUBARU_RUNTIME",
  "projects": [
    {"project": "PRIVATE_LANCER_PROJECT", "build": "PRIVATE_LANCER_BUILD", "physical_id": 28},
    {"project": "PRIVATE_THIRD_PROJECT", "build": "PRIVATE_THIRD_BUILD", "physical_id": 29}
  ]
}
```

Use the matching `roster-reservations.json` for future revisions of that roster.
Do not import the old SCALE probe lock and steal its IDs: it owns28/29 for
different identities and will be rejected. The new candidates start a separate
isolated reservation lineage from frozen26/27, as explicitly requested. They
do not migrate probe/campaign saves. UI/physics merges and CarID rebinding are
generated, not hand-edited per vehicle. This first composition profile still
requires the exact qualified frozen bootstrap and Navara-derived T2 author
family validation; it is not an arbitrary retail-build or any-class installer.

## Validation evidence

- Full synthetic suite: **733 run, 732 passed, 1 skipped**.
- Both matched launchers pass bundle verification, original EXE/approved proxy
  environment checks and allocation tests, including exact RW/NX page and
  rejection of an occupied allocation address. No game was launched.
- Two independent derivations reproduce each delivered bundle's generated files,
  payload, operations, resource hashes and policies exactly. Launcher PE build
  timestamps are not claimed deterministic.
- Capacity helper replay covers every ID/class mapping, authored AI pools and
  87/90 audio lookup cases with deliberately clobbered volatile registers.
- Actual Lancer/Pajero independent engine resource routing is replayed at four
  participant slots across stock IDs0–27, IDs28/29 and unknown255.
- Two fully layered test profiles validate interleaved audio owners, independent
  state/BOV, surviving-owner cleanup, stock pass-through and reused addresses.
  The actual Pajero profile is engine-only; optional effects can be authored later.
- The **exact delivered shared damage payload** passes source-match/rejection
  cases and original native deformation replay on Lancer and Pajero, preserving
  native positions/RGB/return and restoring only owned alpha.
- 185 immutable bootstrap resources remain byte-identical outside five explicit
  shared composition paths. All5637 prior vehicle and884 modification values
  remain unchanged. Banks preserve33 Vehicle Select and31 Results records,
  growing to34/32 in29 and35/33 in30. Source UI textures are unchanged.
- A simple combined race binding-order LRU prediction with one of each addon
  and a synthetic8 MiB world/UI reserve has no steady-state misses/evictions.
  This is accounting evidence, not measured frame-rate or actual world demand.
- Original `MRallye.exe` SHA256 remains
  `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`;
  `d3d8.dll` remains
  `eb7ea3d9501b514bff668f1e75e86041906c5fe4e8afa89f06d658751429aaf4`.

Private evidence under `.research-output/vehicles/vsdk1/`: candidate validation
and audit files, `regression-29/30.json`, `native-capacity-29/30.json`,
`native-actual-engine-isolation.json`, `native-delivered-damage-dispatch.json`,
`native-delivered-original-deformation.json`, `determinism.json`,
`protected-originals.json`, `workflow-smoke.json`, `tests-full.txt`, native-audit,
camera and third-source reports/captures. `ui-roster.png` is an offline atlas
diagnostic, **not** an in-game screenshot. Source handoff excludes all private
models, textures, sample WAVs, screenshots, native dumps and compiled game files.

## Gameplay test order

1. Close other MR instances. Start **29-final** using its own launcher/state.
   Check stock cars, Mercedes, Subaru and Lancer; ID27 must still mean Subaru.
2. Test Subaru and Lancer as player and AI, a race finish, Results, menu return
   and another race. Check Lancer crew, wheels, damage, brake lights and current
   physics/audio (including neutral/load release). Toggle reflections on/off.
3. Close the game. Repeat on **30-final**, including Pajero as player and AI and
   a mixed roster. Check its first-import lighting/alpha, attachment fit and
   donor handling; record any rendering/performance defects.
4. Check select icons/names and race/results thumbnails for all three. Each
   uses its own frames and audio namespace. Never copy probe/campaign state
   into these candidates. Campaign migration/network play remain unqualified.
5. Camera comparisons are a separate unchanged-camera observation: same mode,
   track position, aspect and renderer settings; capture stationary, throttle,
   brake, bump/jump and impact against stock Megane and stock off-road cars.

The completion gate here is an installable **offline-validated** combined
candidate. Actual simultaneous player/AI lifecycle, audible mixing, cache/FPS
and camera perception remain explicit human-gameplay gates.
