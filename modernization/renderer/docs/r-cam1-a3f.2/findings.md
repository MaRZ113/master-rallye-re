# R-CAM1-A3f.2 — high precision flight timing

## Change and preserved behavior

The Freecam input sampler now uses `QueryPerformanceCounter` with a frequency cached once when the game-window input subclass attaches. Elapsed time is computed as a floating-point counter delta divided by the validated positive frequency. The existing native camera-submit scheduler remains the sole sample point. The controller equations, exponential translation response, direct mouse look, 50 ms integration cap, pause behavior, camera scope, and all input/cursor ownership are unchanged.

The millisecond `GetTickCount64` delta quantized motion time to 1 ms steps. QPC removes that coarse quantization from ordinary supported systems, which is the targeted source of small per-frame translation variation. This is a timing-resolution correction; synthetic validation cannot prove the perceived visual improvement.

## Clock failure and lifecycle policy

If `QueryPerformanceFrequency` fails or returns a nonpositive value at attach, the sampler selects `GetTickCount64` and reports its 1000 Hz granularity. If a QPC sample fails later, it switches one-way to `GetTickCount64`, establishes a fresh fallback baseline at that instant and returns zero for that sample. The two domains are never subtracted from one another. A backwards or negative sample is rejected, increments the invalid counter and rebaselines safely. The source is selected again only on a new attach.

Focus loss, window deactivation, lifecycle cancellation, Reset cancellation and release clear only the timing baseline (along with their pre-existing input cleanup). The selected source and bounded counters remain available for diagnosis. On regain, the first sample establishes a baseline and contributes zero elapsed time, so time spent unfocused cannot move the camera. The controller continues to cap accepted elapsed time at 50 ms, including long pauses or stalls.

## Diagnostics

The existing bounded F10/free-camera state snapshot now includes clock source, source frequency, last/min/max/mean observed interval in milliseconds, zero-interval count, intervals over 50 ms, and invalid-clock count. It does not emit per-frame records. Statistics use saturating counters; intervals are recorded before the controller's existing cap, making long scheduling gaps visible without permitting a movement jump.

## Evidence boundary

Native deterministic tests exercise QPC-sized 8.333/16.667 ms intervals, sub-millisecond timing, equal and backwards counters, invalid frequency, QPC failure and fallback-domain reset, focus baseline reset, long gaps, and diagnostic accounting. The full native suite, Python suites, compilation and PE verifier are listed in [validation](validation.md). The DLL has not been tested in-game in this phase; use [runtime handoff](runtime-handoff.md) for the short human comparison.
