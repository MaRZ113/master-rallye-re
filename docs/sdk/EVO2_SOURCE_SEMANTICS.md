# Evo2 Toyota 4Runner — original source semantics

Date: 2026-10-28. Scope: `TRUCK/T4RSR52.TRK`, its original body/wheel SMFs,
and read-only static analysis of the supplied PC `4x42.exe`. The original game
was **not executed**. This document qualifies a static inspection assembly; it
does not establish original runtime rendering, suspension motion or MR gameplay.

## Exact build and source identity

| Input | Size / SHA-256 |
|---|---|
| `4x42.exe` | 2,776,064 / `ab8286e6bce8a1bf3769acddfeb0a79df2e5d43c72f462a89aa90f477951ec75` |
| `TRUCK.POD` | 144,691,121 / `5669509d709193621802a43c2c63b32e537fcf93ea3fd5d94af8c66947be6a41` |
| `TRUCK/T4RSR52.TRK` | POD offset141843246, size6674 / `d2ff6c5914e8102116e56704dac800442fed3adfbf42326c6b3311517e8bbcb4` |
| `MODELS/4RUNNERSR5.SMF` | POD offset126695862, size171308 / `a7f71e0ae1cae2fb64438ce8614bf7db47eb9dfc813d926388da4dfef7b6a11e` |

The original TRK declares version7, `Toyota 4Runner SR5 Sport Package 2WD`,
model year2000, body basename`4RunnerSR5`, wheel basename`4RunTire`, stock parts0
and nine source color records. No color or equipment was inferred from a filename.

REA successfully admitted this x86 PE and used Ghidra12.1.4 with completed default
analysis. Decompiled function names/signatures below are analyst locators, **not
original source code**. Relevant instruction text and raw byte windows were also
retained, and all eight sampled Ghidra byte windows exactly matched the original
PE file mappings. No binary/database metadata was changed.

## Axes and units from original asset labels

The source body frame is **X right, Y up, Z front**, with lengths in **feet**.
This conclusion uses the original TRK and anatomically named original SMF parts,
independently of the community Blender importer's axis conversion.

- `faxle.rtire.static_bpos=(+2.47,-0.6,+4.79)` and left tireX`-2.47`;
  rear rightX`+2.455`, rear leftX`-2.455`, both rearZ`-4.09`.
- TRK light records explicitly label body-axis position/bitmap radius`(ft)` and
  cone dimensions`(ft)`. Front lamps areZ`+6.86`, heading0, pitch`-0.174533`;
  rear lamps areZ`-7.201115`, heading`3.141593`.
- Original `MirrorL` occupiesX`[-3.00463,-2.29859]`; `MirrorR` occupies
  X`[2.29859,3.00463]`. `LightHL/HR` are at positiveZ; `LightRL/RR` negativeZ.
- Driver headY`+3.23` and upper rear lightY`+4.32952` are above tire centersY`-0.6`.

The implemented neutral preview contract uses X right, Y up, Z rear (front is
negative Z), matching the existing viewer's right-handed camera. Its derived
mapping is `(x,y,z)source → 0.3048*(x,y,-z)` metres. The basis change
has determinant`-1` before uniform scaling: it changes handedness. Transform
normals consistently and reverse each triangle's corner order for the reflected
basis; preserve the original face indices separately. This is an explicitly
derived normalization, not a claim the game stores canonical metres.

The completely consumed SMF records contain object names/flags/materials,
positions/normals/UVs and face indices; no separate per-object matrix record was
observed in these files. Body submeshes already share the labelled body frame.
Identity body-node transforms are therefore an inspection representation of
those stored coordinates, not recovered original matrix bytes. Wheel-node
translation matrices are derived from the separate original TRK records.

Original cross-product/vertex-normal checks on the high-detail body give1957
positive and10 negative triangle dot products; each16L/16R wheel gives227
positive and0 negative. Preserve the ten original body inconsistencies; this
evidence does not authorize per-face “repair”.

## Wheel detail variants and static placement

| Slot | Original left/right resources | Geometry per side | Source tyre outer radius |
|---|---|---|---|
| 0 | `4RUNTIRE08L/R.SMF` | Tire34 vertices/32 triangles | approximately1.27526ft |
| 1 | `4RUNTIRE12L/R.SMF` | Wheel25/36 + Tire85/108 | approximately1.27527ft |
| 2 | `4RUNTIRE16L/R.SMF` | Wheel33/51 + Tire129/176 | approximately1.27528ft |

