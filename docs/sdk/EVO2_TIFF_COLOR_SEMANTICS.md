# Evo2 TIFF and original color semantics — v8.0

This checkpoint extends the retained `EVO2_SOURCE_SEMANTICS.md`; it does not replace its equipment, wheel, axle or suspension evidence. The accepted native Toyota 4Runner and original neutral scene remain unchanged.

## Qualified boundary

**PASS: original pre-gloss CPU color reconstruction. WARN: original GPU alpha, bump/reflection response and complete runtime appearance.**

The second indexed TIFF sample is demonstrably a control input to color processing and is copied into the packed output high byte. It is not safe to call it ordinary image opacity. The new preview uses the recovered RGB with opaque cache alpha; the original auxiliary sample and packed native output remain separate. No native MR material changes are authorized by this experiment.

The new `source_adapters/evo2_color.py` runs a narrowly bounded original x86 consumer in isolated Unicorn, using the owner's hash-pinned EXE. It carries no executable payload. The original HSV helpers and CRT conversion instructions execute directly, avoiding an attractive but unverified replacement recoloring algorithm. The host does not launch the game or service original file/OS/GPU calls.

## Exact source and executable evidence

- `4x42.exe`: `ab8286e6bce8a1bf3769acddfeb0a79df2e5d43c72f462a89aa90f477951ec75`.
- `TRUCK.POD`: `5669509d709193621802a43c2c63b32e537fcf93ea3fd5d94af8c66947be6a41`.
- `TRUCK/T4RSR52.TRK`: `d2ff6c5914e8102116e56704dac800442fed3adfbf42326c6b3311517e8bbcb4`.
- Original body `MODELS/4RUNNERSR5.SMF`: `a7f71e0ae1cae2fb64438ce8614bf7db47eb9dfc813d926388da4dfef7b6a11e`.
- Body TIFF `ART/4RunnerSR5.TIF`: indexed photometric3, 512×512, chunky two unsigned8 samples, ExtraSamples0. Source raw samples SHA256 `0e1eb17588e44770fe8b6f6cc1e9d416d691ab2234a93bcbd0effa44b1161b82`; original1536-byte ColorMap SHA256 `726d29c8c4ae64c73785605c520b945fa91248da25b48b88e06d8dfc60d16043`.
- Immutable baseline scene SHA256 `05cb2b9db5b3c103cd623b8c1282099ac9f1f1f93593ad95d8243003f41e33dd`.

The original 16-bit ColorMap uses byte-replicated samples (`value % 257 == 0`) for all768 entries. This implementation rejects a different palette reduction rule. Both raw planes and full original palette remain hash-bound by the UVS manifest.

Existing `005d7980` evidence connects the selected TRK color record to the color texture consumer near `004273d0`. Its first3 parameters divide by original **float64** constants360/100/100 at `0065b5c0/0065b5c8`, then pass float32 values. The final3 RGB numbers in each catalog row are preserved metadata; they are not substituted for this HSV calculation.

New independent PE instruction inspection confirms `0047c63f..0047c68f`: for the indexed additional-sample branch the virtual stream byte reader is called twice per pixel. First byte enters the buffer at image-object+`0x228`; second enters+`0x22c`. The existing consumer retrieves both exact pointers through its TIFF image instance and binds them to `008218c0/008218c4`. This is actual byte routing, not an image-library alpha interpretation. Ghidra did not define the indirect TIFF procedures as functions; Capstone5.0.7 independently decoded these original mapped instruction bytes. The new REA/Ghidra12.1.4 evidence verifies the original bytes and RGB↔HSV helpers; decompiled output is analysis, not original source.

Private evidence remains in `scratch/cross-game-materials/evo2/`: `rea-evidence.json`, `rea-snapshot.json`, original address-disassembly windows and controlled replay diagnostics. These files and extracted pixels are excluded from source review packages.

## Established arithmetic

