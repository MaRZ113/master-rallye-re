# V-MESH3 - Subaru geometry and wheel alignment

**Status: READY_FOR_HUMAN_RUNTIME. Not runtime-qualified. No runtime PASS is claimed.**
V-MESH2 was human-confirmed to load, drive and keep basic collision/damage. V-MESH3 only changes the geometry
pipeline; the addon identity, J.3-B runtime bundle and launcher are the same (addon plan SHA256
`567a27a8f3c978bebd2a6600710b89779d16ddece7cd983630d286338490477b` is identical to V-MESH2).
GT3 data, derived `.dx`/`.dxt` and the runtime bundle stay private under `.research-output/`.

## Defects found, their origin and the fix

| Visible defect (V-MESH2) | Origin | Evidence | V-MESH3 change |
|---|---|---|---|
| In a race the body floats ~0.4 m above the wheels | **Conversion**: the body was built in the *frontend* frame and used unchanged in `car.dx` | in 22/25 donors `complete.dx` = `car.dx` + constant dy (Navara 0.3932, dx = dz = 0; 3 donors differ and are rejected); candidate body draws had a frame error of -0.3932 m | body is generated once, shifted by -dy for `car.dx`; frame error now 0.0000 m (checked per draw) |
| Blocked/distorted wheel arches (frontend) | **GT geometry + conversion**: GT3 cuts the arches with *texture alpha* (`Mat1_Tex2`, 256x64, 18 % transparent); the single-texel mapping made those panels opaque; relief then pushed ~100 vertices out of the tyres | alpha analysis, hole area 0.80 GT-m2 (4 half-disc arches), 99 % inside wheel zones | alpha cutouts are baked into geometry (adaptive subdivision confined to the wheel zones), 44 invisible/overlay-only triangles dropped, carved edge snapped to a circle |
| Tyre does not fit the arch | **Donor**: Navara tyre r 0.383 m vs Impreza tyre ~0.29 m x scale | scale 1.163 from wheelbase gives an arch for r 0.337 | visual wheels scaled about their hubs by k = 0.880 (`wheel.dx`, embedded wheels in `complete.dx`) |
| Navara cab pokes through / is wrong in the Subaru | **Donor leftover** (`underdash`, crew) | donor underdash reaches y 1.375 (> Subaru roof 1.139 in the race frame once lowered) | GT cabin shell replaces `underdash` in both files; crew draws are translated rigidly (dy = -0.374) so the helmet sits 8 cm under the cabin roof |
| Race vs frontend bodies not identical | conversion | n/a | one transform per frame; consistency test compares draws byte-for-byte after the dy shift |
| Hull no longer matched the lowered body | conversion | hull spanned the old frame | hull refit in the race frame: floor kept at the donor value (hub level), top = body roof, x/z from the body |

Authentic proportions: scale is still 1.163 (see *Native proportions blocker*), so the car is ~16 % larger than a real
Impreza, but all four hubs, the axle mid-point and the hub height are now matched exactly, and the tyre/arch fit is
the GT one.

## Reproducible build

```powershell
$env:PYTHONPATH = 'src;.'
python tools/build_vmesh3_impreza_experimental.py `
  --gt-dir ".research-output/vehicles/gt-import/gt3-dumps/sb0097/sb0097_dump/CarModelSet" `
  --retail-root "D:/Game/Master Rallye/corpora/retail" `
  --retail-exe "D:/Game/Master Rallye/MRallye.exe" `
  --before-candidate-dir ".research-output/vehicles/vmesh2/exp-001/runtime/resource-root/DataGx/Vehicles/ImprezaProto" `
  --output-root ".research-output/vehicles/vmesh3/v3-exp-001"
