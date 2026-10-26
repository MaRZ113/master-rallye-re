# Audio Import 2.0 and optional GT sources

Open a qualified addon in Audio Studio. The existing native engine, Whine,
Spool and BOV configuration remains the playback authority. Stock audio authoring
is unsupported; ordinary stock passthrough stays intact. Importing sounds does
not edit physics, cameras, names, models, materials or the installed game.

## Ordinary local files — no GT game needed

Choose **Import Audio 2.0…** and select a local sound. Bounded RIFF PCM WAV uses
the existing SDK decoder. Optional **ffmpeg + ffprobe on PATH** enable verified
FLAC, MP3, Ogg Vorbis/Opus and additional PCM/float WAV decoding. The local decoder
version is recorded. No decoder executable or proprietary recordings are bundled.
If unavailable or unsupported, a clear error is shown; no replacement sound is
invented. The original **Import Local WAV…** workflow also remains available.

Current guards: original file ≤64 MiB, duration ≤30 seconds, mono/stereo; decoded
frame budget and a 60-second decoder timeout. Select a **0.1–4 second** native
interval. The optional decoder downmixes/resamples to mono PCM16/48000 Hz; existing
supported PCM WAV keeps the established SDK conversion path. MP3/Ogg encoder
delay, decoder rounding, float quantization and source saturation can affect the
decoded result; a compressed recording is not a bit-exact original PCM archive.

The dialog shows target vehicle/CarID and lets you select any of its four
qualified layers. Trim endpoints are **decoded source frames**, end-exclusive.
Gain, DC removal and circular crossfade use the existing native-resource compiler.
**Use original forward loop** explicitly selects a supported RIFF smpl loop and
maps endpoints when resampled; unsupported loop types are reported, not guessed.
Circular crossfade shortens the selected interval by its overlap. BOV always
plays once; source loop metadata does not turn its native trigger into a loop.

1. Set trim/loop/gain and **Prepare / refresh comparison**.
2. Compare the decoded/downmixed source excerpt with the **actual converted
   native WAV**. Play either, inspect their waveforms, formats, hashes, peak/RMS,
   full-scale sample count and seam warning. Playback uses ordinary Windows
   waveform audition, not the game mixer.
3. Changed settings invalidate the comparison, including edits during decoding.
   Prepare again. Native gain clipping rejects Apply until corrected. Source or
   decoder saturation is a separate limitation; a zero native clip count does
   not prove an unclipped encoded original.
4. **Apply reviewed source to selected layer** changes only that layer's source
   and import provenance, preserving its response controls and native identity.
   Disabled layers stay disabled. An absent layer needs a qualified response
   preset first; imports do not invent native behavior.
5. Save a named Audio preset, reopen, Validate and Build a private candidate.
   Undo/Redo/Reset/Restore remain shared actions. Exact source hashes and
   import-time conversion settings survive; later gain edits have separate
   current compiler hashes. Identical PCM from different banks retains distinct
   per-layer origins rather than overwriting another layer's association.

Original files remain unchanged. Private original copies, decoded pins, previews
and provenance stay inside the Workshop project. Builds use pinned PCM sources
and do not require the original compressed file or GT installation at runtime.
Missing required PCM pins reject validation. Source inspection still requires its
explicit original game/catalog inputs; it never substitutes another bank.

## Optional GT Audio Source Adapter

Choose **Find Sounds for This Vehicle… (optional GT)**. This is a read-only source
browser over the independently qualified GT Sound Bank Lab parsers. Configure:

- GT4: user-owned extracted root with the qualified Beta/US2560 spec database and
  carsound banks; optional already-qualified reconstructed CORE ELF for anchor
  pitch evidence. Other layouts are not automatically supported.
- GT3: original user-owned RoFS VOL; optional qualified original CORE.GT3 for
  native event/leaf-pitch evidence.
- An existing private `gt-sound-bank-lab/1` catalog, or generate a new project-local
  catalog. Neither database contents nor source banks belong in SDK distribution.

Load the catalog. Enter an **exact source vehicle ID**, or a source-verified GT4
model code, then **Find sounds for this vehicle**. GT3 short mesh codes such as
sb0097 have no qualified CAR join; choose a real CAR label explicitly. Source
IDs and GT Sound IDs are not MR CarIDs and never alter runtime registration.

Inspect shared Sound IDs, original row/hash evidence, source RPM records, missing
variants and static default tuning candidates. Select another engine/normal/turbo
bank freely; suggestions are not an assertion of the game's current equipment.
For the qualified Lancer, mits0015 maps to lancer_evo4_wrc_97, ENGINE1605,
Sound ID22601 shared by eleven ENGINE rows. The supplied-CORE default-part rule
suggests turbo3, but historical Beta pairing and actual saved equipment are not
runtime-confirmed. Explicit selection wins.

Select a bank and one **PCM_VALID** entry. The inspector preserves original
records, sample offsets, encoded hashes and loops. In GT3, sample_file_offset is
inside the decoded member; a compressed RoFS member's stored location is separate.
Do not add these offsets together. Unsupported INST/loop/sequence entries remain
visible and cannot be exported as some other recording.

## Named source routes and pitch

**Inspect named route** exposes qualified source associations for turbine2,
turbine and b_off. GT4 turbine2 has recovered continuous drivetrain/gear/speed
control evidence; this does not prove a particular real-world acoustic identity
or reproduce its complete procedural control in MR. GT4 shift_change program15
is absent in the sampled Beta race2 bank: export is explicitly refused, with no
neighboring sample or synthesized replacement. GT3 native event routing requires
the exact qualified CORE, GTSE and INST identities.

Choose **nominal** and an explicit 8000–96000 Hz rate, or **native** where the
qualified leaf/anchor evidence supports it. GT4 INST event pitch remains nominal;
GT4 ENGN anchor pitch requires the admitted CORE. GT3 native engine/event pitch
uses recovered leaf rules at a nominal SPU2 48000-Hz clock. Full envelopes,
modulation, Doppler, build pairing and actual game mix remain unqualified.

Export a private audition, play it, then **Use in Audio Import 2.0…**. This opens
the same ordinary review/conversion dialog. Pick Engine, Whine, Spool or BOV
explicitly. A source label is not an acoustic classifier. Engines are **one
selected recording through MR stock synthesis**, not GT's multi-RPM orchestra
or its engine+tuned+road-noise stream combination. Native multi-band playback is
a separate future qualification.

Bank, decoded/encoded spans, source build/Core/parser hashes, catalog, RPM/loop,
rate provenance, event route, user choice and conversion hashes are retained.
Changing source files/catalogs after inspection fails safely. The source window
belongs to its vehicle; switching projects requires reopening it rather than
silently applying edits to another car. A different car may explicitly import
a compatible Audio preset with destination CarID/namespace rebinding.

## Listening and diagnostics

Use the existing Engine/Whine/Spool/BOV Mute/Solo and combined native-DSP audition
after assignment. Signed crank torque/RPM and estimated pressure remain the
qualified MR inputs; no physical boost/throttle sensor or exact GT trigger is
invented. The scripted near-listener sum can clip even when individual WAVs do
not. Read **Clipped** counts, lower authored gains if appropriate and audition;
there is no hidden automatic normalization. Spatial/DirectSound/game timing and
actual race loudness require owner listening, not offline claims.

Test idle, acceleration, neutral, drive/coast, spool-up/down and sustained-load
release/BOV without spam; compare all-layer loudness, stock/AI isolation,
race exit/re-entry and Results. Current D3D8 listening is **PENDING OWNER**.
