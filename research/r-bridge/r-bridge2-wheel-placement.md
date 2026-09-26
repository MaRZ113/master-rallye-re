# R-BRIDGE2 — runtime wheel placement mapping

## Current result

The complete-model wheel geometry is a usable visual reference. Retail executable disassembly also shows that the `wheel.dx` model is instantiated four times and each instance receives a transform derived from per-car dimensions plus per-wheel state. The exact connection from the executable's numeric `Vehicles/Car%d/...` broker paths to the extracted named roots such as `Vehicles/Navara/...` is **UNRESOLVED**. A one-field runtime patch is therefore not ready.

This stops at the R-BRIDGE2 gate **B**: model/config relationship is strongly supported, but the precise config alias/record format that must be edited remains unresolved. We did not launch the game or alter a game asset.

## Complete-model geometry

The analyzer follows the four `wheel $cylinder...` mesh spans in `complete.gxm` (or the matching TXT sidecar only when the current hierarchy parser rejects the node layout), takes referenced Vector C positions, and applies the observed source-to-DX transform `(x, y, z) -> (x, z, -y)`. Centers below are AABB centers of the named wheel meshes, not proven race hardpoints. Lateral sides are reported by DX-x sign; positive/negative longitudinal endpoints are retained where front direction is not independently identified.

| Build / vehicle | Front, lateral-negative | Front, lateral-positive | Rear, lateral-negative | Rear, lateral-positive | Geometric track / wheelbase |
|---|---|---|---|---|---|
| 8.4.1 / Jump | `(-0.749443,-0.069033,1.257237)` | `(0.748064,-0.069033,1.257237)` | `(-0.749443,-0.069033,-1.264826)` | `(0.748064,-0.069033,-1.264826)` | `1.497507 / 2.522063` |
| 9.3.1 / Jump | same as 8.4.1 | same | same | same | `1.497507 / 2.522063` |
| 9.10.0 / Jump | `(-0.749443,0.382078,1.257237)` | `(0.748064,0.382078,1.257237)` | `(-0.749443,0.382078,-1.264826)` | `(0.748064,0.382078,-1.264826)` | `1.497507 / 2.522063` |
| 9.3.1 / Trooper | `(-0.752512,0,1.211832)` | `(0.752617,0,1.211832)` | `(-0.752511,0,-1.183466)` | `(0.752617,0,-1.183466)` | `1.505128 / 2.395297` |
| 9.3.1 / Rav4 | `(-0.748669,0,1.290315)` | `(0.746453,0,1.290315)` | `(-0.748669,0,-1.263246)` | `(0.746453,0,-1.263246)` | `1.495122 / 2.553561` |
| 9.10.0 / Navara | front endpoint not independently verified | front endpoint not independently verified | rear endpoint not independently verified | rear endpoint not independently verified | `1.588388 / 2.783650` between the two z-end center pairs |

For Jump, Trooper, and Rav4, a headlight/front-grille mesh lies at positive DX-z, supporting the front/rear labels above. The 9.10.0 Navara complete sidecar does not yield a usable front landmark span, so its signs remain unlabeled. Every listed wheel span contains 162 triangle records and 91 unique Vector C positions. The 9.10.0 Navara spans came from `complete.txt` because that GXM uses a hierarchy node type/version not currently decoded by the hierarchy parser.

The 9.10.0 Jump wheel centers preserve X and longitudinal Z from 9.3.1 while changing vertical DX-y by `+0.451111`. Its extracted vehicle XML also changes track width from 1.7 to 1.6 and ride height from 0.0 to 0.08 between those builds. These are observed parallel changes; they do not prove a single cause for the vertical shift.

Configuration values provide useful comparisons, but do not exactly equal the geometric centers. Examples: 9.3.1 Trooper XML lists wheelbase 2.4 and track widths 1.65; 9.3.1 GXM center-to-center measurements are 2.395297 and 1.505128. Retail Navara lists wheelbase 2.8 and track widths 1.7, while the 9.10.0 Navara complete model measures 2.783650 and 1.588388. Do not substitute these measurements as hardpoints without a runtime alignment proof.

