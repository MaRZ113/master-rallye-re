# R-CAM1-A3b implementation boundary

**Freecam: not implemented. Status: `BLOCKED_ON_LIVE_RACE_OWNERSHIP`.**

This change extends the read-only scope inspector, its tests and static research.
It installs no native completion hook, changes no renderer source or INI, calls
no Broker getter, and performs no CameraFrame writes. The built DLL is the
existing renderer baseline, not a first-flight candidate. WASD/Numpad/Custom,
mouse look, toggle, focus ownership, pose math and Freecam restoration have no
implementation/tests to claim here. F10 remains reserved for existing capture.

The completed native end audit is in [scope closure](scope-closure.md). GameFov
continues to own `0x006532DD` / RVA `0x002532DD` and tail-JMP to the original
RET-8 traversal. There is no second competing hook. The completion candidate is
the five-byte scheduler CALL at `0x005B0166` / RVA `0x001B0166`. A future bridge
would retain the effective fields through EndFrame, then finish restoration
before returning to `0x005B016B`. Original ECX and float argument, RET-4 cleanup,
EAX/EDX, EFLAGS, nonvolatile registers, x87, SSE and MXCSR all require actual
x86 fixture verification. The byte scanner certifies none of these replacements.

Once the live-race epoch is established, one coordinator must snapshot only
planes/Previous/Current Pose, apply coherent pose/frustum, and restore the
current native snapshot. Native viewport writes survive. Present and Reset
currently call `GameFov.finish_frame`; simply adding pose fields to that owner
would restore too early on the late path. That ownership must be coordinated,
including native driver reentry and cancellation. Install/rollback must cover
both nonoverlapping sites atomically. These are future implementation obligations.

R-UI1 accepted automatic correction, sticky anchors and WORLD restoration,
display lifecycle, vehicle semantics, AF/MSAA, FOV, camera probe, F10 and foliage
diagnostics have no source changes in this stage. Exclusive remains deferred.
Original EXE, assets and reverse databases are unchanged. No game deployment,
new branch/worktree, push, teleport, HUD hide or photo feature is part of this result.
