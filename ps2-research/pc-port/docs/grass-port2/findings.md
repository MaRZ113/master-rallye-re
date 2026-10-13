# Turkey3 second ground-decoration category

The original detail system has two generating categories: `grass` selects pool 1
and `PARTICLES/GRASS1.GXI`; `shrubs` selects pool 0 and `PARTICLES/BUSH1.GXI`.
The second category is a supported source-backed target for the requested second
vegetation layer. This is not a newly invented grass texture or a second random
scatter algorithm.

The supplied Turkey3 image shows upright tufts and shorter branching ground
details. Their resemblance to the two source images is
`SCREENSHOT_CORRELATION`. No captured PS2 packet ties an individual pictured
decoration to BUSH1. Large bushes beside buildings may instead be authored model
geometry; they are not included in this category merely by appearance.

The user reports the first PC grass layer appears along the track and the menu
and hidden-HUD stalls are gone (`USER_RUNTIME_OBSERVATION`). That confirms the
delivered first layer's usefulness, not exact PS2 placement or image parity.

## Fresh source and geometry checks

Canonical ELF/CNF/PAK/000 identity was verified through existing tooling, and
Turkey3/BUSH1 were freshly extracted by named PackFS lookup. The landscape hash
is `dd274ac1cb56c16d35410fbe2e8e3771a750b47710b747fddc70604fdb3d59fc`.
The PC compiled source is the protected retail `Turkey3/turkey3.dx`, hash
`724a69da708a124f7dbfd666b7ad8d391bcaf22ff94bd2c91143e305749cf7f8`.
All 420 ordered route anchors agree exactly without a fitted transform.

| Property | First grass category | Second shrub category |
|---|---:|---:|
| Spatial material IDs | 2, 5 | 3, 4 |
| Category-bound spatial triangles | 5,035 | 6,752 |
| Slope/category-eligible triangles | 2,912 | 3,835 |
| Strictly matched PC compiled triangles | 2,797 | 3,702 |
| Nonexact sources excluded from pilot | 115 | 133 |
| Matched PC draw records | 154 | 199 |
| Reconstructed whole-triangle points | 64,900 | 146,498 |
| Category lift | float32 0.33 | float32 0.4 |
| Texture | GRASS1, 32×32 | BUSH1, 32×32 |
| Distinct stored alpha values | 223 | 213 |

These are source/reconstruction counts, not simultaneously visible plant counts.
The larger shrub total comes from different eligible authored surfaces. The
traced generator does not select a separate shrub density factor.

Shrub material 3 at decoded byte offset **3811342** is
`$surfacetype(grass) $detail(shrubs) `; material 4 at **3811384** is
`$surfacetype(harddirt) $detail(shrubs) `. Material 3 produces 61,937 and material 4
84,561 points under the declared full-triangle activation reconstruction.

Turkey3 has no singular `$detail(shrub)` in the actual spatial table. The known
singular spelling belongs to **Turkey_S1**, not Turkey3. It remains an
unrecognized category and must not be normalized to plural shrubs.

## Reusable contract

Both categories share pitch `float32(1.33)`, original coordinate-hash jitter,
upward normalized-cross threshold `ny > float32(0.975)`, the snapped camera
region and radial fade. The main proved category differences are resource,
eligible material/surface ownership and lift/size. CPU sprite inputs multiply
the category lift by 3; the size ratio is approximately **0.4/0.33 = 1.212121**
with common renderer inputs. That ratio can preserve the existing PC preview
scale while giving the second category its original relative size. Exact PS2
projected scale still requires live renderer constants.

Fresh Rabbitizer 1.16.2 `InstrCategory.R5900` checked 46 compact original words
for pitch/lift, category selection and size writes. Byte/file mapping comes from
the canonical ELF PT_LOAD, not generic MIPS approximation. See
[instruction-probes.json](instruction-probes.json) and
[material-contract.md](material-contract.md).

Only the source contract and separate private asset are produced here. Native
mode, transaction and build validation belong to the parent implementation pass.
No original asset, renderer baseline, Course SDK or earlier phase was edited.
