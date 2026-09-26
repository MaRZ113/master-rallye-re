# R-PHYS1 — retail vehicle configurations without exact model folders

## Scope and evidence boundary

This report inventories the retail `vehicles.xml` family roots against exact top-level directories in extracted retail `DataGx/Vehicles`, then checks those names against the three separately retained demo corpora. It reports filesystem and XML facts only. A config entry or directory does not, by itself, prove a selectable/playable vehicle, a resource binding, or an alias.

The scanner is read-only with respect to source corpora and writes its detailed inventory beneath ignored `.research-output/r-phys1/`:

```powershell
$env:PYTHONPATH = 'src'
python tools/scanner/r_phys1.py `
  --corpora-root 'D:\Game\Master Rallye\corpora' `
  --output-dir '.research-output\r-phys1'
```

The generated `r-phys1-analysis.json` retains exact folder filenames, per-build roots, every file path under each vehicle directory, XML field observations, and all cross-build comparisons. `r-phys1-config-schema.json` contains the structured 6,081-row vehicle schema. These machine-readable outputs and proprietary inputs are ignored or external; neither is committed.

## Retail counts

Retail `vehicles.xml` contains **35 named vehicle families**, **6,081 vehicle-specific values**, and a separate `Tyres` root with 348 values. Exact top-level `DataGx/Vehicles` inventory contains **26 directories**. Seventeen config families match a model folder byte-for-byte by name, eight differ only in letter case, and ten have no exact/case-insensitive directory match (seven exact config-only names plus three lexical alias leads). `forklift` is the one extra retail model folder with no same-named vehicle config family.

| Retail config family | Folder classification | Exact folder or case-only folder |
|---|---|---|
| `Astero` | exact | `Astero` |
| `Bowler` | config-only | — |
| `Bruno` | exact | `Bruno` |
| `Cherokee` | config-only | — |
| `Chevyblazer` | case-only | `ChevyBlazer` |
| `Citroen` | config-only | — |
| `Custom` | config-only | — |
| `Forester` | exact | `Forester` |
| `Frontera` | exact | `Frontera` |
| `Icecream` | case-only | `IceCream` |
| `Jump` | exact | `Jump` |
| `Kamaz` | exact | `Kamaz` |
| `Kangoo` | exact | `Kangoo` |
| `Kiasportage` | case-only | `KiaSportage` |
| `Landcruiser` | case-only | `LandCruiser` |
| `Mattserati` | exact | `Mattserati` |
| `Megane` | case-only | `megane` |
| `Megane2` | possible alias lead | `megane` (unproven) |
| `Mercedes` | config-only in retail | — |
| `Navara` | exact | `Navara` |
| `Navarabig` | possible alias lead | `Navara` (unproven) |
| `Newrav` | case-only | `NewRav` |
| `Pajero` | exact | `Pajero` |
| `Pajerostripe` | possible alias lead | `Pajero` (unproven) |
| `Patrol` | exact | `Patrol` |
| `Rmonster` | case-only | `RMonster` |
| `SeatBuggy` | exact | `SeatBuggy` |
| `Simmbugghini` | exact | `Simmbugghini` |
| `Tata` | exact | `Tata` |
| `Terios` | config-only | — |
| `Terrano` | exact | `Terrano` |
| `Trooper` | config-only in retail | — |
| `Ufo` | exact | `Ufo` |
| `Wildcat` | case-only | `WildCat` |
| `Xtrail` | exact | `Xtrail` |

The eight case-only rows are not classified as missing assets. Conversely, the three “possible alias” rows are only lexical search leads; no alias relationship was established. In particular, `Newrav` is a config spelling and `Rav4` is a separate 9.3.1 model directory; the scanner does not merge them.

## Retail model folder resource presence

All 26 retail directories contain top-level `car.dx` and `complete.dx`. Twenty-five also contain `wheel.dx`; `Ufo` is the sole folder without it. DXT counts and total file counts are:

| Exact folder | DXT | Files | `wheel.dx` |
|---|---:|---:|---|
| `Astero` | 33 | 39 | yes |
| `Bruno` | 34 | 40 | yes |
| `ChevyBlazer` | 45 | 51 | yes |
| `Forester` | 27 | 34 | yes |
| `forklift` | 16 | 22 | yes |
| `Frontera` | 31 | 37 | yes |
| `IceCream` | 75 | 81 | yes |
| `Jump` | 29 | 35 | yes |
| `Kamaz` | 110 | 116 | yes |
| `Kangoo` | 31 | 37 | yes |
| `KiaSportage` | 64 | 70 | yes |
| `LandCruiser` | 34 | 40 | yes |
| `Mattserati` | 29 | 36 | yes |
| `megane` | 40 | 48 | yes |
| `Navara` | 95 | 101 | yes |
| `NewRav` | 34 | 40 | yes |
| `Pajero` | 41 | 47 | yes |
| `Patrol` | 33 | 39 | yes |
| `RMonster` | 37 | 44 | yes |
| `SeatBuggy` | 37 | 43 | yes |
| `Simmbugghini` | 31 | 38 | yes |
| `Tata` | 94 | 100 | yes |
| `Terrano` | 32 | 38 | yes |
| `Ufo` | 17 | 21 | no |
| `WildCat` | 31 | 37 | yes |
| `Xtrail` | 63 | 69 | yes |

Folders also contain local TXT sidecars and some vehicle-specific extras; their exact relative filenames are preserved in the generated JSON. Counts do not assert that every texture or sidecar is loaded at runtime.

## Config-only families and demo corpus cross-check

“No matching directory” below means no exact or case-insensitive same-name retail folder. Demo folder matches include `*Alpha` companion directories but remain inventory observations, not playability proof.

| Retail family | Retail classification | 8.4.1 | 9.3.1 | 9.10.0 |
|---|---|---|---|---|
| `Bowler` | exact config-only | none | config only | config only |
| `Cherokee` | exact config-only | config only | none | config only |
| `Citroen` | exact config-only | config only | config only | config only |
| `Custom` | exact config-only | none | config only | config only |
| `Megane2` | possible `megane` lead | none | none | `Megane2` config; no model directory |
| `Mercedes` | exact config-only in retail | `Mercedes`, `MercedesAlpha` | config only | config only |
| `Navarabig` | possible `Navara` lead | none | none | `Navarabig` config; no model directory |
| `Pajerostripe` | possible `Pajero` lead | none | `Pajerostripe` config; no model directory | same |
| `Terios` | exact config-only | none | none | config only |
| `Trooper` | exact config-only in retail | `Trooper`, `TrooperAlpha` | `Trooper`, `TrooperAlpha` | config only |

The exact demo top-level model-directory inventories are:

- **8.4.1:** `Copy of Mercedes`, `Copy of MercedesAlpha`, `Jump`, `JumpAlpha`, `LandCruiser`, `LandCruiserAlpha`, `megane`, `MeganeAlpha`, `Mercedes`, `MercedesAlpha`, `Trooper`, `TrooperAlpha`, `WildCat`, `WildcatAlpha`.
- **9.3.1:** `Forester`, `ForesterAlpha`, `Jump`, `JumpAlpha`, `NewRav`, `newRavAlpha`, `Rav4`, `rav4Alpha`, `Tata`, `Trooper`, `TrooperAlpha`, `Wildcat`, `WildcatAlpha`.
- **9.10.0:** `Jump`, `KiaSportage`, `megane`, `Navara`, `Simmbugghini`, `Wildcat`.

Thus Trooper has config and model assets in the two earlier demos but only config in 9.10.0 and retail. Mercedes has demo 8.4.1 assets but no exact retail folder. No same-named model folder was found for the other seven config-only/alias families in the corresponding demo inventories. `Teranno` in a 9.3.1 config is not silently equated to `Terios`.

## Provenance and limits

The scanner records SHA-256 and byte size for each source `vehicles.xml` and executable. The retail `vehicles.xml` used here is 757,388 bytes, SHA-256 `a6762bb20999c7224c71b9f5d1d7edca55bcea147ff9f973300a8cf8d350aee0`; its EXE is 3,121,214 bytes, SHA-256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. All external corpora were treated as read-only. This report makes no claim about slot selection, scene registration, physics use, or whether a folder is active in a game mode.
