# V-SDK1 third vehicle — GT4 Pajero Rally Raid '85

Status: **private offline author builds PASS; not gameplay qualified**. The third
vehicle is the genuine GT4 Beta `mits0038`, a tall short-wheelbase SUV rather
than another sedan. No alternate game's model was substituted.

## Source and selection

Authoritative private root:
`D:/Game/GT_Model-Tools/VOL/GT4-Beta_Extracted/extracted`.
The read-only identity trace is `CAR_VARIATION_american.idi` label
`pajero_parisdakar_rally_85`, row 705 → variation row 448 → string 2356
`mits0038`. Private `source-identity.json` records original table hashes and
row evidence. PDTools' local Variation/SDB readers provide comparative field
interpretation; this is not an asserted original PS2 instruction trace.

The initial Peugeot 206 candidate `peug0012` exposed a race V2-32 UV stream
outside the current qualified float interpretation. Its nonfinite-UV rejection
and private profile are preserved; no guessed UVs or substituted menu body
were used. Pajero's 24 menu / 95 race shapes decode and every stored shape is
accounted for in the source graph. One selected model/LOD is built at a time.

## Outputs

All paths below are relative to ignored `.research-output/vehicles/vsdk1/third/`:

| Output | Purpose |
| --- | --- |
| `source-profile.json` | Editable GT4 source hashes, callbacks, selection and rig labels |
| `build-02/assets/` | Original-resolution shared-converter DX/DXT resources |
| `validation.json` | Deterministic reconversion, source inventory, references and texture checks |
| `author-01/project/`, `author-build/` | Full-resolution independent author project and validated build |
| `author-02/project/`, `author-build-optimized/` | Optional cache-normalized independent project/build |
| `optimized-128/assets-normalization.json` | Exact changed-image hashes/dimensions and cache accounting |
| `optimized-validation.json` | Byte-identical repeat normalization and unchanged geometry checks |
| `preview/` | Front, rear, side, three-quarter and normalized Previewer captures |

Family is `SdkPajero85`, addon ID `mitsubishi-pajero-rally-raid-85`. Author slot
27 is only the preexisting standalone author validation slot. Collection
integration owns explicit rebinding to requested CarID 29; this build does not
reserve or patch runtime capacity itself.

The independent physics profile clones Navara into `SdkPajero85` with **no
handling overrides**. The independent audio namespace `pajero85` authors a
user-local stock MR `DataAudio/vehicles/engine3.wav` through the existing engine
pipeline. This initial donor sound is not identified as GT4 Pajero audio.
The project has its own names and both authored UI images.

## Shared improvements

1. `build_gt4_vehicle.py` now accounts for source passes masking **all RGB**
   while writing **no depth** as unsupported alpha-only preparation effects.
   They remain in diagnostics and never become invented visible MR geometry.
   Partial RGB masks and depth-writing cases still fail closed. No model code
   or shape number is involved.
2. `validate_gt4_vehicle.py` qualifies CAR4's actual rim component pointer at
   `0x20` as assembly authority. The separately stored original menu-wheel bank
   is independently decoded and hashed. Pajero's banks have different bytes
   but both contain four models/four shapes/2972 stored triangles. Their byte
   equality is reported, not assumed. Malformed structures still fail.
3. `normalize_vehicle_texture_residency.py` provides an optional deterministic
   integer box filter into a **new** asset directory. It preserves DX bytes,
   material references, normals and UVs. It does not edit the original GT data
   or silently alter source-decoder results. The editable project sidecar
   `texture-residency-profile.json` records this deliberate lossy author step.

Original-resolution family working set is 13,393,920 bytes. Cap 256 gives
9,265,152 bytes; cap 128 gives **3,170,304 bytes** (37 resized textures), leaving
more room in the native 32 MiB cache for Lancer and track/stock resources.
This proves accounting reduction, not absence of runtime cache stalls.

## Validation and remaining limits

- `complete.dx`: 8626 vertices / 7256 triangles / 214 physical draws.
- `car.dx`: 3027 vertices / 2179 triangles / 106 physical draws.
- `wheel.dx`: 1192 vertices / 1076 triangles / 24 physical draws.
- Every generated referenced DXT parses. Rebuilding original DX/DXT is byte
  deterministic. Repeating normalization is also byte deterministic.
- 26 focused synthetic tests pass, including new alpha-only rejection controls,
  distinct rim-bank provenance, malformed-bank rejection, filter arithmetic,
  output preservation, and unchanged model resources.
- Previewer captures were inspected. They show the recognizable complete SUV
  body, livery and coherent source-rest wheels. Source rest-pose assembly is
  not evidence of correct donor-physics wheel fit during gameplay.

Generated environment effects, destination-alpha dependencies and animation
remain shared documented GT4→MR approximations/unsupported source records.
Four alpha-only passes per body model are explicitly retained in the report.
This first third import does not claim full source-render fidelity, fitted MR
crew, native state-dependent brake conversion, tuned collision or GT4 physics.
Daylight lamp surfaces remain source-selected. Donor physics/attachment fit,
damage, AI/player rendering, independent sound and alpha filtering require
actual game testing in the parent combined candidate.

## Reproduction

Use the existing shared tools with a user-provided source root and profile:

```text
python tools/build_gt4_vehicle.py --source-root <GT4-root> --profile <profile.json> --donor <stock-Navara> --output <new-build>
python tools/validate_gt4_vehicle.py --source-root <GT4-root> --profile <profile.json> --donor <stock-Navara> --candidate <new-build> --output <validation.json>
python tools/prepare_gt4_addon.py --candidate <new-build> --donor <stock-Navara> --profile <profile.json> --output <new-author>
python tools/normalize_vehicle_texture_residency.py --source <new-build/assets> --output <new-normalized/assets> --max-edge 128
```

The normalization step is optional; update the copied project's scene/texture
sources before building it. Keep original and normalized builds distinct. No
proprietary models, textures, samples or screenshots belong in a source archive.
