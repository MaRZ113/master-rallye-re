# One original PC convex lifecycle control

The new observer does not spawn a tumbleweed, call a game getter, write process
memory or install a DLL. The original vehicle can exercise the shared convex
reader/clone/backend interface; it cannot prove the private tumbleweed port or
physical contact. Use a separate manual session with the same verified retail
EXE and the currently accepted renderer. Keep foliage/pixel/reflection modes0.
Preserve already working grass/puddle settings if wanted, identically each run.

## Passive snapshots

From `D:\Game\Master Rallye\master-rallye-re-general`, make an ignored output
directory using `New-Item -ItemType Directory -Force ps2-research/data/rigid-port1`.
Start the game manually and obtain its exact PID with Task Manager. Replace
`12345` below; it is an example, not a detected process. Start sampling before
loading Turkey3, drive briefly, restart and return to menus within60seconds:

```powershell
python ps2-research/pc-port/tools/rigid_lifecycle_probe.py sample `
  --pid 12345 --seconds 60 --interval-ms 100 --max-instances 8 `
  --output ps2-research/data/rigid-port1/native-control.jsonl
```

The process is opened with query/read rights only. The exact on-disk EXE SHA,
loaded PE32/base, creation identity and installed backend/vtable slot are gated.
Each sample has a64KiB read budget, at most16 instances, and a maximum60second
duration. Root/vector/instance double reads detect some concurrent changes;
they do not make a snapshot atomic or eliminate pointer-reuse/ABA ambiguity.
An unreadable/changing relationship is explicitly reported. Header-only image
validation is not a checksum of all loaded code. No native course certificate
is acquired: `course_identity=UNKNOWN` throughout, not an admission permission.

Fields include actual vector count/selection truncation, representation slots
0/+4, base+8, body+C, category+10, Egg name+14/cache+18. Only body vtable691A04
permits interpretation of current XYZ/four-word orientation; the original seven DWORDs
are retained. Other body types remain undecoded. No resolved Egg pointer is
dereferenced. Changed/absent selected addresses do not prove entity deletion.
No contact, function-call thread or private resource ownership is inferred.

## Function order/thread, if needed

Installed x32dbg is available at
`D:\Game\Master Rallye\_reverse-tools\xdbg\release\x32\x32dbg.exe`.
Load the verified retail EXE manually and check loaded image base00400000.
While paused before cold Turkey3 loading, load the supplied
`native-logpoints.x32dbg` through the debugger's script interface, then resume
manually. Save the debugger log after load/brief drive/restart/exit. If
breakpoints already occupy any supplied address, resolve that in the debugger
first; do not replace unrelated breakpoints. The script is a generated recipe,
not a debugger runtime test performed by Codex.

Each of14 exact entry/RET logpoints records event, thread ID, ECX, caller or
return EAX, and only event-specific original arguments. Every point disables
itself at16 hits, limiting output to224 records. Initial physics updates establish
a thread/order control; their hit cap does not cover the entire race. Do not
interpret missing late events as absence of cleanup. There is no automated
`run`, native `call`, DLL injection or vector modification. INT3 instrumentation
changes live code/debug timing, and is not the passive sampler. Original EXE
bytes on disk remain untouched. Remove only these named diagnostic breakpoints
after the capture; do not clear the user's other debugger state.

Log conditions and never-pause behavior follow the official
[conditional-breakpoint documentation](https://help.x64dbg.com/en/latest/introduction/ConditionalBreakpoint.html).
Fast-resume stays0 because enabling it with break condition0 skips logs;
see [FastResume](https://help.x64dbg.com/en/latest/commands/conditional-breakpoint-control/SetBreakpointFastResume.html).
This limits text output and callback hits, not every possible debugger overhead.

## What the next capture must settle

Correlate original reader EAX prototype, attach Egg/body/category, cloned
instance and body assignment; record the original physics-update thread.
Observe native cache clear before original cleanup, race restart and normal
exit. Private source admission still requires an owned stream/cache bridge,
allocation rollback, native entity lifetime and an actual vehicle-contact test.
This control is insufficient to authorize injected objects by itself.

Expected line kinds: `header` with process/hash/limits; `snapshot` with sequence,
elapsed seconds/read bytes/status/backend/instances; debugger text starts
`RIGID_PROBE event=... tid=...`. Keep logs local/ignored and return this bounded
capture rather than arbitrary RAM dumps. Live capture: **NOT_PERFORMED**.
