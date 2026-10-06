# R-GFX4 continuation #2 findings — R-GFX4-3

READY_FOR_HUMAN_RUNTIME; new human A–E retest is pending. Starting branch research/general-re, HEAD25cb58d. R-GFX3 remains CLOSED. All edits are renderer-local; EXE/assets, frozen research and user renderer.zip remain unchanged.

**CONFIRMED_BY_CODE_AND_RUNTIME_TRACE:** R-GFX4-2's race→HUD projection transition reset temporal history before Present. The four new captures have positive known signatures but zero tracks/reflection modifications. Managed metadata survived two Resets, with epochs21170/21598 despite only two Resets. The new explicit race-seen frame state preserves history across HUD, expires it once on a menu-only frame and retains pool-aware Reset. [Lifetime correction](classifier-frame-lifetime.md), [hashed inputs](continuation2-runtime-evidence.json).

**CONFIRMED_BY_EXE:** CPU sphere visibility004F2380 uses four normals built by004F2620 from camera source/dimensions; final perspective uses004F2350→005614A0→0053F9E0 separately. Old linear CPU angles differ from a widened final projection. Separate body/four-wheel entities pass through common model bounds and can be rejected independently. The described X-Trail omission remains STRONG_HYPOTHESIS until the candidate's human edge test resolves it.

The approved narrow hook replaces the5-byte CALL006532DD→00509680 after current viewport dimensions are assigned. Source90 single-camera family gets four finite outward normals matching configured VFOV and actual perspective HFOV; source degrees, poses and distance/near/far remain stock. Planes restore before Present/Reset; final D3D override requires matching live proof. Disabled/unknown/failed signature or proof is stock, with no D3D-only fallback. [Static map and runtime constraints](fov-culling.md).

At640x480, VFOV80 corresponds to HFOV96.418343; at1920x1027 to114.967910. A linear source rewrite would require106.666667/149.561831; VFOV110 widescreen would exceed180, so the candidate never supplies those unsafe source values to the stock builder. Source45 preview and ortho remain excluded. Generic rotated/lookback contracts pass; actual five presets and edge behavior are pending human validation.

No constellation/material gate or reflection aesthetics changed. Only a mature unambiguous Body, opaque FVF152 and exact stock env stage qualifies for temporary NORMAL→REFLECTIONVECTOR→NORMAL high bits. Wheels, glass, static world, frontend and HUD stay excluded. Prior no-change screenshots on R-GFX4-2 do not evaluate the prototype because modified draws were0.

Corpus and current pristine test-install EXEs both rehashed to canonical bf8aef32… in this continuation, superseding the previous current-install warning below. Native contracts and build verification are separate from human runtime acceptance. The new handoff requires Stock A, then FOV edges/cameras/Reset B–D, before reflection E. Stop after preparing that retest; no later effects phase begins.

---

# R-GFX4-2 recorded findings (superseded candidate)

R-GFX4-2 is READY_FOR_HUMAN_RUNTIME. Reset fix and body-only ViewDependent2D are implemented and synthetically tested; the new DLL has no human runtime pass yet. R-GFX3 remains CLOSED / CONFIRMED_BY_RUNTIME. Previous R-GFX4-1 at HEAD 9c3a353 was deliberately classifier-only/BLOCKED_BY_CLASSIFICATION; the supplied runtime evidence now supports a bounded four-wheel structural classifier.

OFFLINE_GEOMETRY_ON_RECORDED_RUNTIME_TRACKS: canonical session 42928 on DLL b3a52962… contains four accepted chassis/four-wheel rectangles in frame 22806, three in frame 60310. Local half-width/half-wheelbase patterns are approximately .750/1.225, .875/1.385, 1.000/1.375, .825/1.200. All seven pass the generalized predicate; several wheels in the second frame lack independent dynamic flags. This is retrospective analysis, not a runtime pass for the new native classifier. Exact hashes, coordinates and errors are in constellation-runtime-evidence.json. The user's no-artifact/no-unexpected-change observation applies to that Stock DLL only.

CONFIRMED_BY_TRACE + CODE_DIAGNOSIS: session has 2095 MANAGED textures, 11 MANAGED VBs, 6 MANAGED IBs and 3 DEFAULT VBs across startup/two successful Resets. Each Reset is followed by one recreated DEFAULT VB and no recreated MANAGED resources. In frames 61896 and 99676 all draw classifications are UNKNOWN. Clearing the entire resource registry made surviving managed geometry signatures unknowable. New Reset removes default/RT/depth metadata and keeps managed generations; temporal identity/race context still resets. Relearning is proven on a mock timeline and awaits Stage A in the game.

Object identity and draw material are separate: VEHICLE_BODY, VEHICLE_WHEEL, UNKNOWN/CANDIDATE/DYNAMIC_ENV_OBJECT; individual base, opaque env, alpha env and wheel env families. Reflection requires an unambiguous previously completed four-wheel constellation, mapped indexed owner, race projection, known generations, FVF 0x152, no alpha blending, Z write and exact stock stage1 combiner. Only TCI high bits change from 0x10000 to 0x30000 for one native draw, then restore. Low bits, texture, matrix, combine, colors and lighting remain unchanged.

Backview means the active race camera's rear-view/look-back mode. It is not camera preset six: five normal selectable presets remain (3 follow + 2 fixed). VIEW flips do not clear world/geometry identity; projection/context/resource transitions do. Partial visibility can still conservatively lose a full rectangle. No draw-order or fixed participant-count rule is used.

CONFIRMED_BY_ASSET_PARSER: rerunning the existing tool on twelve protected retail car/wheel DX files exactly reproduced lighting-input-summary.json. 187 diffuse-enabled draws, 174 variable RGB; median strongest absolute normal/luma correlation .9535410087534312, 171 full-rank fits with median R² .9256522457919937; sampled vertex alpha is 255. This supports significant orientation-correlated prelighting/double-light risk, not a uniquely recovered baked sun. No new lighting or vertex changes.

Current test-install EXE hash fb11754c… differs from canonical bf8aef32…; historical captures' exact build identity remains valid. The current executable cannot validate target-specific effects. No installation files were changed. See continuation-starting-state.json and runtime-handoff.md.
