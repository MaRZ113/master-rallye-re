# Controlled foliage cases

All counts below refer to **authored visual source mesh records**, with ADC-suppressed and degenerate triples excluded by the existing WATER1 reader. Source-index, welded-vertex and shared-edge components are distinct grouping conventions. No component count is promoted to a live plant count.

The exact decoded PSM hashes, PackFS provenance, source strip ranges, flags, offsets, normals/UV/color summaries and PC draw identities are retained in `foliage-material-matrix.json`.

| Case | Course/node byte offset | Shader | Source strips | Faces | Referenced source vertices | Shared-edge components |
|---|---|---|---|---|---|---|
| A | TURKEY3 /3620664 | treeblend | 14 | 256 | 384 | 16 |
| B | ITALY_S1 /3706566 | tree | 5 | 64 | 120 | 4 |
| C | FRANCE1 /3550808 | tree | 4 | 80 | 120 | 10 |
| D | TURKEY3 /3429766 | object | 13 | 139 | 245 | 12 |
| E | FRANCE1 /3509209 | treeblend | 2 | 24 | 36 | 2 |

## A — Turkey3 TURshrub2

Resource `\TNG\DATAPSM\COURSE\TURKEY3\TURKEY3.PSM`, decoded SHA-256 `dd274ac1cb56c16d35410fbe2e8e3771a750b47710b747fddc70604fdb3d59fc`.

Tag2 path `root.0.63.11`, material offset3620723:

```text
TURshrub2 $alphatest() $shader(treeblend)
```

Primary name at3620686: `Course\turkey3\shrubtrig2-tga`. The 14 source strips produce256 nonsuppressed/nondegenerate triangles;100 consecutive triples are ADC-suppressed. Sixteen shared-edge components have16 faces each. This remains a group of authored geometry, not sixteen independently owned shrubs.

Source bounds, XYZ: `[1769.264160,30.159233,-78.139091]` to `[1877.363525,57.838039,30.376247]`. Source RGBA words include f4f4f4ff on320 referenced vertices and211a00ff on64; VU-derived integer colors are respectively(122,122,122,127) and(16,13,1,127).

The material reaches mode2, bucket1, source-alpha blending, alpha-test-disabled and ZMSK=1. It uses original authored strip positions and the original primary texture name. No distance alpha weight or plant-generated primitive is found.

GEOM1's strict/baseline/relaxed comparisons retain256 unmatched source candidates in the paired PC compiled landscape. No paired same-texture-family draw is identified, and the explicit paired shrubtrig2 DXT path is absent. This strengthens the bounded source delta; it does not establish a whole-game absence, sixteen missing PC instances or an implementation-ready placement plan.

## B — ItalyS1 pinus2

Resource `\TNG\DATAPSM\COURSE\ITALY_S1\ITALY_S1.PSM`, SHA-256 `f74854a0789c1d3bb416cef8d70a02c65141a2d7afc5a150068c047b94bc30a0`.

Tag2 path `root.0.32.5`, material offset3706622:

```text
bush $alphatest() $shader(tree) $mip(1.0) $clamp(v)
```

Primary `Course\Italy_S1\pinus2-tga` at3706588. Five strips produce64 faces, excluding46 ADC triples. Four whole shared-edge components have9/38/16/1 faces; vertex welding and source-index grouping yield different component totals. None identifies four independent trees.

Bounds: `[-1219.896851,-43.444035,-74.782951]` to `[-926.994446,26.185669,219.225037]`. NormalY is close to zero in these upright authored surfaces, while primary U spans−1..1.372977 and V≈0.002..0.998. UVs are consumed as authored rather than rewritten to a newly generated quad.

The callback reaches mode6, bucket0, alpha>64/KEEP, ABE=0 and ZMSK=0. Normals are cached but not used by selector0's position/color computation. PC has28 same-texture-family draw records, but the selected PS2 group has no exact world-coordinate face correspondence at the declared profiles. Equal pinus2 pixels do not resolve placement/instance ownership.

## C — France1 pinetree

France1 landscape decoded SHA-256 `d0b9845218ddd1ff4f12b3b16e77eff43aa182ac73992b5cbea8d81be04f935d`.

Tag2 at3550808, material at3550865:

```text
pinetree $alphatest() $clamp(v) $shader(tree)
```

Four strips,80 source faces,32 ADC exclusions,120 referenced vertices; ten shared-edge components of8 faces each. Bounds: `[-2473.776855,38.972424,-406.902008]` to `[-2268.027832,112.243393,-247.483963]`.

The matched PC source is draw283, tag2/core offset3281947, feature mask3, flags1/1/1/1. There are43 same-family PC draw records in the examined course, not43 proved trees. Draw283 has320 triangle records: **80 exact unsigned triangles repeated four times, all with both windings present**. Duplicate topology must not be counted as additional plants.

| Profile | Exact PS2 triangles | Other GEOM1 relations |
|---|---|---|
| strict | 62/80 | 6 equivalent surfaces,9 partial,3 modified diagnostics |
| baseline,0.001 | 62/80 | 10 equivalent surfaces,8 partial |
| relaxed,0.01 | 80/80 | All exact under that declared tolerance |

Source normals/UV ranges are compatible across the selected source families; per-vertex colors are not assumed identical because the PC draw has redundant vertices and triangles. Both files have stored A=255 for the selected vertex colors. Pinetree texture pixels are identical after the explicit PC stored-row conversion. This provides a useful shared asset/control, with float-coordinate residuals and redundancy preserved.

## D — Opaque hut control

Turkey3 tag2 at3429766, material at3429821:

```text
rustic Hut $clamp(uv) $shader(object)
```

The selected source subset has139 faces and uses `hut_01-tga`. Its PS2 texture is64×64 with constant stored alpha255. Mode15 shares source geometry/cache/texture machinery but has ATE=0,ABE=0,ZMSK=0. Therefore foliage alpha/depth differences cannot be attributed to every ordinary landscape draw.

The current whole-group world-coordinate matcher does not establish a paired PC draw for this leaf. DRESSING1's stronger hut subpart/reuse findings remain unchanged; absence of a whole-leaf exact match does not erase them. PC's opaque hut DXT has stored alpha0; that illustrates why file alpha alone does not prove transparency.

## E — France1 bush01, second treeblend course

Tag2 path `root.0.1.16` at3509209, material at3509264:

```text
bush $alphatest() $clamp(uv) $shader(treeblend)
```

Two strips,24 faces,8 ADC exclusions,36 referenced vertices and two shared-edge components of12 faces. Bounds: `[-951.277283,44.521038,452.819061]` to `[-945.412659,48.445168,462.138489]`.

**24/24 exact unsigned matches at all three profiles**, to PC draw54/core3261170. The PC draw has48 triangles but24 unsigned unique triangles, each represented in both windings. Its sidecar material is `bush $alphatest() $clamp(uv) $shader(tree)`, compiled flags1/1/1/1 and feature mask3.

This is the strongest controlled material delta: shared geometric surfaces, PS2 treeblend versus PC tree/alpha-test candidate. It also has an independent image delta, PS2 BUSH01 64×64/89 alpha values versus PC128×128/15. Selected PS2 vertex tints and PC BGRA tints differ slightly; their respective histograms are recorded. An exact vertex-attribute pairing across redundant PC vertices is not asserted.

Mode2 semantics generalize beyond Turkey3. The result is not a foliage-instance count and does not prove live pixel parity, global sorting or an LOD crossfade.
