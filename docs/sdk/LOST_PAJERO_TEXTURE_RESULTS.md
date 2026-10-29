# Lost Pajero — original MR texture forensics and livery experiment

29 October 2026. Baseline `483f03d78c03f74841a123c944028938426115bb`, initially clean `research/vehicles`. Complete owner Master Plan v7.5 retained verbatim; the repository's additional v7.4 implementation checkpoint is separately preserved, not discarded because it was absent from the new attachment. Historical plans are context; current authorization is texture forensics and neutral preview only.

## Finding

**Original red Pajero model textures genuinely survive in clean retail Data.sma.** They are not merely frontend pictures or recolored Xbox artwork. The preserved `Pajero.txt` identifies their old material names. However, five key red/art resources are **TXT-only**: the currently parsed `car.dx`, `complete.dx` and `wheel.dx` do not reference them. The TXT contains material references and mesh names/counts, but no original UV arrays from which to recover that earlier red model.

Whole-image MR → Xbox texture replacement is **UNSUPPORTED: no verified cross-atlas UV correspondence**. The private C experiment transfers only authentic MR number203 artwork into authored atlas rectangles. It preserves geometry and UVs, but has a visible opposite-side legibility defect and retains the Xbox livery elsewhere. **C is not a successful full red-livery restoration or a justified native import.** An accurate limitation is the milestone result.

## Exact original sources and ownership

Qualified retail archive: `D:/Game/Master Rallye/corpora/retail/Data.sma`, SHA256 `03c2b52d451b378c7ec634132ebfab706616e33c57fea2985b83db66d3fd4b2f`. Family: `DataGx/Vehicles/Pajero/`. All **47 family files** were compared byte-for-byte with the original archive through the existing read-only SMA compatibility reader. No archive was rewritten or treated as a modded loose installation.

[LOST_PAJERO_TEXTURE_INVENTORY.json](LOST_PAJERO_TEXTURE_INVENTORY.json) records exact absolute paths, archive member names, sizes, SHA256, DXT dimensions/header words/alpha range, each native DX draw/slot/flags/UV hash/bounds, TXT material ownership and demo boundaries. It contains metadata only, no texture pixels or geometry arrays.

41 DXT images: **33 referenced by at least one parsed DX**, **6 TXT-only**, **2 unreferenced within the three DX / three TXT family files**. A structural DX reference does not prove that runtime switches selected that surface. “Unreferenced” is bounded to this inspected family, not every executable path in the game.

| Original filename | Dimensions | SHA256 | Ownership / actual content |
|---|---|---|---|
| pdoor128-tga.dxt | 128×128 | 351f8f89dcfffee243cd5b67e4f3251fcdd3b864c3b90a3bb5ce59eb19368440 | Pajero.txt material12 PDoor128; red door/window panel, yellow/black band, Mitsubishi graphics; TXT-only |
| pajeror128-tga.dxt | 128×128 | 3986c4d1e29d05a940c3c9f7bd5e86c566988416c4d22ed7b3cf448ac37e29a1 | Material10 PajeroR128; red rear door, yellow band, MR emblem, spare-shaped shading/outline and grille art; TXT-only |
| pfront-tga.dxt | 64×64 | f4b1f8c6716d178a840f5375972d4c3a8cd7e06e2ef93b89eba25f9fb50ceb3c | Material7 PFront; red front/bumper fragment; TXT-only |
| pfrontgb-tga.dxt | 64×64 | f4b0d86c5c3c1abc8e9e95f4fd89251d3322e5440f1e73c8f63c1bd34946f1e7 | Material8 PFrontG; red front opening/paint; TXT-only |
| mastersticker-tga.dxt | 64×64 | e56a2a39e1f799ec86bb78cb3f701b4910bc06f0d1c211cf209b25aa20dfac45 | Material9 Sticker; genuine MR logo + number203; TXT-only, distinct from active mastersticker203 |

The sixth TXT-only image is `pfrontgbblue-tga.dxt`, 128×128, associated with the older frontend TXT. `bonblue-tga.dxt` and `pathe-tga.dxt` are the two apparently unreferenced family images; neither is evidence for a lost red atlas merely because it is unused. `plight64-tga.dxt` contains red-background lamp fragments and is DX-referenced; its ownership is lamp material, not a whole red body. Shared chrome, rubber, glass, crew, tyres and glow textures are recorded separately.

