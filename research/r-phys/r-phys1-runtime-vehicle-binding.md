# R-PHYS1 — runtime vehicle broker, wheel hardpoints, and physics binding

## Result

R-PHYS1 establishes a bounded **retail spline-playback wheel presentation path** and inventories the named vehicle configuration/model families across four builds. It does **not** establish the active named-config-to-`CarN` broker binding for ordinary race vehicle construction, nor any equality between spline wheel transforms and physical contact points. A runtime config mutation is therefore not prepared.

The corrected stopping point is **STATE C**: one narrow blocker remains—identify the source/population path for `Vehicles/Car%d` values used by the active vehicle/physics constructor. The only direct read path established for the six dimension/suspension fields is the spline-record AI path described below. No game was launched for this phase; extracted game data and EXEs were read-only.

## Inputs and reproducibility

`tools/scanner/r_phys1.py` parses exact XML roots, inventories model directories, preserves file lists and hashes, compares same-spelled families, aggregates schema observations, and writes only under ignored `.research-output/r-phys1/`.

| Build | `vehicles.xml` bytes / SHA-256 | EXE bytes / SHA-256 |
|---|---|---|
| Demo 8.4.1 | 317,390 / `bd3efca271e27f4d00cc4f5846c4aa0bf74836dac223bc64339d28a05a65f4f7` | 2,084,926 / `bbdfdb709ed41b10461b233b2f5c55403f1b6640f57d9e440476211e51ce75be` |
| Demo 9.3.1 | 574,802 / `d32c9ec40cb4d29b8c2e7c12ab401518e025973c6a8bcd4aa255f6fe2402b55a` | 2,637,886 / `931cfc4e0c520c26581b0c1173d1beb586facd17176b885666f455090f646680` |
| Demo 9.10.0 | 718,782 / `5af150d6ce98fe1e8d1e968c87a235d30c5b77d8a02dc8d11fcfaf1d4f794a52` | 2,883,646 / `13eaa642d0aabdfc47911a8606b02d9fc8d57d74328b36a0d3d618aadf1e0b78` |
| Retail | 757,388 / `a6762bb20999c7224c71b9f5d1d7edca55bcea147ff9f973300a8cf8d350aee0` | 3,121,214 / `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` |

The scanner sees 19, 26, 33, and 35 named config families respectively. Across all four `vehicles.xml` files it found **no `Vehicles/CarN/...` XML family roots**; the extracted XML instead contains named family roots plus a distinct `Tyres` data family. The retail config has 35 named families and 26 model directories. Full root/folder classification is in [the retail inventory report](r-phys1-retail-config-only-vehicles.md); every path and all field comparisons remain in the ignored JSON output.

## Cross-build config evidence

Trooper values and family sizes extracted literally from each `vehicles.xml`:

| Build | Trooper fields | WheelBase | Track F/R | Radius F/R | Ride height F/R | MaxDroop F/R |
|---|---:|---:|---:|---:|---:|---:|
| 8.4.1 | 121 | 2.4 | 1.65 / 1.65 | 0.38 / 0.38 | 0.05 / 0.05 | 0.1 / 0.1 |
| 9.3.1 | 150 | 2.4 | 1.65 / 1.65 | 0.38 / 0.38 | 0.05 / 0.05 | 0.1 / 0.1 |
| 9.10.0 | 147 | 2.4 | 1.65 / 1.65 | 0.38 / 0.38 | 0.05 / 0.05 | 0.1 / 0.1 |
| Retail | 147 | 2.4 | 1.65 / 1.65 | 0.38 / 0.38 | 0.05 / 0.05 | 0.1 / 0.1 |

These nine fields compare numerically equal across all four builds. This is config-text evidence; it does not establish that each value is consumed by the same runtime subsystem. Trooper’s complete config changes elsewhere: 9.3.1→retail compares 160 path rows (10 added, 13 removed, 28 value-changed, 108 exact, one numerically equal but text-different); 9.10.0→retail compares 147 rows (25 value-changed, 121 exact, one numerically equal but text-different). The tool preserves raw types, strings, numeric deltas, additions/removals, and paths rather than flattening whole vehicle records.

