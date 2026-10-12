Phase: PS2-R5900-REVALIDATION2

Repository: `D:\Game\Master Rallye\master-rallye-re-general`
Branch: `master`
Starting HEAD: `61cb84d5c7f28d3bd88a3f1f9a8ce16d4c178390`
Ending HEAD: final phase commit (reported in closeout)

Canonical ELF SHA256: `b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2`
Ghidra version: 12.1.4
Emotion Engine Reloaded version: 2.1.38
R5900 language: `r5900:LE:32:default`, compiler spec `default`
Rabbitizer version: 1.16.2, `InstrCategory.R5900`
REA PC-provider status: original R5900 ELF rejected by the Windows provider as `capability_unavailable`; direct Ghidra/Rabbitizer path used
PCSX2 Nightly version: 2.9.117.0 installed; no live session run

Original instruction byte checks: 620 frozen + 6,633 fresh Ghidra words, zero mismatches
Independent R5900 decode checks: all 6,633 fresh listing words + 576 compact phase probes valid
Ghidra listing checks: exact EER language and source-file mapping; 1,218 mnemonic aliases/spelling differences, zero word differences

Tree handler: `0x003ae710`, mode 6, bucket 0, alpha test GREATER 64, ABE off, ZMSK 0
Treeblend handler: `0x003ae618`, mode 2, bucket 1, alpha test off, ABE on, ZMSK 1
GS state contract: `(Cs-Cd)*As/128+Cd`; controlled ZTST=GEQUAL; TEX0 MODULATE; triangle strip
GS inherited-state coverage: ZTE, DATE/DATM, FRAME, PABE, TEXA, dynamic TEX0 base/format, upper PRIM/context fields remain inherited or unknown
Effective alpha: texture and vertex alpha are modulated; source vertex color is clamped then half-scaled before VU output. Final live per-pixel `As` is unknown.
Render bucket ordering: ascending bucket order inside one `0x0031cd98` drain; bucket 0 precedes bucket 1 there
Frame-level ordering: unknown; global opaque-before-treeblend ordering not proved
VIF/VU/GIF correlation: CPU producer, upload path, REF/UNPACK/MSCAL and embedded program contract static-confirmed; live micro-RAM residency unknown

PC bush01 correspondence: same geometry hash and VB/IB generations in four supplied mode captures; one target draw each
PILOT1.3 explanation: depth-write-only mode is sufficient for disappearance in the supplied view; no covering draw is identified. Alpha-only mode produces separate white-card artifact.
Confirmed original research errors: none found in the reviewed PS2 material/state claims. PC causal language is narrowed to state sufficiency, not an identified root cause.
Corrections applied: clarified inherited GS fields and queue-order scope; recorded non-white RGB at alpha-zero DXT texels; retained screenshot pairing as correlation only.
Outstanding unknowns: exact PC covering draw/pixel transition, runtime texture format/sample, live PS2 GS/VU state, and PS2 visual parity

PCSX2 runtime: NOT_PERFORMED; targeted capture procedure provided
PC runtime: four supplied sessions, screenshots and F10 frames audited; USER_RUNTIME_OBSERVATION / SCREENSHOT_CORRELATION

Focused tests: 14/14 PASS
Compileall: PASS
Original files unchanged: canonical PS2 hashes rechecked; PC source and assets not modified
Renderer baseline unchanged: yes
PS2 port unchanged by this phase: yes; pre-existing dirty work preserved
Commit: final phase commit (reported in closeout)
Push: no

Overall status: PS2-R5900-REVALIDATION2 STATUS: PARTIAL

## Findings

### Independent executable audit

The ELF is ELF32 little-endian `ET_EXEC`, `EM_MIPS`, entry `0x00100008`, with one file-backed `PT_LOAD` at VA `0x00100000` and file offset `0x1000`. Analysis used the exact EE language rather than generic MIPS. Fresh Ghidra words map back to the canonical file with zero mismatch; Rabbitizer independently accepts all checked words as R5900. See [r5900-function-map.md](r5900-function-map.md) and [elf-functions.json](elf-functions.json).

The executable chain independently checked here is: shader token extraction at `0x00390d98` → material resolve/dispatch at `0x00391690` and registry `0x003a6c58` → `treeblend` registration at `0x003a7468` → callback `0x003ae618` → mode 2/bucket 1 → common GS state production at `0x00312610` → shared cache/queue/packet path. Original France1 material and PSM binding are cross-referenced from TREEBLEND1 and GEOM1 source evidence; this report does not re-decode or modify those formats.

### PS2 alpha, state, and queue facts

PS2 mode 2 disables GS alpha test, enables ABE, uses selectors `A=Cs, B=Cd, C=As, D=Cd, FIX=0`, and masks depth writes with `ZMSK=1`. The equation is `(Cs-Cd)*As/128+Cd`. `ZTE` and other fields remain inherited. The treeblend queue is bucket 1, after bucket 0 only within one `0x0031cd98` drain. No global opaque-before-transparent order is proved.

The source alpha chain is not just the texture alpha: vertex color bytes pass through float/channel conversion and half-scaling, while TEX0 selects MODULATE. Actual runtime texture format, CLUT/TEXA, live source alpha and final GS values for the France1 bush remain uncaptured. The PS2 equation is not numerically equivalent to the conventional D3D8 `SRCALPHA` approximation.

### Four-mode PC evidence

