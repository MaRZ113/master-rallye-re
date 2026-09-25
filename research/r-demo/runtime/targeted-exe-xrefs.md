# Targeted demo EXE anchors from Debug texture strings

This is a bounded static PE32/disassembly audit of unchanged `MRallye.exe` files. Virtual addresses use the PE image base `0x400000`. The addresses are executable xrefs, not runtime traces. Only the string-anchored texture functions and immediate callers were inspected.

| Build | `Loaded cached DX texture: [%s]` file offset / VA | Direct string xref | Function containing xref | Direct caller |
|---|---|---|---|---|
| demo-8.4.1 | `0x1F4A98` / `0x5F4A98` | `0x522093` push | `0x521FD0` | `0x521718` |
| demo-9.3.1 | `0x2738CC` / `0x6738CC` | `0x520623` push | `0x520560` | `0x51FCA8` |

In demo 8.4.1, the caller invokes `0x521D20` at `0x52170A`; if it returns null, it invokes `0x521FD0` at `0x521718`. The analogous 9.3.1 pair is `0x5202B0` at `0x51FC9A`, then `0x520560` at `0x51FCA8` on null. The first 8.4.1 function visibly constructs `.gxi` and `.dxt` path strings (`0x521D54`, `0x521D89`), uses exact log literals `Reading GXI: [%s]`, `Saved cached texture: [%s]`, `Cached texture out of date or missing.`, and has a conditional save-looking branch around `0x521EE1–0x521F15`. The second constructs `.dxt` (`0x522000`) and logs `Loaded cached DX texture` after a non-null load branch (`0x522055–0x522098`). The corresponding 9.3.1 EXE contains the same named literals and symmetric immediate caller structure. This is **CONFIRMED_BY_EXE** evidence of a GXI/DXT source/cache path. R-DEMO2.1 ProcMon confirms the tested 9.3.1 GXI→DXT miss and generated-file IO; it is a separate trace from the 8.4.1 DXT byte-identity result. Per-resource file access for the 8.4.1 car/complete/wheel visual matrix remains untested. See `research/r-demo2/runtime/procmon-findings.md`.

The 8.4.1 logger function called by these sites is `0x47E0F0`. It formats text and dispatches through a sink object. One installed sink method at `0x4EB8C0` calls imported `OutputDebugStringA` (`0x4EB8C9`, IAT `0x5CF1D0`) and then forwards the string through a second virtual sink; its vtable is at `0x5D232C` and is conditionally installed at `0x4EB91F–0x4EB935`. This is **CONFIRMED_BY_EXE** for the code path, not proof that every Debug line reaches both destinations in a live session. Both demos import `CreateFileA/W`, `ReadFile`, `WriteFile`, `GetStdHandle`, `OutputDebugStringA`, `CreateWindowExA`, and `SendMessageA`; their presence alone does not identify the called file API for this specific texture.

Historical target completed for the defined 9.3.1 GXI→DXT miss: ProcMon records the event sequence, while the 8.4.1 DebugView capture establishes its own cooker messages. No single cross-build trace is implied. No EXE was patched.
