# R-GFX5-4 stable PreserveMargins anchor semantics

Human/runtime narrowed the active defect: the final consumer hook is installed, widened projection stable, restore_failures0, yet animated HUD/decorations jitter. Do not recast missing sorter head as the remaining cause. DrawTextPacket VA0x0056D110/RVA0x0016D110 stays the only production packet hook; Present/Reset/disable/release coordinate ownership boundary stays intact.

Historical 51 exact XY points and bounded left text regions are authoritative admission evidence, unchanged. MarginAnchors (512 slots) stores LEFT/RIGHT, not original XY. Key: entity, entity+4C packet, packet+54 point, packet+8 content row-vector allocation, packet+68 mode1/2, plus registry UI epoch. The existing read-only Ghidra bridge consumer export confirms +8/+C row storage, +54 point and +68 mode; these are not guessed object labels. Each consumption revalidates the structure and reads current engine XY; admitted direction offsets current X by direction*half, preserving animation. Never-matched/invalid/overflow packets remain centered.

Retention invalidates on packet/point/content-allocation/mode change, invalid structure/nonfinite/nonzeroZ, Reset, disable/release, or validated source45/frontend versus source90/race family transition. Context uses already-supported camera owner and original projection, independently of optional GameplayFOV. It does not infer gameplay from the inner UI orthographic projection. A packet absent for a complete consumer frame expires; later reused addresses must independently admit again. No global X>320 heuristic, frozen coordinate, old sort hook or new whole-image SHA profile.

Safety boundary: content allocation and continuous validated consumption are observed lifetime evidence, not a heap allocator generation. No universal native menu/screen generation or allocator free hook has been proven. Same full identity reused without any observed gap/context/storage change is unobservable; it is not claimed safe by raw pointer alone. MainMenu/QuickRace transitions and centered replacement are explicit human regression checks. Reset/family transitions have tested explicit epochs; menu replacement is guarded by changed storage/identity or absence. The conservative missing-frame rule can cause re-admission after an element is hidden; no persistent grace is silently added.

MarginFrame independently owns live memory edits until Present. Duplicate consumes normalize only their still-owned X before admission and never add a second offset. An engine X rewrite becomes a fresh logical value; a Y-only rewrite preserves its new Y without accumulating X offset. Mode/owner/content-storage/XYZ replacement cancels stale restore. An epoch ends pending ownership through the same guarded restore before a new context can learn. The ordinary Present boundary is not redesigned. Camera-family detection preserves caller FPU flags and rounding mode.

Bounded F10 session records now include anchor_id/direction/source/new/retained, ui_epoch, packet mode/content/point storage, current_rule_match, engine_x/engine_y, effective_x and anchor_invalidated_reason. Unanchored packets also appear during the three diagnostic frames. Counters include retained_anchor_without_current_rule_match, admissions/invalidations/count/overflow; positive retained-without-match proves an animated trajectory is using semantic retention. Maximum64 diagnostic slots/256 lifetime records unchanged. No continuous huge log.

Synthetic tests cover20-frame LEFT/RIGHT animation, center exclusion, packet/mode/point/content replacement, Reset/scene epoch, absence expiry, capacity, duplicate and production consume/restore. Centered4x3, preview, UI projection/rules/ABI, MSAA and other feature owners are unchanged. Backdrop remains BACKDROP_ASSET_EXTENSION_REQUIRED.

## Historical R-GFX5-3 UI implementation

# R-GFX5-3: frontend camera and packet consumption

## Frontend preview

CONFIRMED_BY_EXE: helper VA 0x004F2350 / RVA 0x000F2350 returns sourceAngle * height/width for landscape, otherwise sourceAngle. Thus source45 at 4:3 has VFOV 33.75 degrees. The separate FrontendPreviewAspectCorrection validates the camera owner group, main-image projection caller and symmetric LH source45 matrix. With InterfaceMode enabled it recomputes X/Y scales using sourceAngle/(4/3), preserving the current aspect and near/far terms. It never reads the user's gameplay VFOV. Source90 still uses synchronized gameplay FOV only; Stock UI leaves preview Stock. Rejected preview writes retry original and disable only this correction.

## PreserveMargins restore boundary

CONFIRMED_BY_EXE: SortPerCamera_00509970 (RVA 0x00109970) handles the first node separately at 005099B0, using entity+50. The old hook at 00509A21 exists only inside the subsequent-node loop. Consequently not every rendered packet passed through the modifier; changing list head is a concrete route to alternating offsets. This does not prove delayed/double-buffered packet consumption.

DrawTextPacket_0056D110 (RVA 0x0016D110) reads entity+4C, packet mode+68 and point+54 before generating/copying glyph/quad vertices to the dynamic buffer and drawing at return RVA 0x0016D7C4. The new six-byte entry hook replays SUB ESP,108h after a register/flags/x87/SSE-preserving bridge, observes the real first stack argument and shifts eligible mode1/2 packet coordinates before this consumer. The sort list and comparison coordinates are untouched.

Every consumption is covered, including a list head or packet consumed again after Present. Logical/effective XYZ stays frame-local: no stale cross-frame pointer identity is promoted into ownership. Duplicate reads do not double-shift; an intervening engine rewrite creates a new logical baseline. End-of-consumer-frame Present, Reset, disable/release restore only still-owned matching XYZ; entity+4C replacement cancels restoration. Each new consumption reacquires the edit, so ten frames of reused storage render the same shifted X even with no engine rewrite. Different Y/Z and unknown margin positions retain the existing safe exclusions.

