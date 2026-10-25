# V-SDK1-PERF2 — frontend loading diagnostics

2026-10-24 · `research/vehicles`.

**Update:** The subsequent user-run captures identified a dominant cached-DXT
reader cost. A source-qualified bulk-read adapter is now implemented separately;
see [live measurements and adapter validation](dxt-bulk-read.md). The initial
investigation below remains the chronology before those captures. Original
c-perf and its nine-stage layout remain unchanged for A/B comparison.

## What is established

The user measured the visible hesitation as Subaru less than one second,
Pajero approximately two seconds and Lancer approximately five seconds.
Re-selection is faster; leaving Vehicle Select and returning restores the
delay. These are human runtime observations, not precise profiler samples.

This is not sufficient evidence to reapply the old PERF1 diagnosis. PERF1 had
137 texture creations on every warmed frame. The newer observation may involve
cache destruction, initial texture construction, upload conversion, file access
or several of these. No cache-lifetime patch or automatic texture reduction is
justified before the new timing counters have been collected.

Exact original retail EXE SHA256 remains
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
REA/Ghidra12.1.4 reopened that immutable source and supplied the native path
evidence. Direct PE mappings/Capstone separately verified emitted call preimages,
argument counts, displaced instructions and QPC import addresses.

## Native loading and release paths

| Native path | Qualified behavior | Timing distinction |
| --- | --- | --- |
| `0053BE70` | Model-manager lookup; existing model reused; cache miss loads source/cache, updates residency, may evict | Existing caching is real, but frontend ownership still needs a live trace |
| `0053C6B0` -> `00551430` | Open cached `.dx` and construct the serialized model | Inclusive file/stream/decode/material setup; not pure CPU parsing |
| `0053D2F0` | Texture-manager lookup and LRU; absent data calls GXI/cache loader; source charge width×height×4 | Hit and miss paths differ; the profiler measures miss stages and actual evictions |
| `0053DCC0` | Source GXI/cache eligibility path | Successful cached DXT use should avoid expensive source reconstruction |
| `0053DF60` -> `00558CB0` | Cached `.dxt` loading and texture object construction | The MR DXT wrapper contains BGRA pixels, not precompressed GPU mip levels |
| `005587E0` | CreateTexture, acquire surface, D3DX surface conversion, generate mip levels | Conversion/mip work repeats when the native GPU object must be recreated |
| `0053D53B` -> `00558740` | Actual texture LRU eviction releases GPU texture and backing CPU image | Count directly distinguishes pressure from simple initial loading |
| `0053CFFC` -> `0053E7C0` | Texture-manager clearing walks entries, releases native resources | Can confirm a clear during frontend exit/re-entry; source alone does not prove that menu transition owns this call |
| `0053C09C` -> `0054C780` | Actual model LRU eviction | Separates model-cache pressure from texture processing |

`0053CDF0` initializes the32MiB native source-pixel budget. Increasing that
constant without evidence would not remove mandatory initial GPU conversion,
nor establish safe retention across manager destruction/reset. It is unchanged.

## Current frontend complexity

Read from the delivered V-SDK1 `candidate-30-final`, without changing any asset:

| Vehicle | Vertices | Physical draws | Referenced DXT resources | Native source charge |
| --- | ---: | ---: | ---: | ---: |
| Subaru | 6707 | 26 | 32 | 369920B |
| Lancer | 7673 | 186 | 71 | 11331584B |
| Pajero | 8626 | 214 | 76 | 3104768B |

Lancer has similar geometry count but substantially more texture pixel data
than Subaru. That is a useful hypothesis for native conversion cost, not proof
that conversion accounts for its five-second stall. All referenced family-local
DXTs were checked for exact byte duplicates; none can simply be merged losslessly.

`vehicle_frontend_complexity.py` reports these counts, source dimensions, hashes,
duplicate candidates and measured Python read/parser times. The current cached
offline reads/parsing are tens of milliseconds, but those are different code,
different cache state and no GPU work. They cannot establish native timing.

The current main-directory renderer log is
`session-20261024-041219-33516.jsonl`. It contains520frame summaries and
6090successful CreateTexture events, with peaks of657/653creations at frames
5147/12827. It mixes loading, menus and racing; the logger has neither per-stage
wall-clock durations nor reliable selected-car markers. Creation events explicitly
say `lifetime_observed:false`. They cannot measure destruction, loading seconds
or assign those bursts to a particular car. Older Pristine-directory logs were
not substituted for this run.

## Implemented opt-in native profiler

`vehicle_frontend_perf_native.py` appends nine independently timed wrappers into
the existing external process payload. It uses original imports
`QueryPerformanceFrequency` IAT`0068F224` and `QueryPerformanceCounter`
IAT`0068F228`; it imports no DLL and starts no graphics/background thread.

