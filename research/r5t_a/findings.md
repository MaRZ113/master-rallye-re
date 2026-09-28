# R5T-A findings

## Scope and baseline

This branch uses the main repository at the frozen Vehicle SDK v1 baseline. Work is limited to course resources and proven shared infrastructure. Original game/demo corpora are read in place; no course writer, executable patch, custom layout, or pushed change exists.

## Corpus and resource graph — CONFIRMED_BY_CORPUS

- Retail has 36 course folders, each with one DX, one TXT, one matched RaceTest XML, one nonempty HNT, one matched SFL, and 3,998 folder DXT files in aggregate.
- The retail resource graph resolves 2,842 HNT entries, leaves one exact reference unresolved, and finds no ambiguous path. HNT is evidence of declared dependencies, not proof that every declaration is required at runtime.
- All 42 course TXT sidecars across the supplied builds parse unchanged through the existing parser. Literal source names and directive-bearing lines are retained in `course-txt-analysis.json`.
- All scanned RaceTest XML roots are `Scene`; element/attribute counts and raw resource-like references are inventoried without assigning gameplay semantics.

## DX and compatibility — CONFIRMED_BY_BINARY / CONFIRMED_BY_CORPUS

- France1 and Italy1 DX revisions reproduce as 127 (Demo 8.4.1), 131 (Demo 9.3.1), and 135 (Demo 9.10.0 and retail).
- Shared DX header/vertex/normal/color/UV/local-index parsing is reusable. Revision-135 course root records, sequential draw batches, and course wrapper tags are interpreted additively in `dx_course.py`.
- The revision-135 course parser validates all 36 retail course DX files and both 9.10.0 target tracks. Retail yields complete, disjoint index and vertex coverage in all 36 cases; tag100 is reached at the render tail in each.
- Demo 9.3.1 course files are revision 131. Their first 8-byte root prefix and tag-4 root tag match the later layout; raw tag-4 control words are `(49, 1, 106)` for France1 and `(77, 1, 66)` for Italy1, versus `(49, 1, 23)` and `(77, 1, 28)` in 9.10.0. The first tag-2 body also differs from the revision-135 core: at the later 40-byte core boundary, its presumed slot-count word reads 845,116,275 for France1 and 1,936,941,426 for Italy1 from printable texture-name bytes. Demo 8.4.1 revision 127 has a visibly different root envelope. These are format boundaries, not explanations of the user-observed empty-world behavior.
- The user's runtime observation is `CONFIRMED_BY_RUNTIME`: retail course packages load in Demo 9.10.0 with needed files supplied, while Demo 9.3.1 and 8.4.1 produce an empty/void world. The cause remains unattributed.

## France1 / Italy1 timeline

Per-layer sizes and hashes are in `france1-evolution.md` and `italy1-evolution.md`; complete records are in `course-evolution.json`.

- Both source GXM files are present only in Demo 8.4.1. Their post-header body is not parsed. Two header word relationships to same-build TXT counts are `CONFIRMED_BY_SOURCE_COMPILED_PAIR`, but do not establish geometry or directives.
- TXT parses in every version. Italy1 material counts move 66 → 90 → 100 → 100; France1 121 → 150 → 158 → 127. Mesh spans and names are preserved in JSON.
- France1/Italy1 SFL exists in 9.3.1, 9.10.0, and retail. Dimensions and header bytes match across those three; France1 payload SHA-256 changes from `1e60ee1a…` to `e2cb9884…`, and Italy1 from `8b6c46c3…` to `fe3b8af9…`; the 9.10.0 payloads match retail.
- Italy1's literal root child changes from `<EggLists_Version3>` in 9.3.1 to `<EggLists_Version4>` in 9.10.0 and retail. France1 already has the version-4 element in 9.3.1. XML sizes and hashes also change.
- Retail HNT is present for both tracks; Demo 9.3.1 has no course HNT, while Demo 9.10.0 has an empty Italy1 HNT and no France1 HNT.
- The two demo course folders gain 33 DXT files in aggregate (145 → 178). Italy1/France1 TXT material counts change 90→100 and 150→158, with corresponding mesh-count/span changes. These package-level changes remain compatibility candidates, not proven causes.

## SFL / FL / SF — CONFIRMED_BY_BINARY

Every retail SFL satisfies `20 + width × height` bytes. The first header float is 3.0; the remaining fields and cell semantics remain unknown. Ten Demo 8.4.1 FL/SF candidates satisfy 20-byte-header plus four bytes per cell. Header dimensions differ from later SFL; only a broad historical relation is plausible. Flip pairs with equal dimensions/header can still have different payload hashes.

## Source and compiler boundary — UNKNOWN / PARTIAL

The existing vehicle GXM parser is not reused for course bodies. A bounded probe records the 32-byte Demo 8.4.1 headers and same-build TXT count relations. Source objects, hierarchy, render correspondence, `$bsp` compilation, `$grnd*` storage, and cooker transformations are not decoded. No standalone Demo 9.10 cooker was identified; a course cooker bridge was not tested.

## Blender — PARTIAL

The existing add-on now imports revision-135 course render geometry, reuses the vehicle coordinate transform and material/DXT preview path, preserves source identifiers and opaque metadata, and blocks all vehicle exporters for course objects. Italy1 and France1 have complete parser-side counts. Blender itself is unavailable in this environment, so headless import and visual confirmation remain outstanding.

## Evidence-driven next phase

R5T-B should focus on source-to-compiled course semantics: parse the small developer GXM oracles and correlate `$bsp`, `$grnd*`, `$landdb`, and marker directives with compiled sections. Physical tag100 decoding should follow only where that correlation or exact consumer evidence narrows the structure.
