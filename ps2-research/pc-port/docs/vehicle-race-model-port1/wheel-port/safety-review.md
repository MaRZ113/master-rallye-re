# Focused native wheel/trim safety review

Scope: read-only review of `wheel_model_native.hpp`, role-2 `FrontendModel` asset/resource handling, race trim submission changes and staged Reset integration. No source edits or builds performed by this reviewer.

Result: no new release-blocking state-restoration or resource-lifetime flaw found in the reviewed implementation. This is source review, not evidence that private wheel geometry has rendered correctly in the game.

## Confirmed source safeguards

- Wheel admission requires a valid current race certificate, exactly one native participant, the currently certified chassis already drawn in the same frame, and matching race generation and owner lifetime. An approximate spatial check alone never admits a wheel.
- The current native caller/queue must resolve an owner whose model has exactly four leaf submissions. The bound native VB/IB must match the current source containers after proxy unwrapping; descriptor ranges, FVF/stride, actual effective bindings, buffer generations and upload revisions are checked.
- All four source geometry signatures must complete a coherent owner/world warmup before next-frame replacement. A changed source cache invalidates certification; duplicates, missing records, owner overflow, upload loss and unknown damage geometry fail closed.
- Each replacement retains that wheel's native WORLD. It does not copy the chassis pose, implement wheel physics, or alter steering/suspension/spin state. World finiteness, unit axis lengths and distance to the current chassis are admission guards, not a reconstructed physics contract.
- Private role-2 data is locked by exact size/hash and geometry counts. The four-range resource preserves the independently proved 252-face source union. Texture creation is owned and partial failures clean up and disable retries.
- The existing narrow transaction captures native state, marks changed state before each setter, restores native state and effective shadow, and retains pending state for repair. `DrawPrimitiveUP` stream invalidation is accounted for. Actual private draw HRESULT is returned; failed restoration is logged and disables further replacement rather than claiming Stock equivalence.
- Wheel pending transactions are included in the real Reset gate and resource-reset path. `reset()` does not release textures while a transaction is pending. Existing internal window-mode echo handling remains upstream of real Reset processing.
- Wheel shader secondary sources are explicit: verified authored rubber for the first three ranges and the existing ready Mode-4 mixed capture for the chrome range. No texture-name-only or ordinal-only admission is introduced.

## Bounded limitations and required runtime checks

1. The initial policy deliberately excludes races with additional native participants. Do not describe it as multiplayer/opponent coverage.
2. Current four-wheel owner evidence, native steering/spin continuity, suspension pose, menu/race transitions, restart, MSAA and real Reset need user runtime verification on the new DLL. A source-corpus match and synthetic tests do not establish these observations.
3. CULL_NONE and inherited fixed-function lighting remain accepted diagnostic approximations, not PS2 pixel parity. Unit axis lengths are not a general orthogonality proof; the matrices remain original native engine matrices and no fitted correction is applied.
4. Wheel owner slots are bounded to four for a race lifetime. Additional owners fail closed. This may cause a safe Stock fallback after unexpected owner recreation; it must not trigger widening admission.
5. The new race trim path uses explicit source face subsets. `trim_[4]` / `kTrim15Pc17` and `kTrim18Pc17` are not submitted by this implementation. Any such unmatched or mixed-source surfaces must remain explicitly Stock/unresolved in the coverage matrix.
6. Damage fallback is based on current geometry identity and upload validation. Unsupported damaged models should remain Stock; do not claim comprehensive private damaged geometry support.

Recommended release statement: IMPLEMENTED_PENDING_USER_RUNTIME for the separate wheel and trim additions, with existing user-confirmed chassis and glass retained as earlier evidence.
