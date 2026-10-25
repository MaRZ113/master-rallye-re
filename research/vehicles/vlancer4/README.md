# V-LANCER4 — race wheels and native damage alpha ownership

2026-10-23 · `research/vehicles` · private, offline-qualified candidate.
**No new gameplay confirmation is claimed.** The user's latest clarification
places the body failure after collisions, not at initial race spawn.

## Candidate

Run `.research-output/vehicles/vlancer4/candidate/Launch-Lancer.cmd` after
closing the previous game. Use this launcher and runtime together. This is the
existing Mercedes ID26/T1 + Lancer ID27/T2 layout, separate from frozen Subaru
and from the experimental SCALE1 packages. No capacity expansion is included.

Only three immutable runtime resources differ from PERF1: Lancer `car.dx`,
`complete.dx`, `wheel.dx`. **212 other immutable files, all 64 DXT files, UI,
donor collision and physics remain unchanged.** Texture residency remains
10,903,552 bytes (10.4 MiB), within the existing 16 MiB authoring budget.
The frozen Subaru bundle passes its original manifest/hash/reconstruction gate.

## Findings and implemented rules

### Wheel template basis

Stock Navara/Pajero outer wheel faces point toward local **-X**. The imported
Lancer's detailed metal face pointed to +X, exposing the opaque inner tyre cap
on the outside of native race instances. Source UVs and triangle winding were
coherent; the error was the separate MR wheel template's basis.

Shared `addon_sdk/wheel_orientation.py` applies a proper Y half-turn to template
positions **and normals**. Its determinant is +1: no mirror or index reversal.
Source UVs, colours, indices and radius/depth are retained. The frontend's
already assembled wheels are unchanged. Preview instance angles compensate
only this template basis; their source hub translations stay exact. Actual MR
physics hub/spin/steering parameters have not been edited.

`tools/validate_vehicle_wheels.py` checks all four explicit rest instances,
positive determinants, outward faces, finite attributes, canonical winding
against normals and unchanged topology/UVs/colours/hubs. No degeneracy was
introduced. One zero-area triangle already present in the source rim remains
explicitly counted, rather than deleting source geometry to obtain a clean
statistic. Source-qualified face draw IDs are caller input, not texture-name
heuristics or hardcoded vehicle identities in the validator.

### Damage: coverage alpha versus reflection-weight alpha

Exact retail SHA256:
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
REA/Ghidra analysis and independent PE-offset byte checks qualify this path:

| Native address | Observed role |
| --- | --- |
| `005841D0` | Dynamic CPU geometry clone |
| `00584570` / `005845B0` | Swap mutable data / update and restore resource |
| `0056BD1D` | Renderer call to native damage, inside `0056BBC0` |
| `005892E0` | Damage entry; original/current arrays, four stack args, `ret 16` |
| `005893F0` / `005897A0` | Native deformation/darkening/alpha fading; nearest vertex |
| `00589110` | Original damage defaults; movement, darkening and RemoveEnvMap enabled |

Native damage fades vertex alpha as an environment-reflection weight. Imported
cutout/blended materials also multiply texture coverage by that same byte.
Damage can therefore erase covered body pixels without separating coincident
vertices. This distinction explains why the geometry looked torn after impact.
It is supported by the isolated native instruction replay, not inferred from
opaque renders alone; the exact user's collision history was not captured.

Two complementary, reusable changes are implemented:

1. GT4 conversion removes redundant coverage tests only when **every baked
   texel and used vertex proves full coverage**. Opaque source-alpha draws are
   normalized only when source depth-write is also enabled. Genuine cutouts,
   translucent materials and additive-effect limitations remain explicit.
   Car/frontend coordinates, normals, UVs, colours and indices stay byte exact;
   only qualified material flag bytes change.
2. A source-bound external runtime bridge calls the original damage function
   once, then restores original alpha only on coverage-owned vertices. Native
   movement, RGB darkening and reflection fading on opaque surfaces remain
   unchanged. Full original XYZ/UV buffers and vector lengths must match the
   supplied model; unknown source geometry passes through. Launcher resource
   hashes seal the associated DX and policy. No deformation switch, welding,
   panel deletion, arbitrary displacement clamp or physics change is used.

The bridge uses the existing bounded 64 KiB private RX allocation mechanism,
**separately from SCALE1**. Payload: 61,261 bytes. Occupied addresses, unknown
retail builds, changed call preimages, oversized identities or an existing
experimental extension fail closed. Larger models need further allocation
qualification; arbitrary topology/size support is not claimed.

