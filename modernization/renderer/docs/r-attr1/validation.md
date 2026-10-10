# R-ATTR1 validation — runtime pending

**READY_FOR_IN_GAME_VALIDATION**. No game was launched, DLL deployed, or
Broker variables captured by the agent. Repeated in-game Restart and legitimate
idle Attract require separate human results.

Executed on the pristine SHA-locked retail image:

- Read-only PE/instruction inspector PASS; full 374-byte Loading context and
  complete factory/thunk contexts match the executable.
- Ghidra 12.1.4 native emulation: 60 Loading cases PASS (six consecutive counter
  values, five media-stat/size outcomes, original versus guard) and six separate
  idle timer branch cases PASS. The guarded Loading path skips only the obsolete
  failure assignment. Native idle expiration still sets Attract and requests
  the demo transition. Emulation stubs external services; it is not gameplay.
- Production native PatchMemory/ThreadGate suite PASS: five-byte boundary and
  signed JMP target, startup admission, all 374 individual context mutations,
  unsupported host, quiescence rejection, phase mutation, one-time entry,
  ownership, readback/cache/protection, partial-write rollback and unverified
  rollback rejection. The real OS thread gate still needs live admission trace.
- All 12 Win32 Release CTest suites PASS, 7.17 s, including unchanged race epoch,
  camera probe, COM/forwarding, renderer/display/UI/FOV/reflection contracts.
- Renderer Python: 145/145 PASS, 109.749 s.
- Root synthetic: 630/630 PASS, 10.413 s; 17 Broker opener cases are included.
- Compileall for renderer and runtime tools, git diff-check: PASS.
- PE verifier PASS: PE32/I386, direct Direct3DCreate8 ordinal 5,
  ValidatePixelShader ordinal 2, ValidateVertexShader ordinal 3; only bcrypt,
  USER32 and KERNEL32 imports, no recursive d3d8 import or delay import.

Combined candidate `.analysis/handoff/r-obs1-attr1/d3d8.dll`:
1,683,968 bytes, SHA256
`989c986e0a010cbe98837dccb5fdf461c70626a6d42d860cb145c0620f7d114a`.
Built with the canonical `tools/build.py`, Visual Studio 18 2026, Win32 Release.

The first combined Python run found two deferred-window-telemetry regressions;
see the R-OBS1 validation follow-up. Both were repaired and the complete suite
rerun. No old assertions were weakened to hide lost events.

**R-OBS1 remains BLOCKED_ON_BROKER_OPEN_INTEROPERABILITY** until the reported
Windowed stall is isolated and regular Windowed/Borderless both open Broker and
create fresh valid Dumps. Passing R-ATTR1 static tests cannot change that status.

Human PASS requires `legacy_loading_attract_guard.applied=true`, two ordinary
Restarts, another Quick Race, and a separately exercised idle Attract path.
If idle was not tested, record NOT_TESTED; source/emulation preservation is
insufficient to claim its live verdict. R-CAM1-A3d stays paused until acceptance.