A 64-slot observation table holds diagnostic identity only, never writable ownership. F10 arms three consecutive consumer frames, using the same Trace frame number; normal boot/menu traffic cannot exhaust the budget before the HUD capture. At most 256 ui_packet_lifetime records per device include packet/entity/consumer RVA, stable diagnostic ID, first/current/previous/restored frame, original/effective/observed X, detectable engine rewrite and consume count. Same-value rewrites cannot be distinguished from retained bytes. F10 includes the compact margin metadata; selected lifetime records live in the session log. If runtime still alternates, correlate these records with F10 before assuming a different restore boundary.

See [backdrop boundary](menu-backdrop.md). Centered4x3 and PreserveMargins share the same full virtual canvas; art extension is independent of anchoring.

## Historical R-GFX5-2 record (superseded where stated above)

# Widescreen UI, independent camera ownership

Original UI authored640x480 is horizontally stretched when its unchanged orthographic matrix feeds16:9. Stock retains that behavior. Centered4x3 requires ConfigVersion1 plus a uniquely verified UI owner, including on an unknown modified image. PreserveMargins additionally retains the exact pristine packet-layout gate. Gameplay FOV is separate. See [compatibility fingerprints](compatibility-fingerprints.md).

Pristine orthographic owner **VA0x00561DF0/RVA0x00161DF0** uses x0..640,y0..480,near-1000/far1000. Its direct D3D SetTransform(PROJECTION) call is **VA0x00561ECD/RVA0x00161ECD**, returning at **VA0x00561ED3/RVA0x00161ED3**. The previous implementation incorrectly used the general/gameplay cached-transform return `0x0013FA75` from `0x0053F9E0`; it is not the UI owner. F10 frame-22056-d1-00007563 shows the actual UI return, feature_mask0 and identical requested/effective matrices: **R-GFX5-1 FAIL_NOT_APPLIED**, not proof that Centered4x3 worked. Ghidra and the current fingerprint independently confirm the corrected owner.

Stock matrix _11=2/640,_22=2/480,_33=-0.0005,_41=_42=-1,_43=0.5,_44=1,all others0. Current caller must be the verified owner AND current matrix must match this orthographic family. Wrong caller, perspective or different ortho stays Stock.

Centered4x3 rewrites only this recognized PROJECTION at the discovered executable return site. Effective viewport aspect a -> width480*a,half=(width-640)/2,bounds[-half,640+half], _11=2/width,_41=-640/width; Y/Z unchanged. Logical GetTransform remains original. Helper bounds aspect1..4;4:3 identity,16:9/16:10/21:9 synthetic tests. No90/45 legacy FOV code. At16:9: virtual853.3333,extra213.3333,half106.6667,_11=0.00234375,_41=-0.75. FPU environment is retained around aspect calculation and rewrite.

SetViewport recomputes a cached UI projection only after a successful validated UI-owner rewrite established live proof, with the logical UI matrix still present. Shape alone cannot establish this proof. A successful new PROJECTION from another owner or successful Reset clears it. Rejected native wide matrix retries logical Stock and disables UI only. Unreviewed state blocks/multiply paths retain existing fallback. Gameplay VFOV/CPU frustum and frontend preview remain separate.

PreserveMargins adds reviewed old left/right anchors to Centered4x3. Its hook, frame edits, 51 rules, restoration and bridge are **unchanged** in this continuation. Earlier oscillation was an **INVALID_TEST_STATE** because the wide projection base never applied. Retest unchanged margins only after Centered4x3 passes; persistent errors then require new packet-timing evidence.

Pristine sort **VA0x00509A21/RVA0x00109A21**, context `d987b8000000d86030d9c0d8c9d9c2d8cb`; overwrite/replay5bytes `FSUB [EAX+0x30]; FLD ST(0)`. Required ECX entity+0x4C packet nonnull,EAX=packet+0x24,mode+0x68=1/2. Static entity+0x50 fallback excluded. Text owner **0x0056D110/RVA0x0016D110**, draw site **0x0056D7BE/RVA0x0016D7BE** confirms packet modes1/2 orthographic; other modes Stock.

Only selected x shifts +/-half,y/z unchanged. [Reference exceptions](third-party-widescreen-analysis.md) are not guessed semantic element labels. Frame-owned edits bounded512, once per storage address, restored at Present/Reset/disable/release only when current XYZ still matches our effective point. Intervening engine writes win. Overflow skips/counts; restoration failure disables UI/logs. No persistent packet identity.

Bridge preserves flags/integer registers/stack/x87/SSE, replays both instructions then resumes pristineVA0x00509A26/RVA0x00109A26. Check exact context/base/SSE; pin DLL; single owner and installing-thread shifts only. Failed install selects Stock UI. Pinned bridge still replays stock safely if hook removal fails. Production bridge tested on synthetic executable memory, never a launched game.

Margin half follows effective viewport/Create/Reset. Packet sorting may precede a new camera viewport: **split-camera per-packet margin aspect remains unproved**, despite correct synthetic full/split/quarter viewport arithmetic. Centered4x3 is initial Stock+ candidate; PreserveMargins separately opt-in. Aspect outside helper bounds stays unchanged; no arbitrary projection guessing.

F10 projection events contain requested/effective payload bits, `widescreen_applied=true`, `widescreen_source=validated_ui_projection_owner` (or its validated cached counterpart), virtual_width, widescreen_extra and center_offset. UI32 is distinct from FOV2, including draw-state differences. UI metadata retains hook/shift/restore-failure/overflow. Native production-wrapper synthetic captures prove the new setter path; **new human appearance is still pending**.
