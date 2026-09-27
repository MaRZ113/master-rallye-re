# R-PHYS2 — Vehicle Param Broker population and physics constructor binding

## Result and stop state

**STATE C — stop before runtime mutation.** The numeric vehicle parameter catalog and race participant namespace are now visible in static and scene data, but the path that populates retail `Vehicles/CarN` from a named `Vehicles/<family>` record, and its binding to the ordinary race physics/contact constructor, is still not established. No game was launched and no runtime config mutation was prepared.

The R-PHYS2 scanner and the focused Ghidra audit are read-only. Machine output is ignored under `.research-output/r-phys2/`; the committed report preserves the interpretation and evidence boundary.

## Corpus search and result

The scanner walked extracted `DataGame`, `DataGx`, and `DataScene` trees for all four builds. It searched text/config files (`.xml`, `.xml#`, `.txt`, `.cfg`, `.ini`, `.csv`, `.json`, `.lua`, `.js`, `.dat`) and compiled metadata (`.dx`, `.dxb`, `.sfl`, `.hnt`) for exact numeric `Vehicles/CarN` and `Race/CarN` paths, frontend car slots, `CarType`, `CarModelDataFile`, and vehicle broker names. The scanner also extracts typed `Race/CarN/CarType` values from `<Value>` elements. For retail, both the outer `DataGame` tree and `Data.sma_unpacked` trees are considered where present.

| Result | Count |
|---|---:|
| Text/config files scanned | 913 |
| Compiled metadata files scanned | 741 |
| Source files with one or more query hits | 28 |
| Text/config or metadata hits for `Vehicles/CarN` | 0 |
| Hits for `Race/CarN/...` paths | 680 |
| Frontend selection-field hits | 16 |
| `CarModelDataFile` hits | 4 |
| Typed scene `Race/CarN/CarType` assignments | 136 |
| `VehicleParamBroker` / `VehicleParams` name hits | 0 |

The zero text/bundle hits for numeric `Vehicles/CarN` do not contradict the retail EXE string evidence below. They mean the scanned extracted corpus files did not contain that literal numeric namespace. The raw `Data.sma` archive was not searched as an opaque byte stream; its extracted text members were scanned.

`CarModelDataFile=RMonster` occurs once in `DataScene/DefaultVehicleParamBrokerRegistration.xml` per build. That is a default scene registration and does not show which named family feeds race physics. Frontend fields `Frontend/QuickRace/Car0`, `Frontend/QuickRace/Car1`, and `Frontend/Network/Car0` are likewise kept in the frontend/save identity layer.

### Scene participant assignments

The typed scene assignments are demo-only in this corpus scan: 88 entries in 11 files in demo 8.4.1 and 48 entries in 6 files in demo 9.10.0. No matching assignment was found in demo 9.3.1 or retail.

| Build | Literal values observed | Case-fold matches to named config family in that build |
|---|---|---|
| 8.4.1 | `Mercedes` (3), `Bruno` (5), `bruno` (4), `Citroen` (2), `Vehicles/bruno` (1), `Null` (73) | Mercedes (3), Bruno (9), Citroen (2) |
| 9.3.1 | none found | none |
| 9.10.0 | `Mercedes` (1), `Bruno` (5), `bruno` (1), `Citroen` (2), `Vehicles/bruno` (1), `Null` (38) | Mercedes (1), Bruno (6), Citroen (2) |
| Retail | none found | none |

For these scene files, `Race/CarN/CarType` is a typed string assignment, and some literal values case-fold match a named config family. This is **scene-level participant-to-string evidence**. It is not yet evidence that the retail loader maps the string to `Vehicles/CarN`, nor that the ordinary physics constructor consumes the resulting values. `Null`, path-like spellings, and case variants are retained literally; the scanner does not normalize them into aliases.

## Layered identity map

