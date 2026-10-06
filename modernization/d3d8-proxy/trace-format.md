# JSONL schema1 and capture control

All integer API values are unsigned/raw numeric words unless explicitly stated.
Pointers are process-local x86 addresses; HRESULTs are unsigned32 bit patterns.
Unknown observational values are JSON null. Names are readable metadata, never
instructions to change rendering. UTF-8 JSONL uses one complete record per line.

Session filename: `MRRGFX2/logs/session-UTC-<pid>.jsonl`, relative to the DLL.
It records executable path/size/SHA, proxy path/SHA, I386 architecture, build label,
real runtime requested/actual path, factory SDK argument, exact CreateDevice
parameters before/after, Reset before/after/result, cooperative-level changes,
resource creation and final wrapper Release. Periodic summaries contain counts
for all97 device slots, attempted primitive totals and the Present result.
The first interval can begin mid-frame and is explicitly incomplete.

F10 uses the high key-state bit and a foreground-process check near BeginScene
and Present. Rising edge sets pending; after that Present a fresh buffer starts.
The following Present closes the capture. Thus it includes Clear before BeginScene
and records one complete Present-to-Present interval. Holding F10 cannot rearm;
release and press again. A very short press between polls can be missed. F10 is
not consumed from the game's input or Windows menu handling. Test any existing
game binding visually. A second deliberate press can request another interval.

Frame filename: `frame-<pid>-d<device>-<frame>.jsonl`.

| Record | Contents |
|---|---|
| frame_begin | schema/proxy version, EXE path/hash, proxy hash, real DLL path, exact/unknown build, device/frame IDs |
| event | sequence/frame, slot/method, result, caller address/module/base/return_rva, eight padded argument words, optional payload bits |
| draw | event fields plus sequential draw_index, primitive type/count and **pre-call** observed state |
| frame_summary | all method counts, attempted primitive total, interval flag, Present result, likely bypass flag |
| frame_end | complete interval flag, reason, truncated/dropped counts, buffered draw count |

Payload copies include16 matrix float-bit words,6 viewport words,17 material words,
26 light words,13 Reset-parameter words before+13 after where readable, and Present
source/destination RECT words. Null Present RECT pointers remain distinguishable
in arguments; partially readable optional payloads do not authorize inference.
No geometry, pixel data, shader bytecode or full memory dump is captured.

Draw state stores viewport, raw VS/FVF and PS, selected RS/TSS, WORLD/VIEW/PROJ
and texture0/1 matrices, textures, streams/strides, IB/base, render/depth targets.
Matrix values have9 significant decimal digits and exact32-bit `bits` arrays;
non-finite decimal values become null while bits remain intact. Viewport float
bits remain available in SetViewport payload. Bindings include last creation
serial where known; zero serial means no metadata association. A known-null
resource pointer is0; an unknown pointer isnull.

Resource creation session records contain method, device/frame, pointer, serial,
eight raw arguments and `lifetime_observed=false`. Argument positions follow the
exact signatures in interface-map.json (dimensions, levels, usage, format, pool,
byte size/FVF where applicable). They are not guessed texture identities.
Serial increments on every observed create, including reused pointers; associations
are bounded to8192 and cleared after successful Reset. Child releases are raw.

Hard limits per device capture:8192 draw snapshots,16384 events, fixed allocation
≤32 MiB (compile-time assertion), and64 MiB serialized output. Registry≤8192;
session≤16 MiB. Overflow marks truncated/dropped and stops buffering, but native
calls and counters continue. Captures are not continuously accumulated in RAM;
one reusable buffer is allocated lazily. Serializing can hitch for this one frame.

Frame output uses `.tmp`, complete-line writes, flush, then atomic rename. Failure
leaves an unaccepted temporary file; partial writes are truncated to the last
complete record where the filesystem permits. A process crash can leave `.tmp`;
never treat it as a full capture. Session partial-write failure similarly attempts
rollback of the partial line and disables file output. Rendering continues.
The reader rejects malformed, interrupted, non-finite or oversized input.

Reset/release aborts an active capture with `complete=false`. Successful Reset
invalidates state; later events repopulate it. Complete means interval coverage,
not a successful Present or human rendering parity. Check HRESULT separately.
No shader/light absence is reported as a confirmed0 from an incomplete/truncated
event sequence. The periodic counters still describe only intercepted calls.

Offline use, from repository root:

```powershell
python modernization/d3d8-proxy/tools/annotate_trace.py <frame.jsonl> --output modernization/d3d8-proxy/.analysis/annotated.jsonl
python modernization/d3d8-proxy/tools/summarize_trace.py <frame.jsonl> --session <session.jsonl> --output modernization/d3d8-proxy/.analysis/summary.json
```

The join requires pristine EXE SHA, matching R-GFX1 map SHA, exact executable
module path and `(return_rva, method)`. **CALL RVA is not return RVA.** Another
module or executable with the same basename does not match. Unknowns remain
UNKNOWN. The DLL contains no game-specific owner names. Narrow offline categories
are billboard, stock shadow, packet UI/video and debug suggestions; shared mesh
draws cannot reliably separate vehicle/road/sky/terrain. Annotation grade is
STATIC_OWNER_MATCH_IN_TRACE with semantic_confirmation=false. Human observations
must support any later CONFIRMED_BY_RUNTIME_TRACE claim.
