# Mercedes source package manifest

## Selected source

| Field | Value |
|---|---|
| Build | `demo-8.4.1` |
| Folder | `DataGx/Vehicles/Copy of Mercedes` |
| Full local source | `D:\Game\Master Rallye\corpora\demo-8.4.1\DataGx\Vehicles\Copy of Mercedes` |
| Source tree inventory | 59 files: 3 GXM, 25 GXI, 25 DXT, 3 TXT, 3 legacy DX |
| Legacy DX revision | 127 for `complete.dx`, `car.dx`, and `wheel.dx` |
| Source tree verification | 59/59 file sizes and SHA-256 values match the prior machine inventory |

Per-file byte counts and hashes are in [mercedes-source-manifest.json](mercedes-source-manifest.json).
It contains metadata only; no asset bytes are copied into Git.

## Locked model source

| Role | GXM bytes | GXM SHA-256 | Legacy DX bytes | DX SHA-256 |
|---|---:|---|---:|---|
| `complete` | 231,795 | `95caced8716239d4fa093fc0320e737e13dc1eedc8b649456d4cc89444fe354d` | 122,138 | `000735aabd54dd6d6e3146ee981c5739616ad9169fbffe7bb9bbb3f461498c91` |
| `car` | 195,867 | `ff238b391da254ef10904bb59b7430d17e1000cfceec8821d61f98b7158993fe` | 112,501 | `989905468d528bb35dec7901b03a08367b37a1fa4f8a32143428a782253d0791` |
| `wheel` | 27,267 | `74bfb66a0b411cb3814bbc16f4c672bc9d42b5b7b7e7e7415686ba805ac517ea` | 12,932 | `9a331627ce44dc24ed9e3a3e4d92882e22b34cf4ef8fe561c1ee293e41d35661` |

All three GXM roles pass the bounded material-prefix/geometry-prefix parser
used by the prior source audit. Across them, the serialized material table
references 25 distinct GXI files plus the `Null` sentinel. The strings include
the absolute authoring root `D:/projects/MRallyeTNG/DataGx/Vehicles/Mercedes/`.
The paths are stored as length-prefixed strings in the parsed material table;
this finding alone does not authorize a generic GXM rewrite.

## Texture inputs and sidecars

The selected folder contains 25 GXI files and 25 existing DXT companions. All
25 GXM-referenced GXI names are present. The 3 sidecars point to 19 car, 25
complete, and 6 wheel texture references (overlapping roles; 25 unique GXI/DXT
stems across the package). Each existing DXT parses with the project's current
reader. The prior offline GXI→DXT encoder output matched all 25 existing DXT
files byte-for-byte; this is a source consistency check, not retail cooker
evidence.

## Variant audit

| Variant in demo-8.4.1 | Current evidence | Selection decision |
|---|---|---|
| `Mercedes` | Has all three DX/GXM roles, but its `car.dx`, `wheel.dx`, `car.gxm`, and `wheel.gxm` hashes match `LandCruiser`; material names also alias that package. Its `complete` differs. | Mixed/aliased, not the distinct source. |
| `MercedesAlpha` | Partial GXM/sidecar/GXI material; no full three-role DX/DXT model package. | Excluded. |
| `Copy of Mercedes` | Full 3-role GXM and legacy DX set, 3 sidecars, 25 GXI and 25 DXT; distinct Mercedes geometry. | **Selected.** |
| `Copy of MercedesAlpha` | Only `car.dx` and `wheel.dx`, both revision 125; no `complete.dx`. | Excluded. |
| Nested `lpha` folders | Duplicate/partial Alpha variants under the two Mercedes folders. | Excluded; not silently merged into selected root. |

The three selected DX files remain historical references only. The retail SDK
does not accept them as retail revision-135 full-DX outputs, and they are not
the preferred inputs for this phase.

## Retail identity lock

| Input | Bytes | SHA-256 |
|---|---:|---|
| Retail `MRallye.exe` | 3,121,214 | `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` |
| Retail `Data.sma` | 282,396,172 | `03c2b52d451b378c7ec634132ebfab706616e33c57fea2985b83db66d3fd4b2f` |

The corpora remained read-only. These identities are documented to reproduce
future tests, not to authorize editing either file.