| Layer | Established facts | Boundary |
|---|---|---|
| Resource directory | R-PHYS1 inventories exact/case-fold directory names and `car.dx`, `complete.dx`, `wheel.dx` by build. | Presence does not establish playability or physics use. |
| Named parameter family | `vehicles.xml` uses named roots such as `Vehicles/Trooper`; no numeric `Vehicles/CarN` root was found in these XML files. | A family name is not a numeric slot ID. |
| Frontend selection | Quick Race and Network `Car0`/`Car1` fields occur in UI/save XML. | No link to `Race/CarN` or ordinary physics is established. |
| Race participant record | Retail EXE includes `Race/Car%d/CarType`, `CarID`, `PlayerType`, `WheelType`, `Transform`, and other participant keys. Demo scene files assign string values under `Race/CarN/CarType`. | Scene-level names are observed for those fixtures; no general retail mapping to the numeric parameter catalog is established. |
| Runtime parameter catalog | Retail EXE contains readers for numeric `Vehicles/CarN` data. | The writer/source that fills this numeric namespace from named families remains unknown. |
| Runtime physics/contact object | The ordinary race constructor has not been tied to the named config or to the wheel-spline reader. | Unresolved. |

In the spline-record route, `CarN` is a participant-record index: `FUN_0048EB40` iterates race-car records and reads per-index transform/spline fields. `FUN_004C0B20` uses that participant index for `Race/CarN/CarType` and passes the same integer to `FUN_004BC590`, which reads the six listed `Vehicles/CarN` wheel-geometry fields. This establishes same-index reuse for that spline path. It does not establish that this numeric vehicle slot is populated from the scene's `CarType` string, or that the same relation supplies the ordinary race physics object.

Identity controls remain separate: `Newrav`/`NewRav` are config spellings while `Rav4` is a separate model directory; retail Trooper has a named config but no same-named retail model folder; retail `forklift` has a model folder but no same-named config family. These are scanner facts, not alias or playability claims.

### Human context, separate from scanner facts

- **Human-confirmed design context:** the user reports retail Ufo intentionally has no `wheel.dx` because it is a wheel-less model. Scanner fact: the retail Ufo directory lacks `wheel.dx`.
- **Human-confirmed cut/hidden context:** the user reports `forklift` is a cut/hidden bonus vehicle associated with a hidden 25th slot. Scanner facts: the retail model directory and its model files exist; no same-named vehicle config family exists.

Neither human context item is emitted as an automated scanner conclusion.

## Retail EXE static audit

Retail `MRallye.exe` SHA-256 is `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` (3,121,214 bytes). Ghidra 12.1.4 read-only analysis and decompilation ran against the existing disposable project; it was not a runtime trace.

| Address / function | Direct observation | Limit |
|---|---|---|
| `0x006E4598`, `Vehicles/Car` → `FUN_00493600` | The helper builds a numeric vehicle parameter path using the `Vehicles/Car` prefix and an integer-formatted suffix. | The path builder does not reveal which named family populates the numeric entry. |
| `FUN_004938C0`, `FUN_00493A40` | Read multiple config groups from the numeric path and place values into parameter records. | The parsed record is not by itself proof of the active body/contact constructor. |
| `FUN_0043E4C0` → `FUN_00442D40` | Iterates numeric vehicle entries, validates/loads parameters, and constructs vehicle records. | Reviewed code does not resolve those numeric records to named XML families. |
| `FUN_0043F020` | Builds a participant path, reads `PlayerType`, prepares a numeric vehicle catalog, and attaches four wheel helper objects. | The reviewed chain does not show the family-to-catalog index or prove the helpers are physical contact points. |
| `FUN_0048EB40` | Iterates race-car records by participant index and processes `Race/Car%d/Transform` / `RecordSpline` data. | Supports `CarN` as a per-participant record index in the spline route; not a model-family ordinal. |
| `0x004C0B20`, `gaVehicleSplineRecordAI` | Reads `Race/Car%d/CarType` and passes the participant index into `FUN_004BC590`. | This is the spline-record route. It is not the ordinary race physics constructor. |
| `FUN_004BC590` | Reads WheelBase, front/rear RideHeight, front/rear TrackWidth, and front MaxDroop using numeric `Vehicles/Car%d` paths. The same participant integer is passed by `FUN_004C0B20`. | The only direct call site found is `FUN_004C0B20`; same-index reuse is confirmed only for spline-record AI. |
| `FUN_004ABCE0` | Registers the `Race/CarType` broker key alongside `CarID`, `PlayerType`, and other race keys. | Schema registration is not a writer or a named-family mapping. |
| `FUN_0048FAD0` / `FUN_0048FB90` | Uses `CarModelDataFile` in a default scene registration path; corpus value is `RMonster`. | Default scene/model registration is not race physics binding. |