**08/12/16 are detail variants, not rim diameters.** All have the same tyre bounds
X±0.434711, Y/Z±1.27526, with increasing polygon counts. Native TRK loader
`FUN_005ed4b0` checks the basename's`16l.smf` existence and formats all six names
into vehicle fields164c/166c/168c for08L/12L/16L and16ac/16cc/16ec for08R/12R/16R.
`FUN_005f6a40` loads all three slots; `FUN_005f6ec0` selects left/right model arrays
at170c/1718 using the current wheel-detail field12a0. The source supports an
explicit **slot2 high-detail inspection policy**; this does not prove the user's
original game graphics setting.

The original left rim lies at negative localX and the right rim at positive
localX. For16L it isX`[-0.352722,-0.287234]`;16R isX`[0.287234,0.352722]`.
Use the distinct original L/R meshes, normals and UVs. Do not generate one side
by mirroring the other or add an unexplained180-degree wheel rotation.

| Wheel | Literal source translation in feet | Static inspection orientation |
|---|---|---|
| Front right | `(2.47,-0.6,4.79)` | Identity, originalR mesh |
| Front left | `(-2.47,-0.6,4.79)` | Identity, originalL mesh |
| Rear right | `(2.455,-0.6,-4.09)` | Identity, originalR mesh |
| Rear left | `(-2.455,-0.6,-4.09)` | Identity, originalL mesh |

`FUN_005f6ec0` builds wheel translations using original axle coordinates and
sine/cosine of axle angles. `FUN_00434840` was checked as the cosine/sine helper.
Zero steering/camber/axle roll in the high-detail branch reduces the expressions
to these literal translations. This is a reproducible static rest-pose policy;
it is not a recovered settled suspension state under gravity.

**Preserved discrepancy:** TRK header wheelbase is8.78ft, while wheel centers
yield`4.79-(-4.09)=8.88ft`. Do not rescale or move axles to force agreement.

### The native1.05 field is not a general model scale

Loader field`vehicle+0x24a0` receives bits`0x3f866666` (float approximately1.05).
The original visual transform routine`FUN_005f6ec0` multiplies axle sine/cosine
by this field **only when body-detail field0x129c is less than1**. It affects
low-detail lateral/vertical wheel positioning through the axle expressions.
The high-detail2 path does **not** apply it. Do not multiply the body or wheel
meshes globally by1.05. The separate tyre-upgrade routine`FUN_005eaa40` can reset
the field to1.0; there are no stock parts for this TRK.

## Original stock BODY draw mask

The SMF's33 object flags are all1, but the native game subsequently derives a
separate draw mask. Treating all33 as simultaneously equipped is incorrect.

`FUN_005d3ad0` calls `FUN_005d43f0` in its explicit stock-mask branch
(`DAT_00d5f120==0`). That routine clears every per-object byte at model+0xe14,
then enables the21 names in the original pointer table at`0x0067d198`:

```text
BEDCOVR BODY BUMPERF BUMPERR CLADFR CLADLT CLADRR CLADRT GLASSE
MIRRORL MIRRORR UNDBODY WIPERLT WIPERRR WIPERRT XHAUST RFRACK
SPARE SPARE2 STEPS SUPPORT
```

Detail0 matches the names with suffix`L`; detail1/2 uses unsuffixed names.
Detail2 additionally enables`COCKPIT` and`GLASSI`. Native draw routine
`FUN_005b2bd0` submits a part only when its byte at+0xe14 is nonzero, corroborating
that the table enables drawing. Upgrade activation`FUN_005ea8e0` can enable
additional parts across all detail slots; with the original stock-parts count0
that loop performs no additions. A separate alternate-mask branch exists; it
does not authorize changing this explicitly selected stock inspection policy.

For the actual33 SR5 objects, the resulting high-detail static BODY pass is:

```text
Body Cockpit GlassI GlassE MirrorL MirrorR RfRack UndBody
WiperLT WiperRR WiperRT
```

The native table includes`RFRACK`: do not hide it merely because the English
name looks like an accessory. Conversely BushBar, FogB2/B3, FogR1..4, MudFlps,
RollBr1, Skid, Winch and Snorkel are disabled in this stock BODY pass.

