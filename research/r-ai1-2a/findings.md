# R-AI1.2a - Challenge frontend preview sync

Status: **READY FOR HUMAN RUNTIME**. This implementation has no human runtime
pass yet. R-AI1.2 stays CLOSED / CONFIRMED_BY_RUNTIME for its tested behavior.
Starting branch research/r-ai1-2, exact HEAD
8a17f2ddf59d81dd8f4f75e8c7601d61becc4c10; tracked tree clean, baseline334/334.
New branch research/r-ai1-2a. Existing local Ghidra and two ZIP artifacts retained.

Stock chronology: screen initialization45E4F0 -> details45EB30 -> authored
preview, then Start45EA60 ->44FEC0 -> late45010E randomizer -> native race.
The mismatch originated in two separate authored-ID reads, not incorrect
localization or model mapping. The preview name and 3D model BOTH consume EDI
after45EC35. One ID substitution synchronizes both native presentation paths.

New chronology: details native authored load -> resolve config/generate once
in DLL -> native preview publications -> Start consumes that cached ID ->
original registry-derived class and native driver publication. Redraw and Start
do not generate again. Native Retry goes directly to Loading and does not call
the participant constructor. Stock retains authored ID, preview and native RNG.

Minimum shared identity is absolute CarID; class derives from the stock registry
in the race. The screen has no driver name or class indicator. Driver policy:
**CHALLENGE DRIVER FOLLOWS RANDOMIZED NATIVE CHOOSER**. No authored-driver
preservation is introduced. Moving vehicle RNG before Start can change the
later native driver draw; this is not a promise of identical old/new RNG streams.

See [preview owner](challenge-preview-owner.md), [lifecycle](lifecycle.md),
[intervention](intervention.md), [validation](validation.md), and
[human handoff](runtime-handoff.md). A process-local cache is necessary because
native preview fields do not freeze policy/event lifetime and the constructor
reloads authored data. No save, sidecar or original asset is changed.

Six+ capacity, general policy redesign and unchanged-EXE loader are excluded.
Five-car composition remains the independently closed R-AI2 intervention.
