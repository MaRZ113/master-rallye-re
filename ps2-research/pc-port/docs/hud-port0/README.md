# HUD-PORT0 — PS2 HUD feasibility

**HUD_PS2_CONTRACT: PARTIAL. HUD_PC_INTEGRATION_FEASIBILITY: PARTIAL.**
This is research/design only. No HUD feature, configuration key, replacement
texture, hook, staged patch or DLL was implemented by this pass.

The highest-value difference is the PS2's procedural rectangular course minimap,
compared with the PC's circular GPS display. It needs a verified live vehicle,
route and progress feed; exchanging the GPS texture cannot reproduce it.
The smallest first implementation is a **static PS2 tachometer plate**, retaining
the original PC needle, speed and gear updates. Its immediate gate is a semantic
mapping of `SpeedDial` to current native packet/draw identities.

Original assets and packet ownership are concrete, but the current 32 captured
PC UI identities are all semantically `unmapped`. A texture, draw ordinal,
FVF or common UI callsite is insufficient to replace a widget safely.

| Subject | Evidence / result |
|---|---|
| Source/capture inventory | [source-evidence.json](source-evidence.json), generated read-only by [review_evidence.py](review_evidence.py) |
| Feature comparison | [feature-matrix.md](feature-matrix.md) |
| Original PS2 owner/render contract | [ps2-contract.md](ps2-contract.md) |
| Current PC native UI and performance constraints | [pc-integration.md](pc-integration.md) |
| First bounded opt-in proposal | [pilot-proposal.md](pilot-proposal.md) |
| Pause-menu differences | [pause-menu.md](pause-menu.md) |
| Verification / dependency limits | [validation.md](validation.md) |

The original renderer remains the committed `0bddf7c7bc5e95831f98714ff6231da05ab073ea`
baseline, renderer tree `e33386bcf682db6983380c499e4928726c758fe0`. In particular,
the HUD race-context cache stays once per D3D frame, while the strict per-draw
Clean View/Freecam checks remain intact. The user reports that the previous HUD
and menu lag fixes work (`USER_RUNTIME_OBSERVATION`); this pass does not repeat
that gameplay test or weaken those checks.

Historical UI1/UI2 reports are reused as evidence with their limitations. Six
direct-call words and the 15-word matrix kernel were freshly checked with
Rabbitizer's explicit R5900 category. The whole historical HUD owner suite was
not independently re-decompiled with Emotion Engine Reloaded in this phase.

