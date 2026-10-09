# Remaining gates after J.1 runtime qualification

R5V-J.0 remains accepted as the offline manifest/compiler foundation. J.1 is
closed with human runtime evidence for the original unmodified retail EXE and
the audited external runtime integration. J.2 is in progress: the shared
two-addon package and its per-vehicle Quick Race paths have runtime evidence,
while the following integration scenarios remain open.

## Required before J.2 can close

1. **SplitScreen composition:** run ID27/T2 R5VQualifier and ID26/T1 Mercedes
   simultaneously through the external launcher, verifying distinct physical
   IDs, CarType/WheelType, rendering, input and camera ownership. First confirm
   the native mode permits this player/class pairing.
2. **Vehicle Select restoration:** after a completed ID27 race, reopen the
   selector without manually navigating and verify physical ID27 restores to
   T2 local ordinal 7. Repeat for ID26 and stock ID7. The existing 2026-10-09
   snapshots show a consistent ID27 selection, but not the complete return
   lifecycle; do not treat this as fixed.
3. **Rallye Cup persistence:** the capture set shows an ID27 initial T2 Cup
   race and its Results state. Advance one stage and compare CarID, CarClass,
   and DriverID to prove native roster reuse.
4. **Master Rallye persistence:** create a new T2 competition, naturally
   generate ID27, save, exit the process, relaunch with the same external
   runtime bundle, resume, and verify exact physical ID and DriverID. Advance
   one stage if practical. Do not alter or migrate an existing stock-only
   save.
5. **Visual integration:** human-check the HUD/progress marker color,
   SmallCarSheet, Results identity/art, Race Details text, frontend names,
   lock appearance, and commit blocking under the same external bundle.
6. **Removal control:** disable the external launcher/bundle between runs,
   launch the unchanged retail EXE normally, and preserve external profile
   saves. Do not delete save files as part of removal.

## Confirmed and bounded

The current runtime bundle is one deterministic collection containing both
manifest-resolved addon profiles and one native patch operation set. It is
statically verified as 246 operations and 243 resources; the native launcher
`--verify` command passes. Runtime captures confirm Mercedes ID26 player and
natural-AI paths, R5VQualifier ID27 natural-AI paths, ID27 magenta Broker
Colour, Results display labels, and an initial T2 Rallye Cup race/Results
pair. These are separate from the still-open campaign/lifecycle gates above.

The exact J.1 runtime builder intentionally pins the only two runtime-qualified
addon profiles, IDs 26 and 27, and composes their audited H.2/I.1 operations.
That is a fail-closed capability boundary, not arbitrary-ID runtime support.
The J.0 compiler remains manifest-driven for the reference collection;
`runtime_installable=false` remains unchanged.

## Profile and removal notes

The J.1 process working directory is the external `resource-root`, so
game-generated profile state is expected under that root's `DataGame` tree.
Keep `PlayerState.xml`, `PlayerState.xml#`, and `options.xml#` when disabling
the loader. The native bundle verifier preserves these known runtime-state
files and rejects unexpected resources. The same external root shares saves
between addon launches. A save referencing ID26 or ID27 is not qualified for
use without its addon bundle; no safe unmodded fallback or save migration is
claimed.

No hot-unload is supported. Normal removal occurs between launches by running
the original executable without the external launcher; leave the resource
root and saves in place for later reinstallation.

J.3 public packaging must not begin until J.2's remaining runtime gates are
closed and the Vehicle Select restoration path is resolved.
