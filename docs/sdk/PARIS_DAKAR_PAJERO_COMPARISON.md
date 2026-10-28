# Paris-Dakar Pajeros and Master Rallye historical evidence

29 October 2026. This comparison concerns original source assets and retained
owner-local references. It does not identify a recovered Paris-Dakar model as
an original Master Rallye model, and does not assign V60/V20 identities from
the `RED` and `Silver` filenames.

## Evidence available locally

The retained image folder is `C:/Users/MaRZ/Pictures/Master Rallye`.
The following actual files were opened and visually inspected. Original
publication URLs, capture executable hashes, camera projection and capture
dates are **UNKNOWN**. Their association with early Master Rallye material is
historical research context, not independently established build provenance.

| File | Dimensions | Bytes | SHA256 | Visible observation |
|---|---:|---:|---|---|
| `m_rallye_05.jpg` | 1024x768 | 85400 | `4ff4e0cc81e8c73d7e6ec6b98b9e8f2ef390aeb600b1965494a076c1fa93c0bc` | Red/yellow/black number203 short SUV; rectangular frontal lamps/grille, angular arch flares, short rear cabin, upright windshield. |
| `m_rallye_07.jpg` | 1024x768 | 91034 | `5d36a53e59df336334ae9d765abc6baaf2cf40278843669932e16b0d44dff47f` | Rear of red short SUV; central external spare, near-vertical rear door, corner rear lamps. |
| `mr4_paj.jpg` | 800x588 | 44060 | `a8e59120142b756e4045dc679a3a4789f64532f247ba26e41ea39130f20b5ea9` | White/silver frontal SUV; circular lamps within rectangular housings, low wide bumper intake, upright cabin. Filename is a lead, not a catalog record. |
| `mr_1m.jpg` | 200x150 | 7158 | `bc1140329a6e388991fb1ff6db9757e280917e8d59161b25575b325c516418d8` | QUICK VEHICLE SELECT thumbnail; white/red PIAA short SUV, flared arches, frontal auxiliary equipment. Low resolution limits identification. |
| `Pajero.png` | 698x421 | 335426 | `c34dca53e25db1e2fd2d7e4a8a1f26eb561714462a555445228b8dff02c9127b` | Yellow number203 MR presentation reference; auxiliary roof-of-grille lights, hood vent, rounded frontal treatment. This is an appearance control, not authenticated prerelease evidence. |

The silver/teal number263 SUV in `mr7.jpg` is a separate visual subject;
`m_rallye_08.jpg` contains a partly occluded silver/red SUV. Neither is silently
assigned to a Paris-Dakar Pajero. Both have been inspected and hashed in the
private reference manifest.

`C:/Users/MaRZ/Downloads/contact_carsheets.png` was also inspected. Its
number022 white/red PIAA card is supported by original game bytes, rather
than solely by an old contact-sheet label:

| Original relative to the named corpus root | Bytes | SHA256 |
|---|---:|---|
| `retail/Data.sma_unpacked/DataGx/Frontend/VehicleSelect/carsheet_022_000.dxt` | 65556 | `5f0b86fced06d8600d121097a18165c6919e4ac84dd234ac79592d371a5e445a` |
| `demo-9.10.0/DataGx/Frontend/VehicleSelect/carsheet_022_000.dxt` | 65556 | `5f0b86fced06d8600d121097a18165c6919e4ac84dd234ac79592d371a5e445a` |
| `retail/Data.sma_unpacked/DataGx/Frontend/VehicleSelect/carsheet_010_000.dxt` | 65556 | `41a1c17b165e427820d4fd47e00efc2d88f48eef229b58d3ea8d04191e5ad8a1` |

Corpus root: `D:/Game/Master Rallye/corpora`. These are observed128x128
BGRA-wrapper images decoded with the existing MR DXT reader. Icon022 survives
byte-identically in the two named local corpora. It resembles the PIAA vehicle
in `mr_1m.jpg`; a screenshot/icon resemblance does not recover its 3D mesh.
Retail `DataScene/FrontendScreens/VehicleSelect.xml` explicitly selects
image-bank10 for `T1_Car2` (lines1186-1202), not22. This is a static menu
declaration, not a new runtime roster experiment.

