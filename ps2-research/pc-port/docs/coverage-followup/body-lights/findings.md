# Remaining body and lamp material boundaries

Read-only source audit on master starting22c0ccad5c849f949e7275e9b4afb09da6e75b93.
Original PSM/DX payloads remain read-only. `source-joins.json` contains only source
hashes, offsets, material records, hierarchy and counts; no complete geometry.
Current registry and all previous findings remain unchanged.

## Principal uncovered source draws

These are original compiled source record indices, never persistent native draw
ordinals. Counts refer to nondegenerate PC source faces. The .005 diagnostic
matches all original PS2 visual material categories rather than filtering to
carshiny; it does not authorize a looser runtime geometry signature.

| PC family / draw | .005 source relationship | Whole-draw Mode4 decision |
|---|---|---|
| LandCruiser8 |215/240 faces join root.15 carshiny;25 remain unmatched |Not proved |
| LandCruiser9 |373/477 faces join root.14 carshiny;104 remain unmatched |Not proved |
| Bruno4 |38 root.4 +191 root.5 carshiny;3/232 unmatched |Not proved |
| SeatBuggy7 |165/169 root.4 carshiny;4 unmatched |Not proved |
| ChevyBlazer7 |60 root.7 carshiny +10 root.21 carglass |Mixed actual PS2 handlers |
| Xtrail1 |195 root.1 carshiny +14 root.2 carflat |Mixed actual PS2 handlers |
| Forester8 |43 root.2 carshiny +11 root.5 untagged; minor duplicate-face ownership also occurs |Mixed resource/auxiliary behavior |
| Forester9 |43 root.9 carshiny +28 root.4 untagged |Mixed resource/auxiliary behavior |

Forester uses PS2 **WOOLDAND**, not PS2 FORESTER. Already registered main
Forester10/12/14 remain verified separately. Its small opaque draw2 grille
(4faces) corresponds wholly to WOOLDAND root.1 carshiny, but PC slot1 isNull;
a source match does not prove a live normal-bearing environment draw.
Xtrail21/22 (28/14faces) are whole carshiny joins, but original PC alpha flags
01000101 violate the current opaque native contract. Forester7 is a helmet,
not a principal body addition. Other whole omitted carshiny roots in the six
families preserve authored rubber instead of replacing it with the mixed target.

## New exact R5900 default-material evidence

Ghidra12.1.4/EER used the existing canonical R5900 project read-only with
`-readOnly -noanalysis`. `BodyMaterialProbe.java` exported six bounded functions.
Rabbitizer1.16.2, **InstrCategory.R5900**, independently verified1308 original
instruction words against canonical ELF PT_LOAD mapping;92 compact probes are
committed in `r5900-byte-evidence.json`. Full export remains ignored at
`ps2-research/data/revalidation2/body-material-probe.txt`.

- **390a98** reads three booleans per texture record; **390ba8:390cb0–390cc8**
  proves20-byte source map records (actual R5900 `mult v0,v0,v1` with0x14).
  The older generic-MIPS surrogate decompilation dropped this multiplier.
- **391690:391774–3918b4** sets generic mode3 when primary and secondary exist
  and the first two primary flags are not both set. It retains authored maps.
- **3a6c58** logs unrecognized shader names without calling a handler. Literal
  carbrakelights/carbrakelight/brakelight/crashiny C strings are not present in
  the canonical ELF; no alias to carshiny is assumed. Registry initialization
  **390f98** was independently exported for bounded review.
- **3ade58** is the actual carshiny handler: mode3, separate color auxiliary,
  defaults and secondary `CommonTextures\\rendertarget64x64` substitution,
  except the original rubber substring exception.

Thus untagged WOOLDAND FLight64/FRear128 run generic mode3 but retain
perspex/whitepaint. They are **not equivalent to running carshiny**. The typo
crashiny also retains generic mode3 and authored rubber. Dynamic environment
override over every face of those mixed PC draws would change original meaning.

## Brake-on, glow and off-light surfaces are separate

**391690 applies primary-name overrides after shader resolution**:

| Exact primary substring | Original writes | Consequence |
|---|---|---|
|`breaklightsonglow-` at487958 |391c54/58 mode14;391c64 +2c=1;391c6c +3c=0;391c84 +44=.3 |Special glow mode, not ordinary body mode3 |
|`breaklightson-` at487970 |391cc0/c4 mode1;391ccc +2c=0;391cd4 +3c=0;391cec +44=.3 |Single-texture lamp-on mode |

These are the original **break**, not normalized **brake**, spellings.
The bounded29-family CAR.PSM inventory finds60 brake-related mesh records:
28 final-mode1,28 final-mode14 and4 mode3 off-light shapes. This is not60 lamps
or60 simultaneously visible objects. Named/indexed children remain conditional.
Chevy brake children have no shader directives at all but the same primary-name
overrides still classify them correctly. The final mode differs from the generic
pre-shader mode in `source-joins.json`; neither is silently promoted to carshiny.

The current PS2-port opaque-only Mode4 excludes glow and alpha draws. Source
evidence supports examining static/off-light materials separately, not adding
the dynamic framebuffer environment to every stop-light polygon. Full mode14
GS state, brake-child runtime selection and actual lightshine/perspex sampling
remain outside this bounded audit; pixel-level behavior remains UNKNOWN.

## Safe implementation options

1. Preserve current exact source/native admission and fix independent Reset
   behavior. Source materials above explain why texture-only or whole-draw
   broadening is unsafe.
2. Add Forester grille only after the actual normal-bearing environment layout
   and resource context are verified. Add Xtrail alpha-carshiny groups only
   with a separately tested alpha-preserving transaction and actual live identity.
3. For mixed body groups, port a material partition or original visual-body mesh
   with proved source ownership. A whole-model replacement needs PC pose,
   wheel/driver/LOD/glass/lamp suppression and lifetime rules; replacing every
   mixed source draw with dynamic reflection is not equivalent.
4. A lamp pilot needs one original off/on/glow conditional identity and the
   mode14 producer/GS contract; no fake modern glow or blanket dynamic reflection.

No native override, original asset, renderer source or integration patch was
edited by this audit. No runtime visual improvement is claimed.

## Reproduction and validation

Executed: `python .../body-lights/audit.py`, canonical read-only EER headless
probe, tooling-venv `python .../body-lights/verify_bytes.py`, Python unittest
discover in this directory (**4/4PASS**), compileall and git diff-check.
Audit regeneration requires canonical PS2 PackFS and protected PC retail corpus,
plus read-only Course SDK. Fixture tests require only the two compact JSON files;
byte regeneration additionally needs Rabbitizer and the ignored Ghidra export.