Native resources remain the existing retail geometry: car.dx 2852 vertices / 2193 stored draw triangles, complete.dx 2980 / 2607, wheel.dx 220 / 252. Race and frontend have different draw/material selections. Active bindings include yellow/blue paint alternatives and `mastersticker203`; no native red variant is inferred from the presence of its older TXT.

Available demo-8.4.1, demo-9.3.1 and demo-9.10.0 extractions contain **no Pajero family or named pdoor128/pajeror128/pfrontgb inputs** in the inspected vehicle trees. Exact demo executable hashes are retained in the inventory. This does not establish what every original demo disc contained. Frontend `carsheet_010_000.dxt` / `carsheet_022_000.dxt` records are classified separately as artwork, not mesh textures; six available retail/demo images are listed. Icon022 does not supply UVs or a recovered lost mesh.

## Historical correspondence

Owner-local originals: `C:/Users/MaRZ/Pictures/Master Rallye/m_rallye_05.jpg` and `m_rallye_07.jpg`. Original hashes and dimensions are retained privately in `.research-output/vehicles/lost-pajero-livery/historical-evidence/references.json`; prior reference hashes remain in PARIS_DAKAR_PAJERO_COMPARISON.md. Capture executable, camera and authenticated build provenance remain UNKNOWN. Private contact sheets place actual original MR texture pixels beside the references; no repainting or generated decals.

| Association class | Result |
|---|---|
| Verified original source association | All listed textures belong to the original retail Pajero archive family; old TXT material names/IDs are verified. This is source ownership, not proof of a particular prerelease frame |
| Visually matching artwork | Red base, horizontal yellow/black band and original number203/MR badge correspond to visible elements of the red promotional subject |
| Partial correspondence | Rear red/yellow treatment and MR emblem resemble the rear reference; door/window artwork contains Mitsubishi identity. Perspective, low resolution and differing panel geometry prevent pixel/UV identity claims |
| Unrelated or unresolved | Yellow/blue sponsor atlases, lamp/glass/shared textures and UI art have separate ownership. Historical white-bar stripe details and complete sponsor arrangement are not recovered as a complete verified red sheet. Exact build chronology, original red mesh, source asset ancestry and which older materials were active remain unresolved |

The spare-shaped texture shading is **not geometry**. No rear spare, new equipment, changed lights or altered body proportions were generated. Xbox Pajero remains a different donor model; this evidence does not identify it as the lost MR mesh.

## UV compatibility

Retail DX has one parsed UV set. Its UV0 is bound to per-draw local textures and reflection stages; exact draw IDs, slot ownership and UV hashes/bounds are recorded. The old red TXT contains no UV positions or triangles, so its named material association cannot reconstruct an exact old red UV layout. Current MR UV overlays are controls, not proof that every older red image fits current geometry.

Xbox uses separate body atlases `xtx-043` and `xtx-046` (256×256), plus other material textures; original UV0, UV1 streams, colors, blend/depth/culling research and compressed images remain untouched. Atlas046 combines opposed side islands, interiors, lamps and decals; MR uses separate 128² door/rear and 64² front/badge resources. Red/black/yellow colors and normalized 0..1 UV bounds do not imply compatible islands. The same atlas also serves other nodes, so global texture replacement would contaminate equipment/interior/transparent surfaces.

Private `review-ready/uv-compatibility.json` lists all 56 Xbox meshes, UV0 hashes/bounds, original UV1/color-stream provenance and source render states. Original MR and Xbox UV0 overlays are under `review-ready/atlases/`. They expose seams, repeated/opposed islands and material ownership; UV1/secondary shader behavior remains unqualified and is not repurposed as a livery channel. No arbitrary 3D scaling, automatic nearest-surface transfer or texture-library swap.

## Controlled experiments

| Variant | Status / exact action |
|---|---|
| A — Xbox Original | PASS conservation baseline. Stage the immutable v7.4 source scene with original geometry, textures, UVs, colors and render states |
| B — Direct MR Texture Test | UNSUPPORTED, not generated. No original MR atlas has verified direct cross-game UV correspondence. A distorted whole-atlas swap would not qualify a direct test |
| C — UV-adapted MR livery probe | **WARN, PARTIAL BADGE ONLY.** Copy the original MR203 badge into two explicit 30×30 pixel rectangles of a derived atlas046, only for material `node-000-sub-01`. It is authored 2D atlas correspondence, not direct mapping or a full livery |