Private paths, sizes, hashes, MR model measurements and decoded reference PNGs
are in `.research-output/vehicles/paris-dakar-source/historical-references/`.
`references.json` binds the original reference files. Proprietary images and
models remain outside source-only review archives.

## Available MR geometry is a retail control

The actual retail `DataGx/Vehicles/Pajero` family was parsed read-only with the
existing native DX reader:

| Original | Bytes | Vertices | Stored triangles | SHA256 |
|---|---:|---:|---:|---|
| `car.dx` | 150367 | 2852 | 2193 | `9d051539ce10ba650840bba6c50b2c8ba9f68b6960661280f69680f0bb7f2c90` |
| `complete.dx` | 156487 | 2980 | 2607 | `0a52e1956b7105619b91f9bf7e08eacf443da06e3aed798336a8e04cb6daa3ab` |
| `wheel.dx` | 12988 | 220 | 252 | `31db2076dcfbdb85714f650712d4e5f2e4efb6cc8b72b695a14588387142f877` |

Retail `car.dx` stored-position bounds are
`(-1.018280387,-0.181922123,-2.394944429)` to
`(1.018280268,1.434110403,1.918310165)`. Its full stored extent is
approximately `2.03656 x1.61603 x4.31325` in MR model coordinates. It contains
crew and other components, so this extent is not a body-only factory
dimension. Frontend `complete.dx` uses a different vertical assembly origin;
an untranslated height comparison would be misleading.

No independently identified MR mesh for the white/red icon022 vehicle or the
red rectangular-front historical vehicle was located in the bounded inspected
retail family and local demo vehicle filenames. The26 retail vehicle
directories contain `Pajero`, but no separate `Pajerostripe` family. This is a
bounded inventory result, not proof that no historical build ever contained
another mesh.

The legacy labels `licensed_red`, `fictional_blue`, `final_yellow`,
`preview_hybrid` and `promo_pswheel64` are explicitly
**LEGACY_HEURISTIC** in
`research/legacy/asset-archeology/pajero-profiles.md`. They do not establish
chronology or asset ancestry. Older Downloads audit reports based only on TXT
texture references are not promoted over the current DX/TXT research.

## Decoded Paris-Dakar comparison

The original decoded source meshes, not image-traced geometry, now provide a
reproducible comparison target. The final neutral D3D9 source captures at
`.research-output/vehicles/paris-dakar-source/validated/PajeroRED/views-normalized/`
and the corresponding `PajeroSilver/views-normalized/` were inspected in front,
rear, left and three-quarter views. These captures use the qualified CW
culling choice. Earlier diagnostic captures with culling disabled showed internal
surfaces through exterior panels and are excluded from the historical
comparison: their black RED bumper and apparent rear side windows were
rendering artifacts, not original exterior appearance. These are static
source reconstructions; original Paris-Dakar renderer parity is not claimed.

| Observed feature | Paris-Dakar reconstructed source | MR historical reference | Interpretation |
|---|---|---|---|
| Short broad rally-raid SUV body, pronounced arches, upright cabin | Present in both decoded Pajeros. | Present in red `m_rallye_05.jpg`, white `mr4_paj.jpg` and PIAA thumbnail. | Vehicle-family similarity; not unique asset evidence. |
| Round frontal lamps in rectangular housings; wide central lower intake; paired small circular bumper openings | Distinctive frontal combination visible in **Silver**. | Similar combination visible in `mr4_paj.jpg`. | **Strong visual relationship**, with unknown source/build attribution and perspective limits. |
| Front lamp and bumper shape | RED has broad headlamp housings and a red bumper with central and side dark intake details; Silver has its separate front treatment. | Red `m_rallye_05.jpg` has narrower upright corner lamp surfaces, a red bumper with different intake treatment, and a different grille treatment. | A red livery does not establish identical model identity. The earlier diagnostic black bumper is not a source-asset difference. |
| Hood and roof | Both PD reconstructions show vented hoods and conspicuous rear roof-edge fins. | Historical red screenshot has a simpler hood treatment; matching roof fins are not clearly visible in these references. | Differences must remain recorded; absence in an occluded view is not proof of absent geometry. |
| Rear spare | PD RED's reconstructed rear has a decorated rear panel without an external central spare. | Red `m_rallye_07.jpg` visibly carries a central external spare. | Important equipment difference; cannot call these identical complete assemblies. |
| Livery and numbers | RED shows PlayStation/Mitsubishi/number256; Silver has its own Mitsubishi/number271 graphics. | MR red uses number203 with MR artwork; PIAA thumbnail uses a separate white/red graphic scheme. | Distinct game artwork. Common manufacturer/sponsor motifs are insufficient lineage evidence. |
| Retail yellow MR control | PD source geometry is not replaced by this asset. | `Pajero.png` has raised auxiliary lamps above grille, different hood/bumper treatment and yellow203 artwork. | The accepted MR retail family is a separate comparison control. |

