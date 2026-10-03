# R-MAT1 vehicle material final closeout

**Vehicle material runtime model: CLOSED WITH NON-BLOCKING UNKNOWNS.**
**Blender vehicle material preview: APPROXIMATE WITH DOCUMENTED LIMITATIONS.**
Date: 2026-10-03. No new human runtime result is claimed.

## Baseline and scope

Only the existing `master-rallye-re` checkout was used. Starting branch was
`research/r5t-course-archaeology`, HEAD `8014edc`; tracked files were clean and
`git diff --check` passed. User-owned untracked `_ghidra_project/` and
`master-rallye-re-blend.zip` were retained. A narrow local `research/r-mat1`
branch was created from that HEAD to keep vehicle work separate from the
current course research. No sibling checkout, worktree, merge, or push was used.

Baseline: 245 synthetic tests passed, compileall passed, Blender 5.2.2 LTS
`d13f752e3b9c` synthetic R4E smoke passed, and the R4E full-corpus Blender
attribute exporter produced 78/78 byte-identical zero edits.

The mutable unpacked asset tree failed validation on Bowler/car.dx, so the
corpus audit used the protected retail `corpora/retail/Data.sma_unpacked/DataGx/Vehicles`
reference. Neither tree was modified. The fresh [corpus report](corpus-validation.json)
records resource hashes and every draw classification, rather than assuming
that an older report describes current inputs.

## Consolidated results

| Question | Result | Evidence |
|---|---|---|
| Slot identities | slot0 -> material +38 -> compiled binding 0 -> stage0; slot1 -> +3C -> binding 1 -> stage1 | CONFIRMED_BY_EXE; [binding chain](texture-stage-binding.md) |
| Null base | No promotion; stage0 stays NULL and slot1 stays stage1. Family remains base_env when Reflections is ON | CONFIRMED_BY_EXE; pixel cascade is HIGH_CONFIDENCE_INFERENCE |
| Byte2 | Pass vertex diffuse/FVF DIFFUSE enable, not alpha test or a second texture | CONFIRMED_BY_EXE; [flags](material-flags.md) |
| Byte3 | Pass source UV count/dimension enable | CONFIRMED_BY_EXE; only the two textureless stock draws disable it |
| Vehicle feature bits | 01 base handle gate; 02 contributes the base selector; 04 env plus global Reflections gate | CONFIRMED_BY_EXE; byte2/mask02 equality is separately CONFIRMED_BY_CORPUS |
| Alpha ordering | Separate alpha queue; per-pass composite key includes descending shared bound depth, order counter, shader, texture | CONFIRMED_BY_EXE; [ordering](transparent-ordering.md) |
| Decal/glow | Observed sticker draws use ordinary opaque base/env; observed glow draws use ordinary source-alpha base/env | EXE selector plus CORPUS, no stock vehicle additive family |
| Damage env fade | Configuration object in renderer, further damage mutation path not audited | OUTSIDE STATIC MATERIAL PREVIEW; non-blocking |

The typed model now supplies stage records, combine expressions, shader family,
feature/flag consequences, render-state scope, Reflections OFF projection, and
explicit unsupported-branch reasons. It is a read-only annotation, not an
expanded writer contract. [Runtime map](runtime-material-map.md) distinguishes
shader setup from later instance depth-state writes.

## Corpus and preview coverage

78 resources / 26 vehicle folders / 1478 physical draws, all CLASSIFIED.
Slot0 is populated 1473 times, slot1 1092 times, slot2 zero times. Masks are
1:21, 2:2, 3:363, 5:151, 6:3, 7:938. There are 1241 opaque, 237 alpha blend,
and zero stock alpha-test draws. Byte2 distribution is 0:172 / 1:1306;
byte3 is 0:2 / 1:1476.

The old filename rule covered 367/1092 slot1 bindings. V3 handles all 1092
bindings generically; 1089 produce an environment node preview, while three
NULL-base bindings preserve stage identity and suppress the env contribution
under the documented NULL-cascade inference. All eight helper names are
covered. The shader family and bound-stage counts deliberately differ from
the effective preview count.

Name-filtered decal evidence includes 48 draws (46 base_env, 2 base), all opaque.
For example Astero/car.dx draw12 is mastersticker263/perspex, flags 00000101,
mask7. There are 25 glow-name draws: 14 base_env_alpha and 11 base_alpha.
Astero/car.dx draw30 is breaklightsonglow/perspex, flags 01000001, mask5;
ChevyBlazer/car.dx draw35 has the same glow texture with NULL helper, mask1.
Their framebuffer factors are SRCALPHA/INVSRCALPHA, not an additive vehicle
special case. Name filters only select examples: family classification never
reads a filename. Lamp-name draws include both opaque and alpha layers.

## Existing runtime evidence retained

R4D.1 M1/M3 establish the tested Astero body/chrome helper response and its
Reflections gate; M2 establishes the tested glass source-alpha response; M4
establishes active brake-glow alpha response. R4E E1/E3/E4 and R4E.1 N1/M1
retain their exact human result labels for UV/color/alpha/normal/env edits.
The inconclusive R4E E2 observation is not rewritten. See
[R4D.1 runtime results](../r4d_1/runtime-results.md),
[R4E runtime results](../r4e/runtime-results.md), and
[R4E.1 runtime results](../r4e_1/runtime-results.md).

No runtime probe is required for a remaining vehicle-used family ambiguity.
No candidate EXE, DX or DXT was prepared for in-game testing. Automated Blender
exports are verification copies under ignored output, not runtime evidence.

See [validation](validation.md), [Blender preview](blender-preview.md), and
[remaining unknowns](remaining-unknowns.md). NEXT: **STOP**.
