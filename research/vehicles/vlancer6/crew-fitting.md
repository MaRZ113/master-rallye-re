# Reusing paint roles and stock crew fitting

Inputs are user-owned private GT data and stock MR resources. The SDK does not
bundle them. Run commands from the vehicles checkout on `research/vehicles`.

## Crew procedure

1. Parse a stock MR `car.dx` with `source_geometry`. Inventory material draws and
   positional connected components; inspect isolated components in the Previewer.
   Character pieces may be batched with seats/dashboard textures. Names alone
   are insufficient selectors. Do not import an entire donor cabin to fill holes.
2. Pin `crew.source_sha256`. Set `crew.draws` to exact draw indices, exact three
   texture names and descriptive roles. Optional `triangles` is a nonempty,
   sorted unique list of zero-based triangle indices in the canonical
   `source_geometry` draw. Unknown keys, duplicates, bad bounds, wrong source
   hash/materials and seat-crossing triangles fail closed. A new stock build
   needs a new qualified data profile, not a silently reused selection.
3. `people` declares two source X sides (+1/-1) and yaw pivots. `placements`
   declares per-model (`race` / `menu`), per-person `lateral`, `vertical`,
   `longitudinal` offsets in MR model units and `yaw_degrees`. These are visual
   transforms only. `seat_pair_preset` is a descriptive label, not a preset
   resolution or automatic seat detector. No scaling, physics or hub movement.
4. Pass `--crew-source <stock-family>` to `build_gt4_vehicle.py` to select an
   independent crew donor. Without it the existing `--donor` family supplies
   crew. Stock texture bytes are copied locally using content-derived names.
5. Inspect every imported material component and both people in cutaway and
   through the actual glass. `diagnose_vehicle_surfaces.py` checks projected
   roof/side envelopes, not complete seat/dashboard intersections. Adjust only
   the explicit per-car offsets/yaw; do not invent missing stock character parts.

The V6 Navara profile imports 52 harness triangles from draw 0 and 48 inner
helmet triangles from draw 1, alongside the 444 triangles from draws 16–20.
Seat and cabin triangles in those same material batches remain excluded.
Static poses and hand-to-steering-wheel contact are documented approximations.

## Paint procedure

Set `material_policy.menu/race.paint_surfaces` to explicit source shape/packet
roles. Qualification additionally requires oriented source environment
correspondence and supported GS states. `paint_cutout_min_alpha` controls the
documented MR shared coverage/reflection-alpha floor (129–255). Do not use it to
classify windows, lamp internals or grille voids as paint. No model name or MatN
number is embedded in the reusable rule.

## Rebuild / validate this candidate

Use a **new nonexistent output directory** for each candidate. These commands
describe the already produced `build-04` / `candidate-04`; use fresh names to rerun.

```powershell
$py = 'C:/Python315/python.exe'
$stock = '../corpora/retail/Data.sma_unpacked/DataGx/Vehicles/Navara'
$gt = 'D:/Game/GT_Model-Tools/VOL/GT4-Beta_Extracted/extracted'
$phase = '.research-output/vehicles/vlancer6'
$profile = 'research/vehicles/vlancer6/lancer-source-profile.json'
& $py tools/build_gt4_vehicle.py --source-root $gt --profile $profile --donor $stock --output "$phase/build-04"
& $py tools/prepare_gt4_addon.py --candidate "$phase/build-04" --donor $stock --profile $profile --ui-from .research-output/vehicles/vlancer5/candidate-01/project --output "$phase/candidate-04"
& $py tools/mrtool.py addon project-build "$phase/candidate-04/project" --retail-data-sma ../corpora/retail/Data.sma --retail-data-root ../corpora/retail/Data.sma_unpacked --output "$phase/candidate-04/author-build"
& $py tools/prepare_vehicle_damage_runtime.py --manifest research/vehicles/sdk/examples/mercedes-ml320.json --manifest "$phase/candidate-04/project/addon.json" --project-build "mitsubishi-lancer-evo-iv-rally-97=$phase/candidate-04/author-build" --model DataGx/Vehicles/LancerEvo4/car.dx --output "$phase/candidate-04/runtime" --launcher-output "$phase/candidate-04/launcher"
& $py tools/validate_gt4_vehicle.py --source-root $gt --profile $profile --donor $stock --candidate "$phase/build-04" --output "$phase/offline-validation-final.json"
& $py tools/diagnose_vehicle_surfaces.py --build "$phase/build-04" --output "$phase/surfaces-new"
& $py tools/preview_vehicle.py "$phase/build-04/assets/car.dx" --model race
```

`validate_vehicle_materials.py` compares the candidate to the private V5 baseline;
`validate_vehicle_damage_native.py` uses the exact original EXE in isolated CPU
replay (local Unicorn dependency). The synthetic tests use generated fixtures.
An offline PASS does not replace in-game validation.