| Stage | Patched call | Original target | Stack arguments |
| --- | --- | --- | ---: |
| DX cached read/parse | `0053C719` | `00551430` | 1 |
| GXI fallback load | `0053D3E6` | `0053DCC0` | 1 |
| DXT cached load inclusive | `0053D3FC` | `0053DF60` | 2 |
| GPU texture creation | `005589CD` | original `[EDX+50h]` | 8 |
| Surface conversion/upload | `00558A3F` | `005D8982` | 10 |
| Mip generation | `00558A71` | `005D9281` | 4 |
| Texture LRU eviction release | `0053D53B` | `00558740` | 0 |
| Texture-manager clear entry | `0053CFFC` | `0053E7C0` | 1 |
| Model LRU eviction release | `0053C09C` | `0054C780` | 0 |

Each32-byte row contains a short lock, call count, cumulative64-bit QPC ticks,
maximum and last duration. The nine rows use288bytes in an explicitly reserved
512-byte tail of the preexisting4KiB RW/NX supplemental state page. In the
current30-layout this is`0x10024E00`; the composer derives the address rather
than assuming it. The emitter validates unused zero storage, actual audio slot
stride/capacity, sealed allocation bounds and every original call preimage.

The GPU hook replaces exactly `CALL [EDX+50h]; TEST EAX,EAX` and replays the
displaced TEST after preserving the original COM result. All wrappers copy the
qualified stack arguments, preserve input registers before the original call
and retain its return registers, callee-saved registers and resulting flags.
Timing starts/stops outside the original call. No native resource is retained,
released, substituted, downsampled or otherwise modified by these wrappers.

GPU creation timing includes the existing graphics proxy's call overhead and
driver blocking; it is not GPU completion time. The original call now returns
through the private wrapper, so observer-only creation-caller addresses in the
proxy log change for this diagnostic candidate. The original renderer DLL on
disk stays unchanged. This profiler is opt-in and not a default release build.

## Capture procedure

The profiling candidate includes `Capture-Frontend.cmd`. Double-click it while
exactly one profiler-enabled MR process is running. It finds the PID, asks for
the vehicle and `cold`, `warm` or `reentry`, then starts a30-second recording
after Enter. Switch to the game and perform exactly one intended action.
Timestamped JSON is saved under `evidence/captures/`; no Task Manager PID lookup
is needed. `tools/capture_frontend_performance.py` is the reusable wrapper and
also accepts `--car Lancer --phase warm --seconds 20` as CLI arguments.

`vehicle_frontend_perf_capture.py` opens the target with query/read rights only.
It verifies original executable SHA256 and all nine installed profiler hooks,
then reads counter snapshots twice, accepting only identical unlocked rows.
It neither writes nor resets process memory. QPC frequency comes from Windows
on the same host. Individual capture files contain the supplied test label,
sample timeline, interval call/tick deltas and the binding-file hash.

Run the profiler candidate and start sampling **before** the measured action:

```powershell
python tools/vehicle_frontend_perf_capture.py --pid <MRallyePID> --binding <candidate>/runtime/native-patch-manifest.json --label Lancer-cold --seconds 30 --output .research-output/vehicles/vsdk1-perf2/evidence/lancer-cold.json
```

Repeat with explicit labels for stock Navara, stock Pajero, Subaru, Lancer and
imported Pajero. For each, record:

1. First selection after process startup; include a note if its model was
   already loaded by the default selection before the capture began.
2. Switch away and reselect the same car without leaving Vehicle Select.
3. Start a capture while outside Vehicle Select, re-enter, then select the car.
4. Repeat the sequence three times using identical graphics options. Keep
   selection/action notes with the capture; counters are not automatic CarID
   attribution.

Do not sum inclusive DXT-loader time with its nested GPU/conversion/mip times.
Compare these children with their parent and inspect residual time separately.
File lookup/I/O and native decoder/material resolution are still combined at
some boundaries. Independent GPU buffer creation and first-visible-frame latency
are not yet instrumented. Counter maximum is since launch; interval totals and
averages use capture deltas. No warm-OS-cache measurement is labelled cold disk.

## Validation and next optimization decision

Seven asset-free tests pass: wrapper argument counts0/1/2/4/8/10, native call once,
registers/flags/stack cleanup, indirect GPU TEST, counter total/max/last math,
snapshot lock rejection, monotonic deltas and offline/log diagnostic boundaries.
All nine preimages are checked against the actual current30reference image.
The profiler appends code without changing its existing payload prefix or
native audio state. No game was running during this implementation.

That initial profiler-only stage did not establish a speedup. Subsequent owner
captures identified scalar cached-DXT reads as the dominant measured interval.
The lossless bulk reader and the later decoder-attested re-entry capture are
documented in [dxt-bulk-read.md](dxt-bulk-read.md). Measured DXT inclusive windows
were 4323.4438 ms /81 loads before and 72.1251 ms /71 loads after; they are not
identical action counts or a whole-menu/FPS benchmark. No speculative cache
increase, retained leaked COM object, asynchronous graphics upload or unverified
DX/DXT format extension was introduced. Optional texture quality policy is a
separate authoring decision, not the explanation for this lossless speedup.

Private evidence: `.research-output/vehicles/vsdk1-perf2/evidence/`, including
REA excerpts, exact profiler bindings and the current complexity/log report.