The two Paris-Dakar `MainBody` records are also structurally distinct:
RED contributes1376 body triangles, Silver1446. The source adapter's
material-separated UVS representation has2586 and2619 body vertices,
respectively; these counts include material splits and must not be compared
as an identity hash against MR's native vertex storage. RED/Silver are
separate original body meshes, not merely two decoded colorways.

Both original Description records give a front-to-rear suspension-attach
separation of2.52778 source units. The neutral assembly bounds are
approximately `2.14524 x1.68126 x4.09441` (RED) and
`2.07965 x1.73084 x4.09442` (Silver). These are static reconstruction bounds,
not factory dimensions or a recovered gravity-settled pose. MR retail full
race stored geometry is approximately0.21884 longer in its own coordinate
units; unlike components and unqualified physical unit equivalence prevent
interpreting that difference as a real-vehicle dimension delta. No hidden
scale factor, body repositioning or image-derived wheelbase was applied.

A bounded exact texture check compared all56 original decoded image resources
per Paris-Dakar vehicle against all41 MR retail Pajero DXT textures. It
required equal dimensions and exact RGB bytes, tried both MR stored and
vertically flipped row order, excluded the derived neutral-white preview
texture, and did not infer alpha semantics. **No complete-image RGB match**
was found. Different palette quantization, cropping, resizing or authored
edits could still conceal a common ancestor; this check neither proves nor
disproves ancestral reuse. The private result is
`historical-references/exact-rgb-comparison.json` beneath the phase output.

## Interpretation categories and present boundary

| Category | Required evidence | Current conclusion |
|---|---|---|
| **Exact asset relationship** | Comparable original geometry and a reproducible correspondence of vertices/topology/UVs or other uniquely identifying source data; transformations and exclusions explained. | **UNRESOLVED.** No independently identified missing MR Pajero geometry is available for this comparison. Different filenames, counts or containers cannot settle ancestry. |
| **Strong visual relationship** | Multiple distinctive matching visible features across source reconstruction and reference views, with differences documented. | **Silver versus `mr4_paj.jpg`: strong visible frontal design relationship.** The historical capture build is unqualified; this is not an exact geometry, game-asset or development-pipeline match. |
| **Plausible inspiration** | Shared vehicle-family/design cues without distinctive asset correspondence. | Both titles' short rally-raid SUV subject matter supports a research hypothesis, not a creator/source pipeline claim. |
| **Unresolved** | Missing mesh, missing build provenance, ambiguous identity or insufficient comparable views. | Exact MR lineage, V60/V20 mapping, factory dimensions and prerelease build attribution remain **UNRESOLVED**. |

Wheelbase cannot be measured reliably from perspective screenshots with
unknown projection and suspension state. Texture lettering and broad livery
colors can support visual observations, but shared sponsor logos or a common
real vehicle do not prove common textures. No public image was downloaded or
substituted for the owner's originals. No historical file was modified.

The next lineage experiment is a separately reviewed recovery of an
authenticated original MR mesh matching icon022 or the red historical
screenshots, followed by coordinate-normalized topology/UV comparison. It is
not an invitation to manufacture an MR model from these images or start a
native donor import.