Coverage wins where native MR has only one alpha channel. Consequently,
damage-dependent reflection fading on coverage-owned transparent surfaces is
an explicit approximation. Opaque paint retains native reflection fading.
Large folds/self-intersections caused by native deformation limits are still
possible; this pass does not redefine the engine's crumpling algorithm.

## Evidence and checks

Private evidence is under `.research-output/vehicles/vlancer4/`:

| Check | Result / evidence |
| --- | --- |
| Deterministic conversion, DX/DXT references, source hashes | `offline-validation.json`: PASS |
| All four wheel instances, winding, no added degeneracy | `wheel-validation.json`: PASS |
| Original native CPU damage + adapter, 36 synthetic rear/side impacts | `damage-native-validation.json`: PASS |
| Native positions and RGB versus adapted buffers | Byte identical; return/stack/callee-saved ABI PASS |
| Coincident original position groups split by deformation | 0 in this replay |
| Coverage vertices losing alpha without/with bridge | 131 / 0 on the new model; old materials lose 157 |
| Different source UV identity | Exact native pass-through |
| GPU front/back fixture and explicit NONE/opposite culling | `previewer-check-final/validation.json`: PASS |
| Stock Navara and Pajero reflection/brake toggles | GPU smoke PASS; no native-game parity claim |
| Full synthetic suite | 629 tests, no failures/errors, one fixture-dependent skip |
| Launcher/resource verification + private allocation | PASS, game not launched |
| Missing, truncated, altered extension | All rejected by sealed launcher |
| PERF1, UI, collision, physics, frozen Subaru | `regression.json` and frozen manifest audit: PASS |

`damage-comparison.png` arranges GPU renders of **actual original-instruction
CPU replay buffers** before/after the material/ownership correction. It is not
a recreation of the supplied runtime screenshot. `wheel-sides.png` shows both
source-rest sides with culling enabled. Additional front/rear/side/three-quarter
captures, reflections and draw inspection remain available through the viewer.

## Previewer changes and boundary

Default culling is now **CW in the SDK canonical-index/RH camera frame**.
The parser swaps wire corners 0/1; this is not a claim that every native D3D8
instance always sets that same numeric state. `K` cycles culling and the title
shows the current state. `--cull none` remains an explicit diagnostic. Preset
6 shows the opposite side. GPU asymmetric fixtures verify front visibility,
back rejection, opposite-cull inversion and NONE visibility, as well as
horizontal/vertical texture orientation. Native inherited state overrides,
world lighting, fog, exact queue sorting and suspension pose remain outside
the viewer's demonstrated fidelity.

## Reproduce with user-owned resources

Use the existing GT4 build/project-build commands from V-LANCER3 and the same
editable source profile, targeting a **new** private output directory. The
builder now emits the native wheel basis and proven coverage normalization.
Run `tools/validate_gt4_vehicle.py` with the same source/profile/donor and
candidate, then qualify wheel face draws from that source's assembly metadata.

Example additional damage packaging, after a normal verified project build:

```powershell
python tools/prepare_vehicle_damage_runtime.py --manifest research/vehicles/sdk/examples/mercedes-ml320.json --manifest .research-output/vehicles/vlancer4/candidate/project/addon.json --project-build mitsubishi-lancer-evo-iv-rally-97=.research-output/vehicles/vlancer4/candidate/author-build --model DataGx/Vehicles/LancerEvo4/car.dx --output .research-output/vehicles/my-next-check/runtime --launcher-output .research-output/vehicles/my-next-check/launcher
python tools/validate_vehicle_damage_native.py --exe '../MRallye.exe' --model '.research-output/vehicles/vlancer4/assets-build/assets/car.dx' --output '.research-output/vehicles/my-next-check/damage.json'
```

The CPU validator needs optional Unicorn (and SCALE's separate helper validator
also Capstone), available here in the ignored research tools path. The normal
SDK build/viewer does not require them. No GT/MR assets are bundled in the clean
source handoff. Each model requires its own explicit qualification; an alpha
mask is never transferred from Lancer to another vehicle by name.

## Human acceptance still required

1. Launch the **new Lancer candidate**, inspect frontend and an undamaged race
   car. Check all four wheels from both sides, including steering/spin.
2. Apply rear and side impacts. Expect real crumpling/darkening, without the
   former large coverage holes or black outward wheel caps.
3. Repeat with reflections enabled/disabled; inspect glass and light surfaces.
4. Check stock cars, Results and return to frontend. Send a fresh renderer log
   and screenshots if a gap remains. New evidence may distinguish remaining
   actual geometry folds from coverage loss.

EXE/DLL hashes remain unchanged; no game launch, commit, push or publication
was performed. SCALE crash correction has its own report and candidates.
