# V-AUDIO2-FIX3 — supplemental balance and neutral policy

User gameplay feedback: FIX2 supplemental layers are audible but masked by the
engine with Engine and SFX sliders at 50%; neutral inhibits the new layers.
This is actual user listening evidence. It is not replaced by offline tests.

## Changes

New private candidate:
`.research-output/vehicles/vaudio2-fix3/candidate-combined/Launch-Vehicle.cmd`.
Previous A/B/C candidates remain intact. The engine WAV and source/tuning
configuration are unchanged. Only three namespaced supplemental WAVs change;
233 other immutable resources remain byte-identical to FIX2 C.

| Layer | FIX2 response gain | FIX3 response gain | WAV authoring gain |
|---|---:|---:|---:|
| whine drive/coast | .55 / .30 | .75 / .45 | 0 → +6 dB |
| spool at full estimated pressure | .60 | .80 | 0 → +6 dB |
| BOV at full estimated pressure | .65 | .85 | 0 → +6 dB |

At the verified native SFX control scalar **0.5**, full-drive/full-pressure
supplemental levels increase by **10 dB** each, combining the original
nonlinear SFX curve with source gain. This is a calculation at the control
input, not a newly measured transfer function of the UI slider or actual race
mix. Coast response increases more strongly because of that nonlinear curve.
The new PCM peaks are 13482 / 14615 / 20535; no source clips.

The existing SFX-volume input is retained. No global mixer, Engine slider,
stock SFX settings or stock engine table is changed. Native code identity and
the existing qualified gain curve remain the basis; no unproved alternative
volume/global address was introduced. The current REA session recognizes the
exact EXE hash but has no procedure boundary at 00409EB0. The existing same-build
Ghidra export and original-instruction replay remain the evidence for this
already qualified seam; no new native field layout is inferred from that failure.

Whine/spool `mute_neutral` are **false** in the new Lancer profile. Whine can
therefore follow input-shaft RPM in neutral. Spool still requires positive
crank-load proxy and rises/decays using the existing pressure estimator; neutral
RPM alone is not treated as physical boost.

BOV gains an **optional** boolean `response.mute_neutral`. Omission defaults
to **true**, preserving all old profile behavior. FIX3 explicitly uses false:
neutral no longer unconditionally blocks a previously qualified loaded release.
Minimum RPM, estimated pressure, rapid load-fall threshold, cooldown and native
one-shot completion still apply. Idle and unloaded revving need not produce a
BOV, and a gear change alone does not request it. This remains a load proxy,
not a recovered physical boost or throttle sensor.

The C helper's private read-only profile record now includes the extra BOV
policy scalar (24 response floats total). Its state-page size, lifecycle,
per-CarID selection and native ownership mechanisms are unchanged. The Python
audition model uses the same backward-compatible policy.

## Checks

- Full suite: **714 run, 713 passed, 1 skipped**.
- New and legacy-neutral native profiles pass the 28 original control/identity
  cases plus explicit neutral loaded release and neutral idle rejection.
- Original SFX gain curve still matches 10,001 native input values.
- GUI audio-preview native-render self-test passes.
- Candidate launcher verify/environment/allocation checks all exit 0.
- Identical resource set; exactly the three supplemental WAVs change. Engine,
  stock resources, geometry, UI and author physics/fitment/shadow/mechanics
  inputs remain byte-identical. The 76,072-byte pre-audio native prefix is
  identical. Later mechanical code relocates without changing its profile.
- Original MRallye.exe and graphics d3d8.dll retain their recorded hashes.
- No game launch, commit, push, publication or private GT sample distribution.

Evidence under `.research-output/vehicles/vaudio2-fix3/`: `balance.json`,
`native-combined.json`, `native-legacy-neutral-default.json`, `tests-full.txt`,
`regressions.json`, build log and candidate preflights. Private inputs remain
synthetic whine/spool/BOV with the existing private GT4 engine source.

## Human test

Start the new candidate, set Engine/SFX to the same 50%/50% used previously,
and compare loaded acceleration, coast and abrupt lift. In neutral check whine
with rising RPM and any load-driven spool; BOV should require a prior pressure
estimate and sharp release, not play on every idle blip. Also test stock cars
and race re-entry. `Preview-Audio.cmd` exposes separate mute/solo controls.

This candidate is ready for listening, not declared subjectively balanced.
Offline preview still omits distance and the native physical DirectSound mix;
combined raw-engine audition clipping is reported rather than hidden.