1. Input plane0 is a palette index. Plane1 is the auxiliary byte.
2. Convert original palette RGB to HSV using original `004269a0`; hue for unsaturated colors is−1. Count palette-index occurrences where plane1>250; choose the first index with the largest count (strict greater comparison). The qualified4Runner's index0 black wins, and the selected base HSV is `[−1,0,0]`. This surprising result is retained exactly.
3. The nonzero color branch bounds each original hue to the selected dominant hue±0.05, adds selected hue delta/360, wraps once, adds/clamps saturation and value deltas/100, then runs original `004267d0` and `0060fb82` conversion. Zero HSV deltas copy the original palette exactly.
4. At `00427c76` and `00428112`: auxiliary0..128 selects original RGB;255 selects recolored RGB;129..254 mixes them with float32 `(auxiliary−128)/127`. Native CRT conversion truncates nonnegative mixed channels toward zero. In every branch the original auxiliary byte enters the packed output high byte.
5. The optional bump/gloss processing starts at `00427d23`. The new reconstruction stops **before** it. Existing evidence shows a separate `%s_BUMP.TIF` branch and modification of the high byte. Its complete GPU meaning is not qualified here.

Actual plane1 counts:88492 pixels in0..128;7239 in129..254;166413 at255. Neither an unconditional recolor nor conventional alpha-only treatment reproduces this behavior.

The original-instruction replay starts `004276f8`, after file loading and allocation, with original loader-equivalent palette/planes explicitly supplied. It checks the intermediate palette endpoint `00427c30`, then stops at `00427d23`; instruction/time budgets and exact EIP checks fail closed. Canonical packed RGB uses the original24-bit branch with its independent high byte. This does not claim an original runtime framebuffer format.

## Reusable implementation and reversible variants

`reconstruct()` validates exact executable identity, dimensions≤512, dual-plane length, finite bounded color values and qualified palette layout. It replays the original palette arithmetic and full per-pixel composition. A separate source-controlled `composite()` implementation must match the entire native packed output byte for byte before success. The high byte must equal plane1 exactly. The preview RGBA explicitly sets alpha255.

`derive_scene()` requires the qualified Evo2 adapter, catalog/body/EXE hashes and original9-record catalog. It creates a new UVS directory containing every original sidecar unchanged. Only a derived body-texture pointer/hash, color metadata and explicit remaining WARN are added. Original geometry, materials, transforms, UVs, wheel variants, source object and source records are compared unchanged before serialization. Original body RGBA remains under its old path and every derived texture can be discarded by reopening the baseline.

The nine configurations are the original TRK rows318..326, zero-based index0..8:

| Index | Original HSV deltas | Original catalog RGB metadata |
|---|---|---|
|0|36.75,−5.42,−27.08|137,151,142|
|1|0,0,0|196,187,179|
|2|4.5,7.5,−18.33|172,153,144|
|3|339,81.25,−17.08|153,45,27|
|4|336.75,99.58,−56.25|70,31,17|
|5|137.25,33.33,−67.92|32,51,51|
|6|203.25,12.08,−40.83|76,76,94|
|7|203.25,23.75,−69.17|37,36,51|
|8|203.25,−95.42,−73.75|20,20,20|

## Reproduction and private visual evidence

```powershell
python tools/evo2_color_lab.py --scene .research-output/vehicles/4runner-stable/baseline/inputs/source-scene/scene.json --executable "E:/RallyWorkshop_Sources/sources/4x4 Evo 2/4x42.exe" --output .research-output/vehicles/cross-game-materials/evo2/new-colors --viewer .research-output/rally-workshop/bin/mr-vehicle-previewer.exe
```

The output must be fresh and outside original sources. Private final output: `.research-output/vehicles/cross-game-materials/evo2/final-colors/`. It includes9 independently reopenable scenes, original color-row identities, native packed outputs and palettes, `validation.json`, `nine-colors.png`, independent index/auxiliary/base planes, and6 consistent D3D9 views per color when `--viewer` is supplied. Pixel sheets are texture diagnostics; only the viewer captures are D3D9 evidence. There is no owner-local original-game capture establishing GPU parity.

## Validation and unresolved scope

Six focused tests include the verified failure classes: ordinary-alpha/unconditional-recolor confusion, intermediate arithmetic and truncation, all256 auxiliary values, palette ambiguity, nonfinite inputs, excessive size, wrong EXE and deterministic original-instruction replay. Actual9×512² outputs each match source-controlled composition and preserve the auxiliary high byte. Every scene reopens; repeated reconstruction is byte-identical; source JSON/sidecars remain immutable. The zero-delta configuration retains base RGB.

The optional original BUMP/gloss branch, final high-byte renderer use, source reflections, native glass/filtering and original runtime parity remain WARN/UNQUALIFIED. Auxiliary Light/Axler objects, suspension settling and accepted high-detail wheel transformations are not changed. No low-detail1.05 factor is introduced. No accepted native paint, lamp, glass, reflection or interior resource is overwritten.
