# R5V-E0.1b findings

## Scope and E0.1a closeout

R5V-E0.1a is closed by commit `ccfd29d` (`research: record R5V-E0.1a HUD icon runtime proof`). The owner reported FULL PASS: ID25 with SmallCarSheet selector 29 displays Forklift frame 29 in the top-left 1P icon and Race Results; the bottom progress marker remains aquamarine and Trooper gameplay is unchanged.

The stats-only candidate received owner-reported **FULL PASS** after the static phase commit. The bars displayed the independent values `(3,4,6,10)` while ID25 remained Trooper-configured. No progress-colour candidate was produced because its producer and participant-specific control point remain unresolved.

## Findings

- `FUN_004A74A0` (retail `0x004A74A0`) formats `Race/Car%d/Colour` using its HUD display-slot field at `this+0x18`, reads a four-component property, stores the components at `this+0x3C..+0x48`, and copies them to the marker render object. The ghost path overrides the tint to white with alpha 0.5. **RAW_GHIDRA_SUPPORTED** by assembly/P-code and direct string xref.
- This proves an RGBA-like Vector4 tint consumer, but not who writes the race property or what Car0 means. The only literal xref for `Race/Car%d/Colour` is the consumer. `/Colour` is registered in the HUD schema at `FUN_004ABCE0`; that registration is not a writer. No matching `Race/CarN/Colour` values were found in the inspected retail RaceTest XML. Classification stays **UNKNOWN** upstream.
- The previous E0.1a runtime selector diagnostic established that changing VehicleRecord[25] `+0x1C` does not change the bottom marker tint. This separates that tint from the SmallCarSheet channel, but does not establish whether colour follows player, participant, controller, vehicle, or another identity.
- `FUN_004819B0` directly loads all four selected-record integers and writes the matching `Frontend/VehicleSelect/*` properties. `VehicleSelect.xml` binds each bar independently to the corresponding property. **RAW_GHIDRA_SUPPORTED** plus static scene evidence.
- The stats-only ID25 candidate sets `(Speed, Acceleration, Handling, Endurance)=(3,4,6,10)`. It is based on the runtime-confirmed Trooper + SmallCarSheet 29 profile. Compared with that baseline, exactly four immediate bytes change. The owner reports the four bars visibly followed the diagnostic values; the candidate retains Trooper's runtime model/configuration. **Runtime-confirmed presentation control.**

## Status

| Diagnostic | Candidate | Static status | Runtime status |
|---|---|---|---|
| Race progress tint | None | Consumer proven; producer/control unresolved | BLOCKED |
| Vehicle Select stats | `research-output/r5v_e0_1b/runtime-test/stats/MRallye_slot25_trooper_stats_test.exe` | Four independent record fields proven; diff isolated | FULL PASS |

R5V-F remains **BLOCKED** on the race colour producer/semantics. The unresolved edge is specifically `race setup/input -> Race/Car0/Colour`, including whether that value is tied to Player1 or vehicle identity.

No original executable or game data was modified. No color candidate, registry extension, asset, or track work was created.
