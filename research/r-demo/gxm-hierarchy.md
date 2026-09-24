# Trooper GXM source hierarchy

The matching demo-8.4.1 TXT sidecars are source-side textual evidence. `src/master_rallye/sidecar.py` parses their materials and mesh `Index`/`Size`; the GXM parser validates the corresponding material count and indexed record count. The ordered printable names at the end of each GXM match the sidecar's `Model` plus every mesh name exactly, including case, spaces and the source typo `$perpsex`.

| GXM role | GXM materials | Sidecar materials | Sidecar mesh entries | Sidecar maximum `Index+Size` | GXM indexed records | Ordered names match |
|---|---:|---:|---:|---:|---:|---|
| `demo-8.4.1:DataGx/Vehicles/Trooper/car.gxm` | 22 | 22 | 28 | 1,979 | 1,979 | yes, 29 incl. Model |
| `demo-8.4.1:DataGx/Vehicles/Trooper/complete.gxm` | 25 | 25 | 29 | 2,375 | 2,375 | yes, 30 incl. Model |
| `demo-8.4.1:DataGx/Vehicles/Trooper/wheel.gxm` | 5 | 5 | 2 | 252 | 252 | yes, 3 incl. Model |

The car sidecar places `shell` at records 0–97; `interior` contains `driver01` / `head01` / `helmet01 $paint` and `driver02` / `head02` / `helmet02 $paint`. `$chull(Trooper)` is a separate final mesh span, records 1911–1978 (68 records). Complete has no crew spans in its sidecar and includes four wheel meshes with `$cylinder_0.766_0.39` through `_0.42` names and hub children. Wheel has one wheel mesh (162 records) with a hub child (90 records).

`demo-8.4.1:DataGx/Vehicles/Trooper/complete.gxm` and `TrooperFrontEnd.gxm` are byte-identical. Their names are a same-build alias, not a universal rule for all vehicles or versions. The binary hierarchy's control fields after the validated vector C array are still opaque; parent-child relationships above are from same-build sidecar indentation and names (**SOURCE_SIDE_EVIDENCE**), corroborated by GXM name order and record spans.