C uses uniform nearest-sample downscaling of original artwork, explicit stored-row/orientation operations and original Xbox alpha everywhere. The 1800 allowed RGB pixels are exactly the 1800 changed pixels. No source UV is edited. Existing source textures remain present and byte-identical; one additional derived RGBA image is private. Only one opaque body material's diffuse reference changes. Original raw material/stage fields remain provenance; the preview replacement is explicitly tagged as derived.

Coverage raster diagnostic identifies 27 triangles intersecting the patch among 4154 original triangles. This measures atlas raster samples, not percent of visible body area. Both side captures retain incorrect badge orientation/legibility after the explicit opposed-island trial. Final image inspection supersedes the earlier provisional left-side readability description. That visible failure is preserved. No claim is made that the entire second patch maps faithfully to the intended external panel; facing/occlusion and island correspondence still need a reviewed manual UV selection. The experiment is therefore unsuitable as a finished livery.

Other panels retain Xbox sponsor markings/paint and roof/hood numbers; window contours, lamps, wheel geometry, equipment and rear shape still differ from MR references. Glass and intact transparency are unchanged; no damaged-glass controller or material reinterpretation is introduced. Full Xbox shader/alpha-test/UV1/reflection/runtime parity stays **L2 WARN**.

Private delivery: `.research-output/vehicles/lost-pajero-livery/review-ready/`. A/C each have front/rear/left/right/top/isometric D3D9 views, plus six labeled A/C sheets. C's `scene/scene.json` reopens in Source Garage with a WARN name and native Create disabled. Earlier orientation trials remain private diagnostics, not qualified outputs.

## Reversibility and validation

Versioned overlay history provides Apply, Undo, Redo, Restore and disk reopening. Source validation regenerated C identically, verified every original sidecar, mesh/UV/normal/node equality and alpha isolation, then checked that Undo/Restore stages an MRPV **byte-identical to A**. Redo returns the exact C scene hash. No accepted scene or Workshop project is overwritten. The helper is an isolated research overlay, not an MR-native project or a claim that the main MR Paint Studio's history owns it.

Eight new source-free tests cover synthetic clean-archive binding/drift rejection, TXT ownership, direct-UV gate, contained uniform patching, original alpha, explicit mirrored-island operations, invalid budgets/rectangles, history/reopen and rejection of unqualified source scenes. Focused suite: 78 PASS. Full Windows rerun: **1166 tests OK, two optional skips**, 63.836 seconds (`windows-regression-final.log`). An initial unrelated compiler directory rename failed once with WinError5; its isolated rerun and full rerun passed. This failure is retained in the private logs rather than hidden.

Protection baseline covers **11500 files**, including donor installations, original EXE/clean SMA/installed proxy, accepted MR projects and previous source scenes. The completed audit hashed **15448297600 bytes**, with **zero changed or missing files** (`preservation-validation.json`). No native candidate, CarID allocation, roster or Silver suspension change. Original/extracted/adapted textures and screenshots stay private; review archives contain source, tests and metadata only.

## Next decision and reproduction

**Native import is not justified by this experiment.** A convincing full red livery needs reviewed panel/island correspondence and likely manual Paint Studio / later Blender UV work. Missing stripe/sponsor elements must be located or explicitly left missing, not invented. Do not start Blender Bridge development during this milestone. A future separately approved candidate must be named **Dakar 2 Xbox Pajero — MR Prerelease-Inspired Livery**, unless stronger source evidence is found; it must not replace Silver or stock Pajero.

```powershell
python tools/lost_pajero_livery_lab.py --corpus "D:/Game/Master Rallye/corpora" --source .research-output/vehicles/dakar2-fidelity/final/PAJERO/scene/scene.json --output .research-output/vehicles/lost-pajero-livery/owner-test --viewer .research-output/rally-workshop/bin/mr-vehicle-previewer.exe --references "C:/Users/MaRZ/Pictures/Master Rallye"
python tools/validate_lost_pajero_livery.py --source .research-output/vehicles/dakar2-fidelity/final/PAJERO/scene/scene.json --experiment .research-output/vehicles/lost-pajero-livery/owner-test --family "D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked/DataGx/Vehicles/Pajero" --output .research-output/vehicles/lost-pajero-livery/owner-validation
```

Owner review: compare original red atlas/number against historical front/rear images; inspect both C side views (incorrect badge orientation on both sides); check glass/lamps/wheels remain unchanged; compare roof/hood/rear residual Xbox artwork; verify Restore matches A. Treat C as diagnostic, not acceptance of a playable restoration. Stop here for review. No push/publication.
