# R-CAM1-A3c: implemented observer pilot

Starting checkout: `D:/Game/Master Rallye/master-rallye-re-general`, branch
`master`, clean HEAD `0ed480712da532a66376da9bd5658166a7663c78`.
No branch/worktree was created, no retired tree was used, and nothing was pushed.

Production additions:

- `include/race_epoch.hpp`, `src/race_epoch.cpp`: fixed-capacity generation/job/owner
  transitions, guarded storage readers, typed supporting-context rejection,
  exact native contexts and transactional patch ownership.
- `src/race_bridges.cpp`: fixed naked x86 bridges for the ten selected sites.
- `src/race_observer.cpp`: exact-retail/device-thread admission, bounded native
  event callbacks, safe hook lifetime and one compact F10 lifecycle snapshot.

Device construction installs observation only when the executable is exact retail
and the existing Trace option is enabled. Device release/Reset revoke state.
The canonical interface generator owns the new Device8 attachment field so
regeneration preserves it. Trace's existing F10 frame writer emits one
`race_epoch_snapshot`; it neither resets the ring nor adds a hotkey controller.
There is no per-frame lifecycle logging or new public configuration version.

The snapshot contains installation/ownership state, request and successful
generations, copied job names/flags/lifetimes, owner attachment/execution lifetime,
unique live/pending membership, participant readiness, typed Broker context,
current camera identity/count, and the last 128 native transitions with VA/RVA,
thread and precise reasons. Only bounded audited fields are read. Array reads
are preceded by lifetime, registry, live-list, retirement and AI checks.

`tools/analyze_race_epoch.py` reads a selected F10 JSONL and summarizes owner
creation inside/outside the captured execution intervals. It keeps authorization
false, bounds file/line/event/job sizes, and writes nothing to the input. The
current inspector/map add only new anchors and observation metadata; historical
A3b documents stay untouched. Ghidra 12.1.4 read-only export added five function
records to the ledger (71 total), with bounded lifecycle excerpts separately.

The concrete blocker and conservative pointer-reuse policy are in
[race-epoch.md](race-epoch.md). A successful recorded native commit is now distinct
from stale scene snapshots, but France1's complete owner/job ordering has not been
observed. Later owner creation receives no invented job lifetime. Current course
identity is not inferred from TrackID. The first-flight implementation is therefore
absent under the prompt's observation-only handoff rule.

Accepted UI/renderer functionality remains outside this change: carousel rows,
PreserveMargins v2, resizing/Borderless, AF/MSAA, preview, MenuFreezeFix,
feature-local FOV/vehicle semantics, reflections and foliage provenance. Exclusive
remains `R-EXCL1 DEFERRED_KNOWN_BROKEN`. No camera writes, flight controls, new
lighting, textures, shaders, photo mode, teleport, HUD hide, or later phase began.