Controls show that these named configs evolve independently:

- Jump has WheelBase 2.5 in all four corpora. Track front/rear is 1.7 and ride height 0 in 8.4.1/9.3.1, then track 1.6 and ride height 0.08 in 9.10.0/retail.
- Navara is present in 9.10.0 and retail: WheelBase changes 2.6→2.8; track stays 1.7 and ride height stays 0.05. Across 147 common paths, 26 values differ.
- Names such as `Rav4`, `Newrav`, and `NewRav` are preserved as separate literal roots. A model-directory spelling or visual similarity is not used as an alias rule.

## Static retail executable evidence

Retail EXE static inspection used Ghidra 12.1.4; its exact hash and size are recorded above. The disposable Ghidra project, decompilation, and script are ignored under `.research-output/r-phys1/` and `dist/r-phys1-ghidra/`. The checked output is not a runtime trace.

| Address / class string | Established observation | Scope limit |
|---|---|---|
| `0x004BFFA0`, `gaWheelSplinePlaybackAI` | Constructor stores wheel index and a per-car record; cached values are copied into instance fields `+0x18` WheelBase, `+0x1C` front ride, `+0x20` rear ride, `+0x24` front track, `+0x28` rear track, `+0x2C` front MaxDroop. | A named spline playback AI class, not evidence by itself of the normal race body/physics constructor. |
| Factory region near `0x004BFAE0–0x004BFFxx` | Formats `Vehicles/%sAlpha/wheel`, loops indices 0–3, allocates four `0x30`-byte wheel instances, and calls the constructor above. | Establishes a four-wheel presentation-object construction path in this AI/factory region. |
| `0x004C00D0` | Chooses front axle for indices 0–1 and rear for 2–3; applies signed half TrackWidth and half WheelBase offsets, the corresponding negative ride-height term, and `max(dynamic_sample, -frontMaxDroop)`. It then maps local components through an interpolated basis into an output transform. | Formula is for the wheel spline playback transform; it is not proven to be a physical contact/hardpoint formula. |
| `0x004C0B20`, `gaVehicleSplineRecordAI` | Reads `Race/Car%d/CarType` and `Race/RaceName`, then calls `0x004BC590` with the same numeric record index. | The constructor lies in a race spline-record route; the `CarType` read does not prove how the named family config is populated. |
| `0x004BC590` | Formats six `Vehicles/Car%d/...` paths: WheelBase, front/rear RideHeight, front/rear TrackWidth, and front MaxDroop. Its only direct call site found is `0x004C0B20`. | Proves field reads on the spline-record AI path only. No general vehicle physics caller or named-family mapping was established. |
| `0x0048EB40` | Calls the spline-record constructor while processing race-car records. | This links the read path to race-record/spline setup, not the standard vehicle physics constructor. |

The local transform helper in `src/master_rallye/vehicle_config_analysis.py` captures only the branch/offset arithmetic supported by `0x004C00D0`; it deliberately names itself `wheel_spline_playback_local_offset`. A test checks all four index signs and the vertical clamp. It does not apply the outer matrix or claim world-space wheel placement.

An existing scene registration in `DefaultVehicleParamBrokerRegistration.xml` names `CarModelDataFile=RMonster`; existing R4A work also establishes that `DataGame/Game.xml` registers the vehicle broker. Neither artifact links `Race/Car%d/CarType` or the spline `Vehicles/Car%d` keys to a named `Vehicles/<family>` physics record. Retail named-config XML contains no `CarN` roots. Therefore the runtime backing source/population step remains unknown.

## Complete-model wheel geometry and limits

The existing R-BRIDGE2 analyzer reads four `$cylinder` wheel spans in each complete model (using the TXT sidecar for Navara 9.10.0 when the hierarchy node is not decoded), transforms GXM coordinates to DX coordinates, and reports mesh AABB centers. They are **visual mesh bounds**, not runtime hardpoints.