The xref report contains one direct code xref for the literal `Race/Car%d/CarType`, in `FUN_004C0B20`; registration uses the separate `/CarType` key string in `FUN_004ABCE0`. No writer/population implementation was confirmed. Generic broker setters may still create these values without embedding the full key literal, so this is a bounded negative result rather than proof no writer exists.

## Trooper config survival and controls

The 9.10.0→retail Trooper comparison has 147 field rows: 121 exact, one numerically equal but text-different, and 25 changed. The changes are 16 `DamageParams`, 7 `Engine`, 1 `Chassis`, and 1 `Suspension`; the Dimensions and Steering groups have no value changes.

Comparing paths changed in Jump and Navara (9.10.0→retail) shows that 21 of Trooper's 25 changed paths also change in at least one control family. Four paths are Trooper-only relative to those controls:

- `DamageParams/EngineThresholdDamageSpeed`
- `DamageParams/MaxTyreDamage`
- `DamageParams/SteeringThresholdDamageSpeed`
- `Suspension/Front/ToeIn`

This is evidence for a systematic retail damage/engine retune plus four Trooper-specific path changes within these XML comparisons. It does not prove that all, or any particular one, is consumed by the ordinary race physics constructor. Existing human reports about Trooper resource transfer, rendering, damage, and race-wheel placement remain project runtime observations without retained exact source hashes/measurements; they are not used as proof for this mapping.

## Runtime gate and next step

Do not mutate a named family yet. First establish a complete call/data path for (1) the writer/source of `Race/CarN/CarType` or the actual selection key, (2) its conversion into the numeric `Vehicles/CarN` catalog, and (3) the ordinary constructor/contact reader that consumes the selected fields. Once those three joins are backed by code or runtime evidence, a one-field scratch experiment can be designed with visual placement and physical contact measured separately.

## Reproduction

From the repository root:

```powershell
python tools/scanner/r_phys2.py `
  --corpora-root 'D:\Game\Master Rallye\corpora' `
  --rphys1-analysis '.research-output\r-phys1\r-phys1-analysis.json' `
  --ghidra-xrefs '.research-output\r-phys2\static\retail-vehicle-string-xrefs.json' `
  --output-dir '.research-output\r-phys2'
```

The output retains hit paths, offsets, snippets, source hashes, typed scene assignments, Ghidra string xrefs, the layered identity map, and field-by-field Trooper/control deltas. It writes only to ignored research output; the external corpora and executables are read-only.

## R-PHYS2.1 follow-up

The STATE C result above records the R-PHYS2 stopping point. The focused follow-up subsequently established the named-family-to-runtime-CarN broker statically: the ordinary local race loop passes participant index `N` into `FUN_0044ED50`, which derives a family name from the participant's numeric `_CarClass`, calls `FUN_00493E30` to read `Vehicles/<family>`, optionally applies a separately derived `Player1`/`Player2` modifications subtree, then calls `FUN_004938C0(N, ...)` to write `Vehicles/CarN`.

The selected Navara's live `_CarClass` and actual string at the broker call have not yet been observed. The full evidence boundary, Trooper/forklift config checks, and one read-only x32dbg procedure are in [R-PHYS2.1 named-family resolution](r-phys2.1-named-family-resolution.md). This follow-up does not establish downstream physical-contact construction or authorize a runtime mutation.
