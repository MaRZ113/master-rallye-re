# R-DEV1.2 — embedded editor lifecycle

Status: **static closeout complete for retail; cross-build evidence supports the same flag-driven implementation in pristine 9.3.1 and 9.10.0.** No runtime experiment was performed.

## Correction to R-DEV1.1

R-DEV1.1 said that retail application bytes `+0x44..+0x47` had no recovered producer. That statement was wrong. `005AF970` clears and conditionally sets all four bytes after checking and closing the corresponding editor windows. `005AF9F0` consumes and clears them. The earlier text is retained as history; this document supersedes its “no producer” conclusion.

## Retail object and byte mapping

The `this` pointer passed to `005AF970`/`005AF9F0` is the retail application object constructed by `005AF5C0` in a `0x4c` allocation. The partial member map below is based on the function arguments and opener calls, not on speculative class names.

| Application offset | Type | Meaning | Evidence |
|---:|---|---|---|
| `+0x10` | pointer | Broker Editor owner | Snapshot predicate/close; restore opener `0065E990` |
| `+0x24` | pointer | Marker Editor owner | Snapshot predicate/close; restore opener `0065B870` |
| `+0x28` | pointer | Egg Editor owner | Snapshot predicate/close; restore opener `00657FD0` |
| `+0x2c` | pointer | Particle Editor owner | Snapshot predicate/close; restore opener `006557C0` |
| `+0x38` | pointer | shared application/window context passed to tool openers | Restore path; exact class/layout remains partial |
| `+0x44` | byte | Marker was open before snapshot | predicate `0065B860`, close `0065B820` |
| `+0x45` | byte | Particle was open before snapshot | predicate `006557B0`, close `00655700` |
| `+0x46` | byte | Broker was open before snapshot | predicate `0065E980`, close `0065E960` |
| `+0x47` | byte | Egg was open before snapshot | predicate `00657FC0`, close `00657F80` |

The four bytes are independent zero/one flags, not a count, list, or bitmask. The predicates inspect the corresponding editor's window-wrapper HWND. Consequently the snapshot remembers only windows that are open at that instant.

## Snapshot and close: `005AF970`

Ghidra 12.1.4 decompilation and instruction review agree on this order:

1. Clear all four pending bytes.
2. Check Marker, Particle, Broker, and Egg in that order.
3. For each editor whose predicate reports an open HWND, call that editor's close/reset path and set its corresponding byte to `1`.
4. Return without a status value.

The close calls do not all have identical effects:

| Editor | Close/reset | Static side effects observed |
|---|---:|---|
| Marker | `0065B820` | closes its helper/window wrappers and runs owner cleanup `0065AEA0`, which decrements `Editing/EditorsOpen` and restores saved editor-view state |
| Particle | `00655700` | closes its helper/window wrappers and resets Particle-owned flags/state; no direct `Editing/EditorsOpen` updater call is present |
| Broker | `0065E960` | closes/releases the Broker Editor window wrapper; no `Editing/EditorsOpen` update or broker-value setter is on this close path |
| Egg | `00657F80` | closes nested view helpers and runs state cleanup `00657630`, which decrements `Editing/EditorsOpen` and restores saved editor-view state |

For Marker, Particle, and Egg, the paths release or reset editor-owned view/model helpers, so “only the HWND is destroyed” is false. The exact amount of editor selection/model state rebuilt on a later open is not established. Broker close is narrower in the observed path; no broker-value mutation or sentinel-list removal was found.

## Restore: `005AF9F0`

The restore helper reads the bytes in the same order: Marker, Particle, Broker, Egg. For each nonzero byte it obtains the application singleton at `DAT_006FDFE8`; if absent, it allocates `0x4c` bytes and constructs an application object with `005AF5C0`. It then passes that object's `+0x38` context to the corresponding editor opener.

| Flag | Reopen function |
|---:|---:|
| `+0x44` | `0065B870` Marker |
| `+0x45` | `006557C0` Particle |
| `+0x46` | `0065E990` Broker |
| `+0x47` | `00657FD0` Egg |

After all four tests, `005AF9F0` clears all four bytes unconditionally. It has no per-opener success check, rollback, or saved-window-state payload. The helper preserves **was open**, not a separately recorded selection, scroll position, selected broker value, or geometry. An opener may restore/reconstruct some state from its owner object, but the flags do not encode it.

The allocation-failure branch is not safely handled before later code reads the application context. This is static error-path evidence, not an observed runtime failure.

## What triggers the snapshot

The snapshot is used by multiple retail state-changing paths, not only by application shutdown. Ghidra xrefs and decompilation identify these direct callers:

| Caller | Evidence-backed operation | Snapshot placement |
|---:|---|---|
| `005B14D0` | Open Game: validates a selected file under `DataGame/` and requires XML | after successful path validation, before storing the chosen path and invoking Game-state/broker operations |
| `005B1370` case `0x32` | Reset Game: asks for confirmation, then enters Game reset/configuration operations | after confirmation, before reset calls |
| `005B2260` | Open Scene: validates a selected file under `DataScene/` and requires XML | after successful path validation, before storing the path and applying scene-load settings/operations |
| `005B1F80` case `0x50` | Reset Scene: asks for confirmation | after confirmation, before reset calls |
| `005B1F80` cases `0x53` and `0x54` | additional scene reload/reset-like operations | immediately before their scene operation; exact user-visible labels are not assigned here |
| `005B2920` | wrapper calls a reset-like scene operation with argument `1` | contains the snapshot, but no direct code caller was recovered |
| `005AF920` | application manager/window teardown, called by entry dispatcher `006766A0` after the frame loop `005AFE30` | during shutdown cleanup |

This establishes that the architectural trigger includes **Game or Scene open/reset/reinitialization**, with a separate shutdown use. It is not evidence for a generic “XML load” rule beyond the explicit Game/Scene paths above.

The open/reset operation itself does not call `005AF9F0` as a direct epilogue. The sole direct call to `005AF9F0` is from `005AFAF0`. That callback first restores the pending editors, then calls USER32 `SetForegroundWindow` on the main-window handle. This is strong evidence for **deferred restoration during an application foreground/focus callback**, but the exact Windows message/interface that dispatches the callback and whether every Game/Scene operation guarantees that callback are not proven by the static direct-call graph. Therefore the complete sequence is:

```text
Game/Scene open, reset, or reinitialization path
    → 005AF970 snapshots open editors and closes their view/window state
    → Game/Scene state operation proceeds
    → application foreground callback 005AFAF0
    → 005AF9F0 reopens flagged editors
    → SetForegroundWindow(main HWND)
```

The first two arrows are **CONFIRMED_BY_EXE** for the listed call paths. The deferred foreground restoration relationship is **CONFIRMED_BY_EXE** at the callback body and **STRONG_HYPOTHESIS** as the normal post-operation pairing; a runtime trace is still required to prove timing and guarantee. Do not describe this as a scene reload alone or claim selection/scroll restoration.

## `Editing/EditorsOpen`

Retail helpers `0066C180` and `0066C380` store an integer broker value named `Editing/EditorsOpen`:

- Increment: if the value is missing, writes integer `1`; otherwise reads it and writes `value + 1`.
- Decrement: reads it, computes `value - 1`, clamps to zero, and writes the integer.
- Both helpers also preserve/restore editor camera/view vectors and related state.
- Direct owner-level callers are Marker initialization `0065ACD0` / cleanup `0065AEA0`, and Egg initialization `006573B0` / cleanup `00657630`.
- Particle, Broker, and Flow Builder do not call these updater functions directly.

The value is therefore an integer count of active Marker/Egg editing-view contexts, with camera/view bookkeeping. It is not a boolean for every embedded tool window and is not the four-byte pending-open state. This corrects the tentative owner attribution in the analysis notes: the counter xrefs `0065ACD0`/`0065AEA0` sit on the Marker paths, while `006573B0`/`00657630` sit on the Egg paths. No new runtime value was read or changed in this phase.

## Cross-build check

| Build | Snapshot | Restore | Callback / evidence | Result |
|---|---:|---:|---|---|
| 8.4.1 pristine | not matched | not matched | Earlier helper pair `00550A90` / `00550C90` exists, but the retail `+0x44..+0x47` application layout must not be projected onto 8.4.1. The nearby 8.4.1 `+0x44..+0x47` references occur in a different per-object update function. | **UNKNOWN** whether the same window-preservation architecture exists |
| 9.3.1 pristine | `005FF080` | `005FF100` | `005FF200` is a `this`-adjusting tail thunk to restore; this thunk does not itself call `SetForegroundWindow` | same snapshot/restore state **CONFIRMED_BY_EXE** |
| 9.10.0 pristine | `006309C0` | `00630A40` | `00630B40` calls restore then USER32 `SetForegroundWindow` | same architecture **CONFIRMED_BY_EXE** |
| retail pristine | `005AF970` | `005AF9F0` | `005AFAF0` calls restore then USER32 `SetForegroundWindow` | same architecture **CONFIRMED_BY_EXE** |

The 9.3.1/9.10.0/retail code has the same four-byte flag mapping and editor order. No old research-patched demo is used as authority for this comparison. The 8.4.1 counter helpers alone do not prove the newer snapshot/restore mechanism.

## Evidence and limitations

- **CONFIRMED_BY_CORPUS:** all four input hashes match the pristine identities recorded in `research/corpus/executable-provenance.md`.
- **CONFIRMED_BY_EXE:** retail functions and cross-reference graph were analyzed in an isolated Ghidra 12.1.4 project; selected assembly was checked directly. Pristine 9.3.1 was also imported into a separate isolated Ghidra 12.1.4 project. Pristine 9.10.0 and 8.4.1 byte/call-pattern checks were made against the verified corpus files.
- **CONFIRMED_BY_RUNTIME:** no new runtime observations.
- Ghidra scratch projects and exports live only under ignored `research-output/r-dev1_2/`; no raw Ghidra database is committed.
- The exact callback dispatch contract, whether it is invoked after every state operation, and retention of editor-specific selection/model data remain unresolved.
