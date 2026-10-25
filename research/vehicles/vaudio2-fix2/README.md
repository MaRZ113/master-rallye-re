# V-AUDIO2-FIX2 + V-TURBO1 + optional BOV

Status: three sealed **offline-validated candidates for human gameplay listening**.
No game launch, audible DirectSound-device qualification, commit or publication.
Working directory/branch: `master-rallye-re-vehicles`, `research/vehicles`.

## Findings and implemented changes

The old whine source/resource stem is valid, but authored gain `.18` reaches
the original SFX backend as **-31.2 dB** near the listener; `.08` gives -61.6 dB.
With source RMS about -17.4 dBFS, drive whine could readily be masked. This is
measured original-code evidence, not proof that gain alone explains every silent
gameplay case. The revised drive/coast values are `.55/.30` (-9/-18 dB).
Original engine source and tuning tables remain unchanged.

Supplemental whine, spool and BOV now own three separate ordinary native SFX
objects per admitted participant. They use the original manager/backend and
destructor lifecycle, preserving stock passthrough and CarID isolation. The
bounded 64-owner state table occupies the existing single RW/NX page; code and
constants remain RX. Allocation/slot exhaustion skips the optional effects.
Stale actor publications are invalidated across construction/destruction.
See [native.md](native.md) for exact addresses, ABI, memory and stub boundaries.

`audio-profile.json` version 1 retains its engine-only behavior and accepts
optional `transmission_whine`, `turbo_spool` and `bov_release` declarations.
Each declaration has a source-pinned relative WAV `source`, editable `response`
and explicit `provenance`. Source decoding, clipping checks, canonical mono
PCM16/48 kHz conversion, exact namespaced resource allowlisting and collection
validation are shared. No engine layer is replaced by these optional sources.

### Estimated pressure and BOV

No native boost-pressure or persistent throttle field is claimed. Verified RPM,
gear and signed net-crank-torque / peak-torque provide a **load proxy**. The
authored estimated pressure rises under load and falls on release. Original
`timeGetTime` supplies elapsed time, capped at 100 ms per update.

BOV requires accumulated pressure, sufficient RPM and a rapid fall in load.
A gear change alone does not trigger it. Neutral, finished race, low RPM,
insufficient pressure, cooldown or an active one-shot inhibit triggering.
Actual native playback completion clears the request before another one-shot
can play; the implementation does not guess the end using a fixed timer.

| Editable response | Candidate value | Meaning |
|---|---:|---|
| spool `load_threshold` | .15 | normalized positive crank-load onset |
| `spool_up_seconds` / `spool_down_seconds` | .35 / .55 | smoothing time constants |
| spool `gain` | .60 | authored native SFX gain; -8 dB at full pressure |
| `reference_rpm`, `pitch_min`, `pitch_max` | 4000, .35, 1.8 | loop pitch response |
| `fade_in_rpm`, `mute_neutral` | 1500, true | low-speed/neutral controls |
| BOV `release_rate_threshold` | 3.0 | normalized load decrease per second |
| `boost_threshold` | .45 | minimum estimated pressure before release |
| BOV `gain` | .65 | multiplied by pressure; about -7 dB at full pressure |
| `pitch_variation` | .08 | bounded deterministic event variation |
| `retrigger_seconds` | .50 | minimum interval, also waits for native completion |
| `release_decay_seconds` | .20 | pressure decay while release sound is active |
| `min_rpm` | 2000 | idle/low-speed inhibition |

These are editable SDK controls, not recovered Evo IV boost constants. A load
proxy can also fall during shifts; a loaded shift may legitimately qualify,
while a low-load shift should remain silent. Pedal-perfect behavior still needs
gameplay evaluation or a separately qualified throttle input.

## GT3 source boundary

Local GT3 event names `turbine`, `turbine2` and `b_off` were recovered, but their
instrument/sample dispatch and nominal pitch are not yet qualified. GT3 INST
cannot safely be substituted into the GT4 bank reader. Therefore current
spool/BOV sources are **original synthetic test sounds**, not alleged GT3 audio.
Whine is also synthetic; the previously qualified private GT4 engine source is
unchanged. See [source qualification](../vturbo1/source.md).

`tools/gt3_audio_inspect.py` inventories user-supplied GT3 data without shipping
it. `tools/vehicle_turbo_source.py --kind spool|bov --output PRIVATE.wav` produces
the deterministic fallback. A custom WAV can replace either profile source:
set its relative path, actual SHA256, trim interval, gain/DC/crossfade settings
and provenance, then rebuild. GT inputs and extracted audio remain private.

## Private candidates and test order

