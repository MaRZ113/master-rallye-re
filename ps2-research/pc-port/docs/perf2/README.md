# PERF2 — frame-time fixes and opt-in timing

On top of SPLIT-SCREEN1 / HUD-PORT4.1. User report: split screen is slow even with `PS2SplitScreen=0`, and PS2
effects cost a lot with many cars in view.

## Changes (no identity proof is weakened)

1. **SHA-256 provider reuse** (baseline `provenance.cpp`, patch 0001, lock updated). `sha256_bytes` opened the
   BCrypt provider on every call (~6 µs per hash, PERF1); every geometry identity hashes ~50 times (frontend
   COMPLETE, fleet CAR/OFF/wheel, reflection learning, damage snapshots). The provider is now opened once per
   process; output is byte-identical (all geometry-hash fixtures and the `abc`/empty test vectors pass).
2. **Rejected-certificate cache for per-draw pre-filters** (`courseintegration::certificate_prefilter`): lamp, X-Trail
   chassis/part/wheel entries remember a rejected race certificate for the rest of the device/reset/frame/current
   camera. In split screen with `PS2SplitScreen=0` (and in menus) every such draw previously re-ran the baseline
   HUD context (owner registry/list walk, broker reads) and failed again. A valid certificate is never cached
   here; the final pre-submission re-checks stay live.
3. **Reflection certificate per frame** (`reflection_native_integration.hpp`): one race certificate per
   device/reset/frame/camera instead of one per reflective vehicle draw, as the fleet paths already do. Each draw
   still proves its own owner, material and geometry identity.
4. **Opt-in timing** `PS2PerfTiming=1` (`renderer/ps2_perf_timing.hpp`), window `PS2PerfWindow` (default 300 frames):
   `ps2_perf_timing` records with calls/frame, µs/frame and max µs for certificate, race certificate, HUD context,
   participant table, fleet car/wheel, lamp/race/wheel/frontend entries, reflection snapshot/classify and
   geometry hash. One branch per timer when off.

## Next step

The timing records decide the second round (e.g. damage snapshot rehashing per revision, learned reflection
identity scans, frontend COMPLETE-tree probing).

## PERF2.1 (runtime timing, DLL e21183ca → 78e7b46a)

User timing (PID 19020 split screen with 4 cars, PID 15820 eight-car race), overlay entries per frame:

| Run | entries total | certificate (calls, time) | hud_context | race_certificate |
|---|---|---|---|---|
| split screen, 4 cars | ~10.0 ms | 90×, 5.3 ms | 3.4 ms | 2.0 ms |
| 8-car race | ~4.7 ms | 46×, 1.5 ms | 0.9 ms | 0.6 ms |

The callers were the fleet/wheel/lamp/X-Trail final re-checks, one per draw and camera pass. Fix:
`courseintegration::certificate(Device8&, bool&)` caches the race certificate (valid or not) per
device/reset/frame/renderer-current camera and every PS2 path uses it; the separate rejected-only pre-filter is gone.
The game's main loop runs its update (0x5AFE30) before the frame scheduler (0x653080) draws the cameras, so the
race-level proof cannot change within a camera's traversal; every draw still proves its own owner, buffers, tokens
and transforms. Expected: certificate calls per frame ≈ number of cameras.

## PERF3 (runtime timing with DLL 78e7b46a → 9279a3f4)

PERF2.1 worked: certificate calls dropped from 90 to 1–2 per frame; split screen with 4 cars went from ~10 ms to
~7.8 ms of overlay entries per frame (PID 9116). What remained (split screen, 4 cars, per frame): race entry
624× / 2.5 ms (fleet car 2.1 ms), fleet wheel 736× / 2.0 ms, frontend entry 288× / 1.75 ms, lamp entry 900× / 1.2 ms.

* Frontend COMPLETE path is skipped inside a certified race (cached certificate): COMPLETE models are menu cars; in a
  race every draw that shared a COMPLETE shape probed ~26 owner trees (my FRONTEND-CARS1 slot binding).
* Race fleet CAR shape test is a sorted lookup instead of scanning every profile record per draw.
* `fleet_owner` / `race_context` owner walks are computed once per DrawIndexedPrimitive call (`caller_serial`) and
  reused by the gate, body certificate and final re-check of that same draw.

## PERF3.1 hotfix (DLL 9279a3f4 → c4ccd412)

PERF3 runtime (PID 14516/19548): slideshow with 8 cars — `geometry_hash` 26–28 calls/frame (~8–11 ms), fleet fallbacks
at gates 2/3, few replacements. Cause: the PERF3 owner memo reused one `Context`; `race_context` fills only the first
`roots` meshes and expects a fresh Context, so the previous draw's mesh tail stayed, owners never compared equal, the
car models were invalidated on every draw and re-identified by hashing. The memo now starts from an empty Context.