## Retail executable trace

Static evidence is from retail `MRallye.exe`, SHA-256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` (3,121,214 bytes). Focused disassembly is retained under ignored `.research-output/r-bridge2/notes/`.

| Address | Observed role |
|---|---|
| `0x004BFE00` | Formats `Vehicles/%sAlpha/wheel`, creates four objects in a loop with index 0–3, and attaches each created instance. |
| `0x004BFFA0` | Constructor stores the per-car record and wheel index, then copies six dimension/state values from the per-car table into the wheel instance. |
| `0x004BC590` | Reads WheelBase, front/rear RideHeight, front/rear TrackWidth, and front MaxDroop using broker keys formatted as `Vehicles/Car%d/...`. |
| `0x004C00D0` | Selects signed half-wheelbase and half-track offsets by wheel index and combines them with ride-height/per-wheel state to construct the wheel model transform. |

Instance field snapshots observed in the constructor:

| Instance offset | Value |
|---:|---|
| `+0x10` | wheel index 0–3 |
| `+0x18` | WheelBase |
| `+0x1C` | Front RideHeight |
| `+0x20` | Rear RideHeight |
| `+0x24` | TrackWidthFront |
| `+0x28` | TrackWidthRear |
| `+0x2C` | Front MaxDroop |

The switch table at `0x004C06CC` associates indices 0–1 with the front axle and positive half-wheelbase; indices 2–3 use the rear axle and negative half-wheelbase. The lateral signs alternate. The transform code uses the front/rear ride-height and track-width fields for the corresponding axle. This establishes that race wheel **visual-instance placement** is not encoded solely by the separate `wheel.dx` geometry.

The function consumes per-wheel dynamic state when producing its transforms. The surrounding physics code was not traced far enough to show whether the same fields also govern contact/suspension positions. Visual-transform construction is established; visual-versus-physical equivalence is not.

## Config alias blocker

The six executable templates use numeric roots:

```text
Vehicles/Car%d/Dimensions/WheelBase
Vehicles/Car%d/Dimensions/TrackWidthFront
Vehicles/Car%d/Dimensions/TrackWidthRear
Vehicles/Car%d/Suspension/Front/RideHeight
Vehicles/Car%d/Suspension/Rear/RideHeight
Vehicles/Car%d/Suspension/Front/MaxDroop
```

Extracted retail `DataGame/vehicles.xml` has 36 named `Vehicles/<vehicle>/...` roots and no `Vehicles/CarN/...` roots. The exact broker alias, generated runtime record, or another data source that binds numeric race car IDs to named vehicle configuration is not identified. Consequently, the report does not say that the method reads `Vehicles/Navara/...` just because the current body was installed in the Navara slot.

The user-confirmed runtime case is a Trooper body/resources in the retail Navara slot. Trooper's 9.3.1 complete-model geometric track is `1.505128`; Navara retail XML says `TrackWidthFront/Rear=1.7`. This is consistent with inherited slot-driven placement, but without the alias proof or measured race wheel coordinates it is not a causal measurement. The Rav4 transfer is a second report of the same general wheel-placement issue, but its exact retail slot was not specified.

## Test readiness and next step

**No runtime patch is prepared.** Changing `vehicles.xml` TrackWidthFront from 1.7 to 1.6 would not be a controlled test until the `Car%d` record-to-XML mapping is proven. It could also affect physical handling; visual-only isolation is not established.

The next narrow research task is to resolve the retail broker mapping between numeric `Car%d` records and named `Vehicles/<name>` roots (or find the actual serialized backing data), then determine whether the four visual transforms can be overridden without changing contact physics. After that, prepare one reversible front-axle test with exact paths and old/new values. No new slot or broader physics migration is in scope.