Paths below are relative to the repository. Each folder has `Launch-Vehicle.cmd`
and `Preview-Audio.cmd`; they do not replace installed originals.

| Order | Candidate folder under `.research-output/vehicles/vaudio2-fix2/` | Layers |
|---|---|---|
| A | `candidate-A-whine` | unchanged engine + calibrated whine |
| B | `candidate-B-turbo` | unchanged engine + spool + BOV; whine absent |
| C | `candidate-C-combined` | all four independent layers |

First compare A to the existing no-whine baseline. In B, accelerate under load
above 2000 RPM, then lift abruptly: expect one short release. Repeat gentle
low-load driving, idle, neutral and rapid low-load shifts: expect no BOV spam.
After A/B sound and lifecycle checks, try C. Include a stock car, an AI Lancer,
race exit/re-entry and finishing/Results. Check that stock sounds remain normal.
Native A/B checks and launcher preflights precede the C build; actual human A/B
gameplay qualification has not been performed by this task.

For a silent layer, take a read-only snapshot while racing:

```powershell
$env:PYTHONPATH='src;tools;.;.research-output/vehicles/scale1/python-tools'
python tools/inspect_vehicle_audio_voices.py --pid GAME_PID --policy PRIVATE_CANDIDATE/runtime/damage-alpha-policy.json
```

The snapshot exposes source handle, backend request/failure flags, gain/pitch,
position, estimated spool and BOV event count. Requested playback is not proof
of audible device output. Do not compare unrelated candidate/process versions.

The Tk audio panel adds independent mute/solo and a scripted sustained-load/lift
audition, reloading the profile on each render. It uses original native engine
DSP and the verified native **near-listener SFX gain curve**, not a linear gain
approximation. The curve matched 10,001 original-code inputs from 0 to 1.
Spool/BOV controls remain authored; distance, native thread timing, actual engine
SFX gain and physical DirectSound mixing are omitted.

Private `auditions/` contains solo examples and `all-layers-lift.wav` with JSON
measurements. Solo supplemental files have no clipping. The raw-engine combined
audition clips 902/48,000 samples because the standalone native engine DSP
already reaches full scale before its omitted SFX gain. This is exposed by the
diagnostic, not hidden by normalization or interpreted as gameplay clipping.
The already-working engine source was deliberately preserved.

## Validation results

- **713 synthetic tests run: 712 passed, 1 skipped** (full suite).
- Native A/B/C: 28 control/identity cases each; original SFX construction,
  registration, backend Play/SetVolume/SetFrequency/GetStatus/Stop and retirement
  instructions replayed with typed service/DirectSound stubs.
- Spool-only and BOV-only native replay also pass; BOV is independently optional.
- Original gain curve: 10,001 exact comparisons; GUI native-render self-test pass.
- Each launcher passes `--verify`, `--verify-launch-environment` and
  `--self-test-native-allocation` including the exact private RW/NX page.
- A retains all 234 immutable baseline resources byte-for-byte. B retains 233,
  removes only the optional whine WAV and adds spool/BOV WAVs. C retains 234 and
  adds those two WAVs. Mutable session/options files are excluded explicitly.
- Physics, visual, UI, mechanical and shadow author inputs are byte-identical
  to FIX1. Existing native code prefix (76,072 bytes), including engine,
  physics, damage and shadow behavior, is byte-identical. Mechanical extension
  addresses relocate after the new audio payload; its profile is unchanged.
- Fresh author rebuild and runtime package reproduce their manifests, resource
  hashes, payload, operations and policy exactly. No deterministic launcher-PE
  timestamp claim is made.
- Original EXE SHA256 remains
  `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`;
  graphics DLL remains
  `eb7ea3d9501b514bff668f1e75e86041906c5fe4e8afa89f06d658751429aaf4`.

Private evidence: `tests-full.txt`, `native-A/B/C.json`,
`native-only-turbo_spool.json`, `native-only-bov_release.json`,
`regressions.json`, `determinism.json`, `audition-diagnostics.json`, candidate
build logs and each candidate's `vehicle-candidate.json` preflight output.

To reproduce the extended native gain comparison:

```powershell
python tools/vehicle_whine_validate_native.py --exe ../MRallye.exe --profile PRIVATE_PROJECT/audio-profile.json --output PRIVATE_REPORT.json --gain-curve
python tools/build_vehicle_extensions_candidate.py --project PRIVATE_PROJECT --output NEW_PRIVATE_CANDIDATE
```

The original-code replay uses stubs for the Broker, allocator/interner, clock,
native service boundaries and DirectSound device. It proves bounded code/control
and ownership behavior, **not audible gameplay, physical boost simulation or
GT3 playback fidelity**. Human gameplay listening remains the final gate.