python -m unittest tests.synthetic.test_vmesh_geometry tests.synthetic.test_vmesh_gt3_to_dx
python tools/vmesh_diagnose.py --donor-dir <retail Navara> --candidate-dir <family dir> --leftover-draws "" --out report.json
```

The driver refuses to overwrite, checks the retail EXE hash before/after, builds `car.dx`/`complete.dx`/`wheel.dx`
with `tools/vmesh_geometry.py`, runs the unchanged J.3-A/J.3-B commands, verifies the launcher and writes
`reports/validation-report.json` (including the V-MESH2 diagnostics for comparison) plus the review archive.
The V-MESH2 tools (`vmesh_gt3_to_dx.py`, `build_vmesh_impreza_experimental.py`) are untouched so `exp-001` still reproduces.

## First in-game test (human)

Same launcher flow as V-MESH2 (`research/vehicles/vmesh/README.md`, "First in-game test"), using
`.research-output/vehicles/vmesh3/v3-exp-001`. Verify first (expect `RESOURCE_ROOT_VERIFIED files=187 ...` and
`RUNTIME_BUNDLE_VERIFIED patch_operations=246 plan_sha256=567a27a8...`), then `--integrated`.

Check, in this order, and report pass/fail with screenshots:
1. **Race, side view, standing still on flat ground.** Are the four wheels inside the arches, centred under them,
   with the body clearly *not* floating and the tyres touching the ground? (V-MESH2: floating ~0.4 m.)
2. **Hover/sink.** The visual tyre (r 0.337) is smaller than the physical one (r 0.383, physics XML): expect the
   wheels ~4.6 cm *above* the road. Is that visible/acceptable? Any body scraping or tyres sunk into the road?
3. **Wheel travel.** Drive over bumps/jumps: does the tyre clip the fender (lip gap is only 3 cm)?
4. **Arches.** Round, open, no donor leftovers or black patches inside; wheels turn without hitting body panels.
5. **Vehicle Select (frontend).** Same body as in the race, arches open, wheels centred; compare with V-MESH2.
6. **Crew and cameras.** Driver/helmet inside the cabin under the roof? In cockpit/bonnet views is the camera inside
   or above the roof (cameras may not follow the lower roof; UNKNOWN)?
7. **Collision.** Wall contact at the visible body edge (hull refit); lower body (below hub level) is outside the hull.
8. Damage/glass/brake lights: same known weak points as V-MESH2 (fillers, see `../vmesh/scale-and-risks.md`).

Report anything that disagrees with hypothesis H1 below; a constant vertical error between wheels and body in the
race is the single most informative observation.

## Evidence levels

* **MEASURED (files):** frame relation, hub positions in the complete frame, GT wheelbase (2.5425 m from LOD0
  arches), alpha hole geometry, all clearance numbers in `measurements.md`.
* **HYPOTHESIS H1:** the race wheels sit where the donor's own `complete.dx` wheels sit, expressed in the `car.dx` frame
  (hub y = complete hub y - dy = 0.002 m for Navara). Supported by the donor pair relation; the absolute race anchor was
  **not** observed in the engine (the code that places wheel.dx instances was not recovered; XML `WheelBase` 2.80 does
  not equal the rendered 2.957 m, so XML dimensions are not used as anchors).
* **ESTIMATE:** GT tyre radius 0.29 m (GT3 reference side view; arch tops measured at 0.52-0.60 m are consistent).
  `--gt-wheel-radius` overrides it.

## Native proportions blocker (not hidden by arbitrary scaling)

A native-size Impreza (4.39 m, wheelbase 2.54 m, tyre r ~0.29 m) needs the *race* wheels at different positions and
radius. In the donor pipeline these come from the physics family (`Dimensions/*`, cloned unchanged by J.3-A) and
`wheel.dx`, and the mapping from XML to the rendered wheel anchor is unresolved. Until that is understood (needs a runtime
capture of wheel positions, or recovery of the wheel-instancing code), V-MESH3 uses the only principled fit available:
uniform scale from the donor wheelbase (1.163) with visual wheels shrunk to match the GT arches. A free future step is
a physics-family override of `WheelBase`, `TrackWidth*`, `WheelRadius*` plus scale = 1.0.

## Source change outside the new files

`src/master_rallye/vehicle_project.py` (tracked): when a resource is declared `topology_candidate` and the attribute-patch
reproduction fails, the topology validator is used as a fallback (needed because a uniformly scaled `wheel.dx` rewrites
the bounds footer; the position-patch path refuses that). Behaviour for all other inputs is unchanged; covered by
`ProjectValidationTests`.
