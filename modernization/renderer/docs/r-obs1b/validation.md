# R-OBS1b validation

**READY_FOR_COMBINED_RUNTIME_VALIDATION**. The separately identified hook-free
Broker/Dump and R-ATTR1 Restart/idle behaviors were confirmed by the user. This
new combined binary has **PENDING HUMAN VALIDATION**, not transferred runtime PASS.

Fresh executions for this closeout:

- Canonical `python modernization/renderer/tools/build.py`, without diagnostic
  flags: Win32 Release, Visual Studio 18 2026/MSVC, all **12/12 CTest suites PASS**,
  7.98 s. The native policy contract exercises Stock/Windowed/Borderless,
  repeated polling without hooks, non-foreground cursor safety, focus-loss and
  idempotent shutdown. Hidden-HWND live resize/nested Reset and existing
  maximize/restore, display, UI, AF/MSAA, camera/epoch, reflection/resource and
  COM/forwarding suites remain passing. Removed assertions concern only the
  deliberately retired message callbacks/queue, not native presentation behavior.
- Renderer Python **146/146 PASS**, 100.243 s. A new policy test checks source and
  built DLL for absent hook APIs, absent diagnostic build flag, current native
  telemetry and included Attract guard. Current sessions are qualified by the
  newly built native test executable's hash, not an old passing capture.
- Root synthetic **630/630 PASS**, 10.113 s, including 17 bounded single-opener,
  timeout/late-window/menu-less/invalid-owner tests. TEMP/TMP used external
  `D:/CodexScratch/r-obs1-tests`, preserving clean-extraction test boundaries.
- Exact retail inspector PASS, SHA
  `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
- Existing native Ghidra emulation rerun: **60 Loading + 6 idle branch cases
  PASS**. Ghidra 12.1.4 read-only project, temporary transaction rolled back,
  no project save or EXE-file modification. Emulation is synthetic evidence.
- Attract production source/header/factory integration compared unchanged with
  starting HEAD. PatchMemory/ThreadGate tests still run in the native suite.
  Initial factory admission, exact context, ownership, protection/readback/
  cache/rollback and unsupported-host behavior were not relaxed.
- Compileall for renderer/runtime tools and git diff-check PASS.
- PE verifier PASS: PE32/I386, Direct3DCreate8 ordinal 5, ValidatePixelShader 2,
  ValidateVertexShader 3, direct exports; only bcrypt/USER32/KERNEL32 imports,
  no recursive d3d8 or delay imports. Built DLL lacks SetWindowsHookExA/W,
  UnhookWindowsHookEx and CallNextHookEx import names; guard record is present.

Standard candidate: `.build-msvc/Release/d3d8.dll`, **1,674,240 bytes**, SHA256
`37b5487345d2e84b13659f0919b3b2165f29fdeb55acbca9fac6f19d90196179`.
The single runtime ZIP records the closeout build commit in PE-MANIFEST.json
and its package manifest. It contains no EXE/PDB/private assets/raw captures.
No deployment, game launch, branch/worktree creation or push was performed.

Native Broker opening/fresh Dump and two ordinary Restarts must pass together
on this candidate. The exact original hook-enabled stall mechanism remains
UNKNOWN/deferred. The separate legitimate idle Attract runtime confirmation
is preserved; an unexercised idle path on this new DLL is NOT_TESTED.

See [runtime-handoff.md](runtime-handoff.md). R-CAM1-A3d is next after integration
acceptance, and no camera or race-epoch changes were made here.
