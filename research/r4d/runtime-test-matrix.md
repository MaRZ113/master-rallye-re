# R4D controlled original-game material tests

Status: **DESIGNED / NOT EXECUTED**. Each case uses a copy of the original archive and a same-size DXT replacement preserving the 20-byte header. Change one DXT resource per case, restore baseline before the next case, and capture the same camera/lighting state. Generated files and screenshots stay ignored. Test race car.dx and presentation complete.dx separately only where the question requires it.

| Case | Astero input / one change | One question | Expected discriminating observation |
|---|---|---|---|
| M1 | whitepaint-tga: replace RGB with a neutral gray, keep alpha | Does the slot-1 paint helper visibly affect body/decal draws? | Affected painted regions versus unchanged first-slot detail; report both positive and negative regions. |
| M2 | windscreen32-tga: set only alpha to 255, preserve RGB | Does first-slot pixel alpha change glass transparency? | Glass opacity changes while RGB pattern persists, or no change. |
| M3 | chrome-tga: replace RGB with left/right diagnostic colors, preserve alpha | Is this shared helper sampled in chrome/rim draws? | Colored reflection/helper contribution; camera rotation can distinguish fixed UV from view-dependent mapping. |
| M4 | breaklightsonglow-tga: set only alpha to 255, preserve RGB | Does glow-family alpha affect appearance during brake activation? | Compare brakes off/on at fixed camera and lighting; do not infer scene lighting from bright pixels alone. |
| M5 | mastersticker263-tga: replace RGB with a quadrant pattern, preserve alpha | Is the first slot responsible for visible decal detail? | Quadrant pattern follows the sticker surface; this does not by itself identify the slot-1 combine equation. |

For each execution record: source hash and dimensions, exact one-resource edit, scene/camera/light, predicted result, observed result, screenshot local path, conclusion, and confidence update. Do not run a slot-order swap without an independently safe material writer.
