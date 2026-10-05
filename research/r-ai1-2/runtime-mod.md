# Modular research DLL

MRallyeRandomizer.dll exports `MRChooseV1(hint,first,count,slot)` and
`MRChallengeV1(hint,first,count,slot)`, x86 stdcall, four integer arguments.
Choose returns class0..2 or -1 (Stock); Challenge returns absolute ID0..24
or -1. Hints0/1/2/4 correspond to Quick/Challenge/Cup-or-Invitation/Master.
Type2/7/6-or-8/5 must independently agree. DLL sources separate bounded config
and generic class-cycle policy from game ABI and stock eligibility.

This module does not install hooks, allocate participants, rewrite DriverID,
rewrite CarClass, change counts, alter native saves or maintain a sidecar.
The exact EXE bridge calls it only at the audited new-roster builders.
Replay/legitimate Attract owners are separate and unpatched; it does not read
persisted Replay/Attract Broker flags as fresh-generation evidence. Network
player count and split-screen are additionally checked in the callback.
The retail split-screen Bool getter4AE2D0 returns AL. Its DLL declaration uses
a byte-return Bool ABI; compiled tests exercise false/true with nonzero upper
EAX bits, avoiding an erroneous full-EAX split-screen rejection.

Before any native game ABI call, DLL checks image base400000, size3121214,
exact source-file SHA256 of one of the two research profiles, and live
bridge/builder bytes. The standalone native test host is rejected before
game calls. Config is relative to the verified EXE directory and read once
at first AI per newly generated roster. Missing/invalid config and unknown
context return Stock with zero policy RNG draws.

Optional bounded diagnostics are separate from Broker evidence. Checker
requires the [pinned build](build-summary.json), generation config hash and
ordered diagnostic classes; it never declares a runtime pass.

The loader for an unchanged original EXE remains **DEFERRED**. This is a
modular research package, not a ready public runtime loader or EXE distribution.
Proxy forwarding/wrapper compatibility must be audited in that later work.

## Runtime closeout

Exact package DLL behavior is CONFIRMED_BY_RUNTIME in tested modes/counts. Current bridge deployment remains research-only; no original-EXE-unchanged loader has been completed.
See [runtime evidence](runtime-closeout.md).
