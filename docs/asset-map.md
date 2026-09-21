# Asset map (Phase R0)

## Scope and provenance

The source is an external, extracted `Data.sma` tree. It was read only. No game
asset or executable is copied into this repository, and neither `MRallye.exe`
nor the patched executable was inspected.

The reproducible inventory covers 7,596 files (806,539,849 bytes):

| Extension | Files | Bytes | Median bytes |
|---|---:|---:|---:|
| `.dxt` | 6,960 | 305,808,064 | 65,556 |
| `.dx` | 160 | 451,488,195 | 129,711 |
| `.txt` | 149 | 6,923,597 | 8,363 |
| `.xml` | 122 | 23,268,179 | 58,817 |
| `.dxb` | 113 | 265,604 | 904 |
| `.hnt` | 54 | 326,491 | 3,044 |
| `.sfl` | 36 | 18,169,268 | 462,038 |
| `.xml#` | 2 | 290,451 | 145,225.5 |

Counts are **CONFIRMED** by `research/r0/inventory.json`.

## Root roles

- `DataGame/`: 23 human-readable configuration files. `vehicles.xml` holds
  vehicle physics/config broker keys, not model geometry. **CONFIRMED**.
- `DataGx/`: 7,381 graphical resources. It contains course, vehicle, frontend,
  HUD, font, marker, miscellaneous, and particle families. **CONFIRMED**.
- `DataScene/`: 191 scene/runtime/frontend files. **CONFIRMED**.

## Cross-extension relationships

There are 190 same-directory, same-stem cross-extension groups:

- 136 `.dx` + `.txt` groups;
- 52 `.hnt` + `.xml` groups;
- 2 `.hnt` + `.xml` + `.xml#` groups.

This strongly establishes the `.txt` files as sidecars for most `.dx` files
and `.hnt` as dependency manifests adjacent to scene XML. **HIGH**; the pairing
is structural, while the exact producer/consumer contract is not yet known.

## Vehicle reference chain

For the lab sample, the observed chain is:

```text
DataGame/vehicles.xml
  Vehicles/Astero/... (147 broker values)
DataGame/Modifications.xml
  Vehicles/Astero/... (26 persistent modification values)
DataScene/RaceTest/smash.xml
  Value Name="Car Name" Value="Astero"
        |
        v
DataGx/Vehicles/Astero/
  car.dx + car.txt
  complete.dx + complete.txt
  wheel.dx + wheel.txt
        |
        v
TXT: material names, ordered texture slots, hierarchy/mesh names,
     sequential mesh Index/Size spans
DX: vertex arrays, UVs, local index buffer, used material/draw records,
    texture resource stems (but no mesh names observed)
        |
        v
33 referenced TGA names normalize to 33 present *-tga.dxt files
```

The direct `Car Name = Astero` scene selection is **CONFIRMED**. The convention
that this identifier selects `DataGx/Vehicles/Astero` is **HIGH**: it is exact
case-insensitively across the configuration/assets corpus, but the executable
loader has not been inspected.

The TXT-to-DXT normalization is **CONFIRMED** for Astero: e.g.
`AsteroWheel64.tga` becomes `asterowheel64-tga.dxt`; all 33 unique Astero
references resolve. The TXT stores original exporter paths such as
`D:\projects\MRallyeTNG\DataGx\Vehicles\Astero\...`; those paths are historical
metadata, not runtime paths.

## Human-readable findings

`car.txt`, `complete.txt`, and `wheel.txt` expose:

- ordered materials and 1-2 primary texture slots;
- `HasAlpha`, `UsesAlpha`, and `IsNoise` flags;
- mesh/object names and brace nesting (hierarchy);
- sequential `Index` and `Size` spans;
- semantic suffixes such as `$paint`, `$glass`, `$chrome`, `$rubber`, and
  `$cylinder_0.766_0.39`.

They do not expose explicit vertex positions, UV coordinates, transforms,
bounding boxes, binary byte offsets, or export setting blocks. **CONFIRMED**
for the three Astero sidecars.

`DefaultVehicleParamBrokerRegistration.xml` contains
`CarModelDataFile = RMonster`; `DefaultTyreParamBrokerRegistration.xml` contains
`TyreType = Studded`. These broker files configure identifiers, not binary
layouts. **CONFIRMED**.

`Damage.xml` and `collision.xml` define global/vehicle-specific physics
parameters. `Surface.xml` maps surface types to texture-like resource stems,
for example `misc\tracks\tarmac`. None directly describes `.dx` layout.
**CONFIRMED**.

## Sample selection

- Primary: `Astero` — common 3 DX + 3 TXT layout and 33 DXT resources.
- Normal validation: `Bruno` — same layout, independent payload and 34 DXT
  resources.
- Unusual validation: `Ufo` — only `car` and `complete` pairs, no `wheel`
  resource, and the smallest vehicle directory by file count among the sample
  candidates.

Astero is not structurally atypical: 20 of 26 vehicle directories have the
full six-file semantic layout. **CONFIRMED** from the inventory.

## Configuration/asset mismatches

Configuration-derived identifiers without a same-named asset directory include
`Bowler`, `Cherokee`, `Citroen`, `Custom`, `Megane2`, `Mercedes`, `Navarabig`,
`Pajerostripe`, `Terios`, and `Trooper`. `Tyres` is a namespace captured by the
same `Vehicles/<name>/...` grammar, not a vehicle. `forklift` is the one asset
folder without a matching `Vehicles/<name>/...` configuration namespace.
These may be legacy aliases, unused content, or indirect selections; the cause
is **UNKNOWN**.

## Machine-readable sources

- `research/r0/inventory.json`: one record per file plus aggregate statistics.
- `research/r0/relationships.json`: stem pairs, duplicate groups, vehicle
  profiles, parsed XML corpus summary, sidecar material/mesh/texture data, and
  the vehicle reference graph.
- `research/r0/mesh-proof.json`: compact results from the experimental DX
  leading-section parser; it contains counts/ranges, not copied geometry.
- `research/r0/dxt-probe.json`: archive-wide DXT header/size invariants.