The complete F10 frames contain the same target call and resource generations. The active modes each emit exactly one `ps2_port_draw_identity` event with `TARGET_IDENTITY_CONFIRMED`; native-only `SetRenderState` events surround the draw and return changed values to the frame's captured stock snapshot. Mode 2 does not touch ZWRITE. Mode 3 does not touch alpha-test/blend/factors. The original native draw succeeds once with `D3D_OK` in each capture.

The corresponding screenshots show the Stock bush visible; Mode 1 and Mode 3 largely absent; Mode 2 as bright/white cards. Mode 3 establishes that the Z-write-only override is sufficient for the disappearance in this view. Because the target is early in the frame and many later draws follow, a later overdraw interaction is plausible, not confirmed. No individual draw is identified as the occluder. Mode 2's artifact is separate; stored alpha-zero DXT texels have non-white RGB on average, but this does not establish what the runtime samples or how its texture is interpreted.

### Tooling and boundaries

REA's configured Windows provider does not admit this original PS2 ELF; the direct Ghidra EER and Rabbitizer path is the verified workflow. The saved headless project was reanalyzed successfully in 69 seconds, then the bounded script exported the target windows. EER warned and skipped unmapped DVP overlay sections; no claim here depends on those sections. PCSX2 Nightly 2.9.117 is installed with debugger documentation, but no PS2 runtime session was captured. A targeted non-invasive capture plan is in [pcsx2-capture-plan.md](pcsx2-capture-plan.md).

## A. What was independently established

The canonical R5900 bytes independently support the parser/registration/callback chain and the selected mode-2 GS template. The original ELF words match both the fresh Ghidra listing and the compact Rabbitizer checks. The PC F10 captures independently show that the same buffer-backed bush draw executes once in each mode and that each temporary native-state write is restored.

## B. What earlier research got right

TREEBLEND1's category mapping, mode 2/bucket 1 distinction, GS `As/128` equation, ZMSK behavior and limited per-drain queue-order conclusion survived this independent byte audit. The France1 PSM-to-visual-group identity is reused from the existing byte-backed PSM research rather than reasserted from a texture-name match.

## C. Confirmed errors and corrections

No prior PS2 material or GS claim reviewed here was contradicted by the independent audit. The PC evidence narrows the old causal uncertainty: `ZWRITEENABLE=FALSE` by itself is sufficient for the observed disappearance, but no specific occluder is proved. Source DXT alpha-zero RGB is not white on average, so that simple explanation for Mode 2 is ruled out; runtime sampling and conversion remain open. See [corrections.md](corrections.md).

## D. What remains unknown

The actual France1 live GS descriptor, sampled source alpha, TEX0/TEXA/CLUT values, VU residency, whole-frame PS2 scheduling, per-pixel PC overdraw, and PS2 visual parity remain unknown. The exact session-to-screenshot mapping is ordinal/timestamp-supported, not encoded in the JPEG metadata.

## E. What the PS2 likely does differently

The proven contract uses a distinct treeblend material mode and GS alpha equation, masks depth writes, and queues this category in bucket 1 within a shared drain. Those are concrete differences from the PC stock alpha-test/cutout state. Whether the original frame's broader ordering or live inherited state explains its appearance cannot be concluded from this static chain.

## F. Implications for the PC bush pilot

Keep the four current diagnostic modes isolated and reversible. Do not choose a permanent depth policy based on visual resemblance: Mode 3 demonstrates a failure mode, not the PS2 fix. Do not infer the white-card cause from stored alpha alone. First capture target color/depth contribution and subsequent overlap in a single PC frame; only then decide whether a renderer or texture experiment is warranted.

## G. Next experiment

Perform the bounded PC per-pixel overdraw capture in [next.md](next.md), using the same France1 target geometry and resource generations. Record the target's contribution immediately after its draw and after candidate later draws. This is the single recommended next step; no PC or PS2 implementation change is proposed here.

## Acceptance matrix

| Gate | Status | Evidence |
|---|---|---|
| Canonical input identity and immutability | PASS | Exact hashes rechecked |
| Direct R5900 analysis path | PASS | Explicit Ghidra EER language + Rabbitizer; byte match |
| Material callback/GS contract | PASS (static) | Original instructions, registration xrefs, prior PSM bytes |
| Alpha source through final live GS value | PARTIAL | Static input path known; runtime texture/CLUT/TEXA/As absent |
| Queue ordering | PARTIAL | Ascending buckets inside one drain only |
| PC classifier same target in modes 0–3 | PASS for supplied captures | Geometry hash and VB/IB generation/revision match |
| PC native draw/state restore | PASS for supplied captures | One successful draw; exact changed-state restoration |
| Root cause of PC disappearance | PARTIAL | ZWRITE-only state is sufficient; covering draw/pixel transition unknown |
| Visual screenshot comparison | PARTIAL | User observations paired by timestamps/order, not embedded mode metadata |
| PS2 live VU residency / runtime parity | NOT PERFORMED | No PCSX2 runtime capture |
| Scope and input preservation | PASS | No renderer, port, Course SDK or game input changes |

## Validation commands

See [validation.md](validation.md) and [command-log.md](command-log.md) for exact invocations. The phase-specific unittest suite has 14 tests; its final result is 14/14 PASS. `compileall` and `git diff --check` both pass.

## One next step

Run the bounded PC per-pixel overdraw capture in [next.md](next.md). Do not change the renderer or PS2 state policy until the target contribution and later pixel/depth transitions are measured.
