# R-MOD1 runtime handoff status

**Do not run a modded game test from this branch yet.** No native operation
bundle, launcher executable, DInput proxy or human-testable R-MOD package has
been produced. This file is a gate checklist, not a candidate handoff.

Before requesting human time, provide one deterministic package with its own
candidate manifest, exact original EXE SHA, shared-core/build identities,
composed patch-plan hash, configuration hash, course guard and removal steps.
The package must not contain a patched EXE or proprietary assets.

When safe, use a disposable game copy and test in this order:

1. Vanilla pristine launch without R-MOD; record EXE hash and normal frontend.
2. Existing graphical `d3d8.dll` proxy only; record its exact hash and normal
   frontend/race/shutdown. Never replace it for R-MOD.
3. Randomizer external launcher only; test Stock and one-to-three AI policies.
4. On the exact qualified Track10 T1/ID0/Ghost-OFF profile, test four AI / five
   total and the Randomizer-off stock-compatible extender path.
5. Do not start six-to-eight total races until a course/count/roster tuple has
   passed a separate grid-clearance audit.
6. Repeat the qualified modes with graphical proxy + Randomizer and verify
   input, menu navigation, rendering, AI, race, Results and normal shutdown.
7. Verify `MRallye.exe` SHA before launch, while the game is running, and after
   exit. The value must remain the pristine retail SHA.
8. Verify removal between launches restores vanilla behavior without touching
   saves, stock data, `d3d8.dll` or the executable.

The optional `dinput8.dll` path needs a separate approval-free technical gate
inside the already authorized project scope: x86 build, complete six-export
forwarding, safe first-call initialization proven before the affected native
constructors, and a four-way renderer/input matrix. Until then, the launcher is
the only planned activation method and no DLL test should be offered.
