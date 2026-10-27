# Master Rallye Observatory v0.3.0-beta

## What's new

- **Relocatable Broker/Debug layout.** Observatory no longer depends on fixed retail addresses. A new locator finds every address it needs from the code itself: the formatted logger and its active Debug-sink global, the Debug-sink constructor and vtable, the Broker Editor command dispatcher and its Dump case, the Broker singleton accessor and manager global, the native Dump walker, the main-window command switch and its `0x27` (Broker Editor) and `0x30` (Flow Builder) cases. Shifted code, grown sections, localized and other retail-family builds now connect.
- **Live memory is the authority.** For non-pristine builds every capability is re-located in the running process image and must agree with the profile resolved from disk. In-memory patches are judged by what actually executes.
- **Capabilities are independent.** Passive Broker read needs only the Debug sink. Native Dump also needs the dispatcher case 2 → accessor → walker route. Opening Broker Editor needs the main switch case `0x27` → Broker opener. A missing item disables only what consumes it.
- **Native Dump on modified builds.** The exact-pristine requirement for native Dump is gone. The walker is classified as stock, relocated stock (address-normalized identity), an audited hardened variant (R-AI1 inline, two-stub NULL guard, J.1), or unknown. **Unknown asks for confirmation** in the menu, or `--allow-unknown-walker` for scripted use; it is recorded in the capture as `native_dump_verification=unknown_walker_confirmed`.
- **Window recognition by command IDs.** The main window is recognized by the native Game menu's Reset (`0x32`) and Exit (`0x2F`) command IDs instead of English labels and an exact item count. Broker Editor is recognized by a submenu that holds the Dump item with local ID 2. Without a native menu, a located build accepts the process's single visible `Master Rallye` window.
- **Any executable name.** `MRallye_merc.exe`, renamed copies and the configured executable are discovered; the process main module is taken from the module snapshot instead of by basename.
- **`resolve` command.** `mr_observe.py resolve PATH` (or `resolve PID`) prints the located addresses, which ones moved from retail, missing items with the reason, capabilities and the walker variant. With a PID it also verifies each capability in live memory.

## Compatibility and safety

Exact pristine retail keeps its runtime-confirmed fixed-address path, including the J.1 live-memory walker checks. Observatory stays read-only: process access is query/read, and the only commands remain the two reviewed tool openers and Broker Editor's original Debug → Dump (local ID 2), sent once. Demo builds are not supported: their logger and command switch differ.

## Limitations

- New located profiles are statically verified against all locally available retail-family builds; a live capture on each new build is still a runtime validation step.
- A Dump through an unknown or stock walker after Results can crash the game (NULL StringList). Capture during an active race.
- No game executable, assets, saves, raw captures, screenshots, or profile cache is included.
