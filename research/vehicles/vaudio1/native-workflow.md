# Custom engine-source workflow

The optional version1 `audio_profile` belongs to one addon and one physical
CarID. Existing `stock_profile` manifests remain the fallback; a project with
no custom profile uses the existing stock selection and resources unchanged.
The schema compiles a local user-supplied WAV into a unique native MR resource,
then the sealed runtime wrapper substitutes that source for the configured
physical addon while retaining its selected ordinary stock tuning profile.

Example editable profile (the SHA and trim interval must match your own file):

```json
{
  "audio_profile_version":1,
  "policy":"native_custom_engine",
  "physical_car_id":27,
  "stock_audio_profile_id":7,
  "namespace":"lancer_evo4",
  "engine":{
    "source_path":"engine.wav",
    "source_sha256":"<64 lowercase hexadecimal digits>",
    "trim_frames":[0,16000],
    "gain_db":-3,
    "remove_dc":true,
    "crossfade_frames":64
  },
  "notes":"Local private source; document origin, chosen band/rate and approximation."
}
```

`trim_frames` uses **input** sample frames and a half-open interval. Input is
bounded RIFF PCM, mono/stereo,8/16/24/32bit,11025..48000Hz. Explicit trim must
be0.1..4seconds, crossfade≤4096source frames and≤one eighth of the interval.
The importer downmixes, optionally removes DC, applies bounded gain, rejects
clipping/silence, circularly overlaps the chosen seam and linearly resamples.
The output is canonical PCM16 mono48000Hz at
`DataAudio/vehicles/sdk/<namespace>/engine.wav`. These are authoring guards;
they are not claims about the original engine's maximum file/loop duration.

```
python tools/vehicle_audio_import.py --profile local-profile.json --source-root PRIVATE_INPUTS --output .research-output/vehicles/vaudio1/local-audio
python tools/vehicle_audio_validate_native.py --exe "../MRallye.exe" --profile local-profile.json --output .research-output/vehicles/vaudio1/native/replay.json
```

The second command needs the existing optional Unicorn validation environment;
the ordinary importer depends only on Python's standard library. Conversion
returns deterministic resource bytes plus `audio-build.json` provenance and
measurements. Stock WAVs are never overwritten. Linked/escaping input paths,
source hash mismatch and malformed RIFF chunks reject before output creation.

For a GT4 source, first establish the actual vehicle-to-bank binding and sample
format. Choose one recovered loop explicitly; one authentic band passed through
MR's synthesizer is a controlled approximation to GT4's multi-band playback.
An unqualified source sample rate remains unqualified even after resampling:
the output's48kHz header is a known MR authoring format, not proof of the GT4
source rate or correct perceived pitch.

Human checklist: compare stock Navara and addon timbre, idle, low/high load,
acceleration, shift, lift-off/overrun, braking, reverse, player versus AI and
race re-entry. Recheck physics and geometry isolation using the sealed resource
inventory. The lightweight audition of a raw imported loop cannot substitute
for native synthesis, so no generic pitch slider is presented as MR parity.

## Optional original-DSP audition, without the game

```
python tools/vehicle_audio_audition.py --exe "../MRallye.exe" --resource PRIVATE_AUDIO_BUILD/DataAudio/vehicles/sdk/lancer_evo4/engine.wav --stock-audio-profile-id 7 --rev-limit 7000 --rpm 1000 --rpm 3500 --rpm 6500 --seconds 1 --output .research-output/vehicles/vaudio1/audition.wav --play
```

This helper needs the SDK's optional Unicorn validation environment. It runs
the original local x86 DSP, emits a PCM WAV
and diagnostic JSON, and optionally plays the result with Windows`winsound`.
Each repeated`--rpm` adds a segment; each segment lasts`--seconds` (≤3seconds,
≤8segments). No game process, DirectSound device context, Blender or retail
binary code bundled into the tool is required. The original EXE hash must
match the qualified build.

This is a diagnostic approximation to runtime timing/mix while executing real
native synthesis. It intentionally exposes RPM and rev limit, not a guessed
independent throttle-to-audio control. Driving throttle/load remain governed
by physics in the actual game. Listen to the generated Lancer audition before
human gameplay checks, but do not treat an isolated waveform as qualification
of AI mixing, attenuation, overrun or race re-entry.
