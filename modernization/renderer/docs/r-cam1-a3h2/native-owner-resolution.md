# R-CAM1-A3h.2 — Native UI owner resolution

Status: **BLOCKED_ON_NATIVE_UI_OWNER_MAPPING**. No production visual suppression was added. The evidence proves a complete UI draw correlation and separate source-level HUD/pause content, but it does not prove the runtime Egg owner for any captured entity/packet.

## Build and evidence boundary

- Retail executable: `D:\Game\Master Rallye Pristine\MRallye.exe`, SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
- Static analysis used the existing read-only Ghidra project for that exact executable, Ghidra `12.1.4_PUBLIC` from `D:\Game\Master Rallye\_reverse-tools\ghidra-bridge-main`, and `ghidra_ai_bridge.export_single_function`. Query transactions were rolled back and the project/program were not saved.
- Runtime inputs were the A3h.1 session and its two complete F10 frames in `D:\Game\Master Rallye Pristine\MRRRenderer\logs`. The checked-in A3h.1 analyzer was rerun against those files; its result is retained only in ignored `.analysis` scratch.
- The source content check used `D:\Game\Master Rallye Pristine\Data.sma_unpacked\DataScene\Hud\Hud0.xml` (SHA256 `91616CAA529FB4762E8E263F58BFE0F35EE5AEBF127E8BA2FC3014A677EA4DBF`). No proprietary binary, source asset, or raw capture was copied into the repository.

## What is confirmed

| Evidence | Result | Grade |
| --- | --- | --- |
| A3h.1 normal frame | 268 UI draw records, 32 entity/packet identities, complete coverage, no drops/overflow | `CONFIRMED_BY_RUNTIME` |
| A3h.1 paused frame | 474 UI draw records, 35 identities, complete coverage, no drops/overflow | `CONFIRMED_BY_RUNTIME` |
| Cross-frame identity comparison | 32 identities shared unchanged; 3 pause-frame-only identities account for 206 additional draws; no normal-only identities | `CONFIRMED_BY_RUNTIME` |
| Typed pause state | `Race/PauseMenu/Enabled` is false in the normal capture and true in the paused capture; read-only diagnostic corroboration | `CONFIRMED_BY_RUNTIME` |
| Draw boundary | The records correlate the native entity/packet consumer scope to the final UI `DrawPrimitive` at VA `0x0056D7C4` / RVA `0x0016D7C4`; all 742 records still have semantic owner `unmapped` | `CONFIRMED_BY_RUNTIME` |
| Source scene | Retail unpacked `Hud0.xml` has separate `PauseMenuTiles` (`enUITileBox`) and `PauseMenuChooser` (whose AI data names `gaFrontendPauseMenuAI` and references `PauseMenuTiles`), plus separate HUD Eggs such as `SpeedDial`, `GPSNeedle`, `GameRank`, timers, wrong-way, and progress groups | `CONFIRMED_BY_EXISTING_RESEARCH` + exact source hash above |

The three paused-only raw pointers remain capture-local observations, not shipping identities. Their roles are not known. Likewise, the shared 32 are not proven to be exclusively HUD; some may be other race UI. The fact that the pause bool changed is not an owner classifier.

## Exact native path inspected

- `DrawTextPacket` is VA `0x0056D110` / RVA `0x0016D110`. Its known caller at VA `0x0056BA70` consumes an entity whose packet pointer is read from `entity+0x4C`; when `entity+0x50` is non-null it first calls VA `0x0056BBC0` to process the associated render/model object. These fields lead to packet and rendering data, not to a proven Egg name or semantic owner.
- A second manager route at VA `0x0056CD80` iterates its own pointer array `[manager+0x94, manager+0x98)` and calls `0x0056D110` for each entry. The manager vtable slice at data VA `0x006922C8..0x0069230C` confirms these are methods of the same renderer service. It contains no source Egg identity.
- `SortPerCamera` at VA `0x00509970` follows `entity+0x50` to transform-origin values (including offsets `+0x4C..+0x54`) for distance ordering. This is evidence against reinterpreting `entity+0x50` as a generic parent pointer. The historical exclusion of a static `entity+0x50` fallback remains correct.
- The inspected consumer and manager methods expose a render entity, packet, geometry/resource object and renderer-list membership. Neither provides a demonstrated edge to an instantiated scene Egg, parent group, source `Name`, or AI class. The scene/Egg creation-registration handoff that would associate those domains has not yet been located.

Therefore the missing edge is specifically:

```text
Hud0 Egg construction/registration (source Name + instance lifetime)
    -> native scene/Egg owner instance
    -> submitted UI entity / packet consumed at 0x0056D110
```

The known draw path is sufficiently narrow for eventual suppression, but classifying from it today would require guessing. No role table can truthfully assign `RaceHud`, `PauseOverlay`, or `Other` to the captured runtime entities.

## One targeted next observation

Do one bounded, read-only creation-lifetime trace at the native scene/Egg registration handoff—not another ordinary/paused F10 comparison. First resolve that handoff in the exact retail image by following the parser/constructor path that consumes an Egg's `Name`/AI metadata from the loaded scene. At the point where the parsed Egg or its owner is registered, record only:

1. validated source Egg `Name` and instantiated runtime class/AI class;
2. owner pointer plus a creation/lifecycle generation (never pointer alone);
3. the submitted UI entity and packet pointers created/attached by that owner;
4. whether that exact entity/packet later enters `0x0056D110` and reaches `0x0056D7C4`.

Limit names to the known `Hud0` pause Eggs and representative HUD Eggs (`PauseMenuTiles`, `PauseMenuChooser`, `SpeedDial`, `GPSNeedle`, rank/timer/progress owners) plus their directly attached visual children. Keep the trace read-only and bounded to creation/registration events; do not log arbitrary memory strings or traverse guessed offsets. A successful mapping must show the same lifetime-qualified entity/packet on the registration side and consumer side. This single instrumented run can include normal race and pause, but it is not a repeat of A3h.1: the new observation is the source-owner-to-native-instance edge.

If the exact registration handoff cannot be identified statically, the next task is to isolate that callsite in the scene parser/constructor path before asking for runtime evidence. Do not add a speculative D3D classifier in the meantime.

## Implementation decision

No `UiVisualRole` production classifier or hide toggle was added. This preserves fail-open behavior and avoids hiding unrelated FVF `0x142` draws. Existing UI entity/packet observation, Freecam, pause handling, camera behavior, and accepted UI correction code are untouched by this A3h.2 investigation. The next implementation gate is a validated Egg/owner-to-entity relationship with lifecycle/ABA protection; only then should independent HUD and pause visibility be added at the verified consumer/draw boundary.

## Reproducible analyzer result

The offline analyzer was run with:

```powershell
python modernization/renderer/tools/analyze_ui_ownership.py `
  --session "D:\Game\Master Rallye Pristine\MRRRenderer\logs\session-20261011-010333-37156.jsonl" `
  --normal-frame "D:\Game\Master Rallye Pristine\MRRRenderer\logs\frame-before-pause.jsonl" `
  --paused-frame "D:\Game\Master Rallye Pristine\MRRRenderer\logs\frame-pause.jsonl"
```

It returned `READY_FOR_A3H_ANALYSIS`, `semantic_pause_ownership_proven=false`, 742 unknown draw records, 32 shared identities, and 3 paused-only identities. `READY_FOR_A3H_ANALYSIS` means the capture is valid input; it does not mean ownership is resolved.