`Axler` and the nine`Light*` objects also have BODY-pass mask0, but the game
handles axle/light meshes through separate systems. Retain them as runtime
auxiliary nodes with unqualified dynamic state; do not delete them or describe
them as permanently absent. The static BODY pass alone does not reconstruct
the original complete vehicle presentation.

## Evidence locations and limits

### Original TIFF channels are not qualified by Pillow's opaque output

The original body`ART/4RunnerSR5.TIF` declares palette photometric3,
BitsPerSample`(8,8)`, SamplesPerPixel2 and ExtraSamples`(0)` (**unspecified**).
Its512×512 strip contains524288bytes: two stored8-bit samples per pixel, plus
the original16-bit palette. Pillow's`P`→RGBA conversion exposes only the palette
sample and produces alpha255; that does **not** recover or qualify the second
stored sample. Preserve both raw samples and palette; second-channel meaning is
UNKNOWN. An opaque RGB preview must be labelled an explicit neutral interpretation.

The bump TIFF declares RGB photometric2 with four8-bit samples but no ExtraSamples
declaration. Its next-IFD word points inside pixel data; the single-channel indexed
wheel TIFF has a next-IFD value beyond its file. These nonconformant tail pointers
must not cause an unbounded IFD walk or authorize discarding the original bytes.
A bounded first-IFD decoder may preserve all channels and record invalid tail
references. The independent original tag/strip metadata and hashes are retained
in private`static-semantics/tiff-original-tags.json`. Neither alpha255 from an
inherited Pillow smoke nor a valid diffuse PNG proves original Evo2 alpha semantics.

Private machine evidence:
`.research-output/vehicles/evo2-pilot/static-semantics/semantics-evidence.json`.
It includes the exact executable/POD/TRK hashes, original source translations,
axis mapping, wheel slots, full mask list, actual selected object names and
eight raw-byte comparison records. Companion files retain per-member original
hashes, geometry extents, original TRK bytes and the winding check. These remain
private and are excluded from source-only review archives.

All Ghidra exports are in the single ignored repository scratch directory
`scratch/evo2-semantics/`: loader, initialiser, stock/alternate mask, upgrade,
model draw and wheel visual-transform pseudocode/instruction evidence. Important
raw instruction locations include:

| Address | Observed operation |
|---|---|
| `0x5d4493` | Clear stock per-object mask byte (loop base increment accounts for+0xe14) |
| `0x5d4545` | Read original stock-name pointer table at0x67d198 |
| `0x5d4585`, `0x5d45b4` | Enable matching base names / detail2 interior parts |
| `0x5b2d2d`, `0x5b2daf` | Check mask byte before part submission |
| `0x5efb55` onward | Format the six original wheel resource names |
| `0x5f71b8`, `0x5f71bf` | Select left/right wheel arrays by detail slot |
| `0x5f739c`, `0x5f73a8`, `0x5f73c7`, `0x5f73d3` | Read1.05 field in low-detail-only transform branch |

For this PE, the sampled code maps to file offsets using VA−0x400c00;
the sampled DGROUP table maps using VA−0x402000. Those formulas apply to these
specific sections/build, not arbitrary addresses or other executable versions.

Confirmed scope: original metadata, anatomical axis signs/feet, wheel resource
slots, static high-detail transforms and stock BODY mask. Still unqualified:
original running-game graphics/LOD selection, complete axle/light/damage passes,
settled suspension state, native shader appearance, model colors in original
runtime and any MR gameplay. No original file was modified or executed.


## Source Garage hardening follow-up — 30 October2026

Current original observations above remain intact. New exact4x42.exe analysis follows005d7980→004273d0 for the nine TRK HSV color records; float64 divisors360/100/100 and three code samples are checked against original PE mappings/bytes. A dual-plane consumer and recolor/high-byte branches are observed, but the complete TIFF second-plane association and renderer semantics remain WARN. Never convert unspecified ExtraSamples0 to ordinary alpha. No nine-color renderer parity, bump/reflection, dynamic Light*/Axler pass or settled-pose qualification is claimed. Six source views and diagnostics were refreshed. Accepted4Runner source-baseline3 DX/3 emitted DXT bytes are identical; six original L/R detail resources and high-detail exclusion of the1.05 low-detail factor remain. No source or accepted vehicle edit. See SOURCE_GARAGE_QUALIFICATION_MATRIX.md / SOURCE_GARAGE_WARN_RESOLUTION.md.