| Build / model | Left/right DX X centers | Longitudinal DX Z endpoints | Derived track / wheelbase |
|---|---|---|---:|
| 9.3.1 Trooper | -0.752511… / +0.752617 | -1.183466 / +1.211832 | 1.505128 / 2.395297 |
| 9.3.1 Rav4 | -0.748669 / +0.746453 | -1.263246 / +1.290315 | 1.495122 / 2.553561 |
| 9.3.1 Jump | -0.749443 / +0.748064 | -1.264826 / +1.257237 | 1.497507 / 2.522063 |
| 9.10.0 Navara | -0.786681 / +0.801706 | -1.338368 / +1.445282 | 1.588388 / 2.783650 |

Front/rear labels are supported for the first three by positive-Z front landmarks; Navara’s front direction was not independently identified. Config wheelbase/track do not exactly equal the complete-model mesh bounds. For example, Trooper config says wheelbase 2.4 and track 1.65 while its GXM mesh-derived figures are 2.395297 and 1.505128. This difference prevents treating either measurement as a hardpoint without an alignment/runtime proof.

## Runtime transfer observation and test readiness

Prior human runtime work reported a Trooper body/resources loaded into the retail Navara slot, with model rendering and damage working; race wheel placement was wrong while complete-model wheel placement looked correct. Exact source asset hashes and measured race wheel coordinates were not recorded. This is compatible with slot-driven wheel placement, but does not identify the `CarN` source or distinguish a spline playback object from the ordinary race vehicle.

No human runtime test was prepared in this phase. Editing a named `vehicles.xml` family would be an uninterpretable experiment until we know it feeds the numeric `CarN` broker values consumed by the relevant constructor. It may also change physical handling, while the transform observed statically is only the spline playback path.

## R4G / production implications

This phase improves source/config provenance but does not authorize a production physics change. Keep existing R4G whole-config/physics linkage as unresolved; do not use `WheelBase`, TrackWidth, ride height, or MaxDroop merely because their names and a spline transform appear to match. The reusable read-only config diff/schema and wheel-geometry analyzer can support later asset selection and report generation without changing production behavior.

## Readiness by component

| Component | Status | Evidence / boundary |
|---|---|---|
| Retail and demo vehicle-family inventory | `IMPLEMENTABLE_NOW` | Exact parser, hashes, directories, and cross-build tables; report is reproducible from the scanner. |
| Full config diff and literal schema | `IMPLEMENTABLE_NOW` | Field path/type/raw value and per-build provenance retained; no semantic interpretation required. |
| Complete-model wheel mesh bounds | `IMPLEMENTABLE_WITH_CONSERVATIVE_POLICY` | Existing parser supports the observed node layouts; Navara 9.10.0 uses sidecar fallback; these are not physical points. |
| Spline-record `CarN` reads | `IMPLEMENTABLE_WITH_CONSERVATIVE_POLICY` | Static six-field key list and observed caller are established for `gaVehicleSplineRecordAI`. |
| Spline wheel visual transform arithmetic | `IMPLEMENTABLE_WITH_CONSERVATIVE_POLICY` | Address `0x004C00D0` and all four index cases are captured; outer basis and runtime use remain contextual. |
| Named family → numeric `Vehicles/CarN` population | `NEEDS_MORE_ORACLE_DATA` | No `CarN` XML roots, serializer, alias, or broker initialization link located. |
| General race vehicle visual transform source | `NEEDS_MORE_ORACLE_DATA` | Prior runtime wheel-placement observation exists; the static path found is spline playback only. |
| Physical suspension/contact-point binding | `UNRESOLVED` | No matching general vehicle/contact constructor path established. |
| Safe named-config runtime mutation | `NEEDS_MORE_ORACLE_DATA` | Would not be controlled until the active source path is established. |

### Next phase boundary

Resolve the one blocker: locate the creation/population path that supplies the named configuration values to numeric `Vehicles/CarN` for the active vehicle renderer/physics constructor. Once that path is proven, select a single wheel field and design a scratch-only human validation that observes both rendered placement and physical contact separately. Do not infer physics behavior from `gaWheelSplinePlaybackAI` alone.
