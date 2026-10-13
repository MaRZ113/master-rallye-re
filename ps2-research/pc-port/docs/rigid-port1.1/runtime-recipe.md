# The bounded control recipe

Use the accepted existing PS2 DLL and original retail EXE. No installation or
configuration change is needed. Foliage/pixel/HUD replacement remain disabled;
accepted grass/water/reflection settings can stay fixed. Cold Turkey3 load,
brief drive, Restart Race and normal return to menu are the user actions.

From the primary worktree, with the user's actual PID (example36572 was the
first **detected actual process**, not a portable PID), run:

```powershell
python ps2-research/pc-port/tools/rigid_lifecycle_probe.py sample `
  --pid 36572 --seconds 60 --interval-ms 100 --max-instances 8 `
  --output ps2-research/data/rigid-port1/lifecycle-control-36572-a.jsonl
```

Wait for capture start before course loading. Existing output files are not
overwritten; use another clearly numbered capture if a missing segment alone
is required. Read rights only;64KiB per sample, at most8 selected instances,
60seconds. Poll results are non-atomic; zero vectors do not mean proven frees.

For thread/order, the user manually opened the exact EXE in installed x32dbg.
At the debugger command line:

```text
scriptload "D:\Game\Master Rallye\master-rallye-re-general\ps2-research\pc-port\docs\rigid-port1\native-logpoints.x32dbg"
scriptrun
```

Then manually F9 to main menu, capture the second passive run (actual PID12760)
and repeat the same course/restart/exit actions. Save the Log text as ignored
`ps2-research/data/rigid-port1/x32dbg-lifecycle-control.txt`. Retain only the
required126 logpoint observations in derived evidence. Each point disables
after16 hits, at most224 total records. Caps apply independently and can be
consumed by frontend traffic; missing late events are not proof of no teardown.
The debugger changes INT3/debug timing, not game data or files. No engine
function was executed artificially. The user closed the game after capture.

Review the saved evidence offline:

```powershell
python ps2-research/pc-port/tools/rigid_lifecycle_review.py `
  --input ps2-research/data/rigid-port1/lifecycle-control-12760-b.jsonl `
  --debugger-log ps2-research/data/rigid-port1/x32dbg-lifecycle-control.txt `
  --output ps2-research/pc-port/docs/rigid-port1.1/correlated-control.json
```

These commands were actually executed, with the supplied PID/output pairs.
The two sources have different clocks: debugger line order and sampler elapsed
time. Correlation uses exact instance/body pointer pairs, not invented timestamps
or equal per-breakpoint hit counters. Thread7588 belongs to this observed
session only. Future selective prop-lifetime validation is a separate gated
experiment, not automatic authorization to spawn or broaden logging.

Official command references:
[scriptload](https://help.x64dbg.com/en/latest/commands/script/scriptload.html),
[scriptrun](https://help.x64dbg.com/en/latest/commands/script/scriptrun.html).
