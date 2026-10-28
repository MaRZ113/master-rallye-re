# Auto Import: universal GT3 profile and automatic Demo features — 28 October 2026

Goal: import GT3/GT4 cars and Master Rallye Demo cars without per-car JSON. The
result should look as if Steel Monkeys made the car: MR-size proportions, MR
tyres, crew behind the glass, breakable glass, a working brake glow and no huge
atlases. The owner-accepted Subaru Impreza Prototype (V-MESH4.x) is the style
reference.

## What changed

| Area | Before | Now |
| --- | --- | --- |
| GT3 profile | Hand-written JSON per car: hubs, rim/tyre envelopes, donor hashes, evidence strings | `gt_auto_profile.derive()` builds the whole profile from the source and the donor |
| Wheel arches | Measured by hand | Side-view raster of the outer skin. Texture-alpha cut-outs count as holes, reflection overlays and ground strips are ignored, and a circle is fitted per axle |
| Fitment | Explicit translation, no scaling | Body is scaled uniformly to the donor's embedded hub wheelbase and its arches are placed on the donor hubs. The visual tyre keeps the donor MR envelope, limited by the arch. Rim/tyre ratio is 0.80, the value accepted for the Subaru |
| LOD | Explicit | Always LOD0, per the owner's decision: LOD1 can lose the real arches |
| Tyres | GT3 tyre image on stock topology | Standard: donor MR tyre textures and UVs. Full: GT3 tyre image |
| Crew | None for GT3 | Standard: stock Navara seated pair. It is placed under the detected roof panel; antennas and wings are excluded |
| Glass / brake | None for GT3; hand-written recipe for Demo | `auto_features`: native `screenfront/rear/left/right` zones (breakable) and a `blight` lit/glow switch |
| Unsupported GS pass | Whole import raised | `material_policy.strict=false` skips the pass and records it in the report. GT4 defaults stay strict |
| Texture budget | Source atlas size | Standard: `max_texture_dim=256` box reduction (UVs are normalized, so geometry is unchanged) |
| Donor | Bridge admitted only Navara/T2 | Any retail family and class T1/T2. `rank_donors` suggests families by wheelbase and track |
| Heritage edition | Unknown EXE/assets rejected | Allowed with a recorded warning (the EXE is never executed). `--strict-edition` restores the old behaviour |
| Missing Demo texture | Import rejected | Exact sibling-family file, otherwise a neutral placeholder. Both are recorded |
| Project bridge | Flat scene or a single `blight` | New `native_state_scene_candidate` resource validated by `native_states.validate_state_scene` |

Commands:

```
python tools/vehicle_sdk.py auto-import-gt3 --source <gt3>/cars/day/<code>.gz --donor <retail>/DataGx/Vehicles/Navara --output <dir> [--mode full] [--rank-donors <retail>/DataGx/Vehicles] [--author --name .. --manufacturer .. --model ..]
python tools/vehicle_heritage.py create ...            # automatic features by default
python tools/vehicle_heritage.py create ... --no-auto-features
```

## Evidence (offline only, no game launched)

- Demo Trooper 9.3.1: the automatic recipe is **identical** to the owner-accepted
  hand recipe. The zones, triangle IDs, brake draw/triangles and lit/glow texels
  are all byte-equal.
- Demo 9.x families with automatic features: Trooper, Forester\*, NewRav, Tata,
  Jump (both editions), Wildcat (both), Simmbugghini. Every sidecar triangle was
  matched (exact or ≤1 cm nearest).
  \*Forester has no `complete.dx` in that Demo, so a Heritage project cannot be
  staged; the recipe itself derives fine.
- Not automatic:
  - KiaSportage: an env-only `Null` diffuse draw (state 6) is outside the native
    repack grammar. The import stays valid without features.
  - Demo Megane 9.10: the source fails global index validation.
  - Demo Navara 9.10: per-draw material prefix words differ.
  - Demo 8.4.1: rev127 models are unsupported.
- GT3 corpus (SCUS_971.02, 287 `cars/day` members): **257 automatic profiles
  (89.5%)**. The median wheelbase is 2.511 m.
  - Detected wheelbase against the published value: Impreza 2.509/2.52,
    Viper 2.439/2.44, Evo 2.502/2.51, Focus 2.635/2.615, 206 2.456/2.468,
    Clio V6 2.528/2.51.
  - 30 failures: 20 have no detectable arches (race prototypes and similar),
    7 have an unresolved callback branch, 1 exceeds the source size budget, and
    2 more fail the arch check. These cars keep the manual profile path.
- End-to-end builds in standard mode: Subaru, Lancer Evo, Focus WRC, 206 WRC,
  Viper, Xsara and Clio V6. All have glass zones and crew. All except the Viper
  have a brake glow (its lamp texture has no red texels).
- The Clio author project passes `project-validate` and `project-build`.
- Subaru standard: body ≈2000 triangles plus crew and native state copies
  (car.dx 2692). Texture cache 3.38 MB (the full mode is 4.46 MB).
- Tests: 953 + 13 new synthetic tests pass (2 optional skips).

Private evidence is in `.research-output/vehicles/auto-import/`: the corpus
JSON, renders and Heritage projects.

## Owner gates (not claimed)

- In-game D3D8 appearance, shattering of the generated glass zones and the GT3
  brake glow have not been checked.
- Race wheel anchoring follows the existing H1 assumption: donor hubs, with the
  body scaled to that wheelbase.
- Non-Navara donors have not been gameplay-tested.

## Next steps

1. Per-axle arch heights for very low cars: a physics `WheelRadius` override when
   the arch limits the tyre.
2. A callback-branch search for the 7 unresolved GT3 cars.
3. A GT4 adapter onto the same `auto_features` + fitment path. `build_gt4_vehicle`
   already shares `compile_draws`.
4. An optional decimation pass for cars above about 3000 body triangles. LOD0 is
   kept as the owner requested.

## Addendum — Demo 8.4.1 models re-baked by Demo 9.10.0 (XMAS `DataGx/Vehicles/841`)

All seven families import with automatic features and pass `project-validate` and
`project-build`: Forester, Jump, LandCruiser, Mercedes, Trooper, WildCat, megane.
The fixed Forester includes its `complete.dx`.

- `family_folder` admits nested collections, and the inventory recurses into them.
- `physics_donor='auto'` selects the same-named retail `vehicles.xml` family,
  matched without regard to case.
- Retail Megane references the tyre tables `FrontTest`/`RearTest`, which do not
  exist. They are overridden with `harddirt`, as the sibling Megane2 uses, and
  the override is recorded in the physics profile notes.
- The 9.10 bakes store the global index table in a different order. WildCat also
  has one triangle of 309 that differs between its local and global tables. The
  global table is rebuilt from the local draw indices
  (`REV135_GLOBAL_INDEX_TABLE_REBUILT`); vertices and local indices are unchanged.
  The same repair fixes Demo 9.10 Megane.
- WildCat 841 body materials (`cata128`, `cdoor128`, `catflag16`) carry the
  alpha-blend flag on fully opaque textures, so the body showed through.
  `normalize_false_blend` clears only that byte when at most 1% of texels have
  alpha below 250. The fix is recorded per draw. No other family changed.
- The sidecar is discovered by mesh span: the 841 Trooper ships `Trooper.txt`
  rather than `car.txt`, and its brake mesh has 12 lens triangles.
