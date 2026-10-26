# Audio Studio

Open a **qualified addon project** with an existing `audio-profile.json`, then
choose **Audio**. Stock projects retain native audio passthrough; this milestone
does not create arbitrary stock sound overrides or invent missing response presets.

## Four independent layers

Choose Engine, Transmission Whine, Turbo Spool or BOV. Engine/Whine/Spool are
continuous; BOV is a one-shot. The inspector shows the current source name,
PCM format, duration, provenance and abbreviated SHA256. **Diagnostics** prints
full source/output hashes, converted mono PCM16 48000 Hz format, peak/RMS,
loop-endpoint warnings, source settings and affected namespaced resources.

- **Import Local WAV** first inspects the original. Choose a 0.1–4 second trim,
  gain, DC removal and circular crossfade. Trim/crossfade use **source frames**.
  Original files stay unchanged. Pinned private copies survive moving the
  external file. A missing or modified pinned copy fails validation.
- PCM WAV only: RIFF PCM, 1/2 channels, 8/16/24/32 bits, 11025–48000 Hz,
  maximum 8 MiB and 2 million source frames. MP3/OGG/FLAC/proprietary sound-bank
  imports are not advertised. Clipping from source gain is rejected.
- **Assign Existing** selects a pinned default/current/preset source and retains
  the destination layer's response. **Apply parameters** validates and saves.
- Engine gain changes its source waveform. Native stock-profile IDs 0–22 select
  qualified ordinary MR synthesis tables; actual RPM/rev limit still come from
  vehicle physics. This is not arbitrary GT multi-bank playback.
- Whine exposes reference RPM, pitch clamps, drive/coast gain, RPM fade and neutral
  mute. Spool exposes gain/pitch/RPM/load threshold and up/down smoothing. BOV
  exposes estimated pressure/release thresholds, gain, pitch variation, minimum
  RPM, cooldown and release decay. Bounds come from the same SDK schema as CLI.
- Engine disable is **audition-only**. Other layers can be disabled for a
  candidate. Spool disable sets its audible gain to zero while retaining its
  pressure-estimator controls for BOV; it still owns a native silent voice.

## Audition

Enter 1–8 RPM steps, audition rev limit, signed load (-1 coast to +1 drive) and
native gear index (**1 = neutral**). Enable scripted release to drop load in
the final third of the sequence. Mute/Solo only select audition tracks; they do
not change saved candidate enable flags. Render/listen, then Stop if needed.

The engine uses original x86 MR DSP from your hash-qualified executable, read
only, via Unicorn. Supplemental tracks preserve phase/spool/BOV state across
steps and use the established response simulation. Reports include source
pins, segment controls, signal levels, clipping counts and BOV event times.
Audition WAV/JSON files are saved in the project's `auditions` directory.
Browse for the original executable when the SDK checkout is not beside the game;
the file is read as DSP input and never launched or patched by audition.

**Approximation:** signed crank torque / peak torque is the native load proxy;
no physical boost pressure or verified throttle sensor is claimed. RPM steps
and scripted release are diagnostics. DirectSound device/spatial attenuation,
thread timing, listener position and the full race mix require game listening.
Use `pip install -e .[workshop]` for Pillow, NumPy and Unicorn 2.1.4.

## Presets, history and builds

Save a named preset, choose it from the combo and Load. Presets retain all four
sources/hashes, conversion settings, responses, provenance and enable flags.
Presets in linked Source Fidelity/Classic versions are listed with their origin;
loading is explicit, leaves the other version intact and rebinds destination
CarID/namespace. Newly rebuilt visual versions inherit audio overrides/presets
without changing their immutable default audio baseline. Importing from another
qualified addon also explicitly rebinds those identifiers; native allocation
addresses are never copied. Missing inputs fail without silent substitution.
Legacy author projects can retain author-slot ID27 internally; the established
roster builder binds this Lancer to runtime CarID28. Audio Studio respects that
qualified mapping rather than rewriting saved ID reservations.

**Reset layer** restores its imported default. **Restore audio** resets all
audio settings but retains named presets. Shared Undo/Redo and Restore all
include audio, paint, surface and crew layers. Save persists the project;
Validate/Build use existing SDK compilation and the configured isolated roster.
No installed game files are edited. Keep private MR/GT sounds out of source
archives and redistributable packages, including preset-associated files.

## CLI (same Core service)

```text
python tools/workshop_audio.py PROJECT inspect
python tools/workshop_audio.py PROJECT import engine LOCAL.wav --trim 0 24000 --gain-db -3
python tools/workshop_audio.py PROJECT save-preset "My audio"
python tools/workshop_audio.py PROJECT load-preset "My audio"
python tools/workshop_audio.py PROJECT import-preset OTHER_PROJECT "Other preset"
python tools/workshop_audio.py PROJECT audition OUTPUT.wav --solo bov_release --rpm 3500 4500 5500 3500
python tools/workshop_audio.py PROJECT restore
```

`apply LAYER JSON` accepts supported `audio_update` keyword fields only:
`source`, `response`, `enabled`, `stock_profile`. This passes through schema
validation. A source object requires a pinned, available WAV and its SHA256.
