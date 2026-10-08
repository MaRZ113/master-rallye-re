# Read-only PC comparison

Reference SDK HEAD `4244fa0c4d878523c9947f54816bf377cdfb2589`, branch `research/r5t-course-archaeology`, clean before/after. The three compiled DX/TXT pairs are validated by fresh SHA-256 against WATER1's frozen independent source identities and complete-disjoint SDK draw coverage. Compiled DX remains the visual source authority; a TXT name is not an independently owned instance.

## Original PC evidence versus experiments

The following is existing **ORIGINAL_PC_ENGINE_BEHAVIOR**, from the read-only SDK's `research/r4d_1/alpha-path.md` and `dx-to-runtime-material.md`, not a D3D8 proxy experiment:

* Loader005528b0 copies tag2 flag bytes+20/+21 into runtime material+22/+23.
* Selector00580360 chooses no alpha suffix when+22=0, `_alpha` for+22≠0,+23=0, `_alphatest` when both are nonzero. Registration00565da0 supplies those variants.
* Original base-family state method005867a0 sets `_alpha`: depth-write0, depth-enable1, blending1,SRCALPHA/INVSRCALPHA, alpha-test0.
* `_alphatest`: depth-write1, blending0, alpha-test1,GREATER128.

This original executable analysis was principally validated on vehicle records. It establishes the shared loader/selector/base-family contract. Applying it to the selected **course** flags predicts the alpha-test variant, but the exact live course handler invocation and state are **STATIC_PC_INFERENCE / NOT_CAPTURED**. It is not promoted to a runtime-confirmed foliage path or used to infer a PC billboard algorithm.

## Selected compiled course records

| Course/draw | Tag2 core | Raw flags+20..23 | Feature mask+24 | Unsigned unique triangles /records | Generic selector prediction |
|---|---|---|---|---|---|
| France1 pinetree/283 | 3281947 | 1,1,1,1 | 3 | 80 /320 | _alphatest |
| France1 bush01/54 | 3261170 | 1,1,1,1 | 3 | 24 /48 | _alphatest |

Focused integration tests independently read those four flag bytes and mask directly from the original DX at core+20/+24, in addition to the SDK reader. Both source draws contain both triangle windings; culling/live duplication remains unknown. The PS2 shader's use of authored strips does not imply a one-for-one PC draw/vertex layout.

## Texture comparison

Use existing SDK `dxt.py`: FEED wrapper,20-byte header, raw BGRA. Conversion to RGBA explicitly compares `preserve-stored` and `flip-vertical`; no automatic orientation is chosen to conceal a mismatch.

| Family | PS2 | PC | Proved relation |
|---|---|---|---|
| Italy pinus2 | 128×128,6 stored alpha values | 128×128,6 | Full RGBA identical under flip-vertical |
| France pinetree | 128×128,4 | 128×128,4 | Full RGBA identical under flip-vertical |
| France bush01 | 64×64,89 | 128×128,15 | Different stored image/dimensions/alpha distribution |
| Turkey shrubtrig2 | 64×64,255 | Explicit paired path not found | Bounded missing paired-resource result |
| Turkey hut_01 | 64×64,A=255 | 128×128,A=0 | Different file pixels; opaque material control |

PC file SHA-256 and both converted pixel hashes are in the case matrix. Full image equality is `CONFIRMED_BY_BYTES`; equivalent final sampled alpha, mips or appearance is not inferred from it.

The France bush01 example can therefore differ through material blending/depth, texture resolution/alpha and source tint, while the selected geometric surface remains shared. Pinetree demonstrates that a PS2-looking foliage texture need not require a new image. Turkey/Italy selected-group placement remains separately unresolved.

## Renderer and content limits

No current PC proxy experiment is proof of either retail PC or PS2 behavior. No PC modernized tree classifier, coordinate generator or stage state was edited. A future proxy needs a reliable material/draw interface; seeing a flat triangle, an alpha image or a pine texture is insufficient to identify a particular PS2 category or scene instance.

The PS2 cutout threshold64 and PC base-family128 use different channel conventions. Numerical thresholds alone do not demonstrate equivalent coverage: PS2 runtime texture/palette/TEXA conversion is not closed. PC billboard, live alpha sorting and exact per-course shader ownership are future capture questions, not new research claims.
