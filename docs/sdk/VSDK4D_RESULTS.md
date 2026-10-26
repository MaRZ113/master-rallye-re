# V-SDK4D — Audio Studio Foundation

26 October 2026. Repository `research/vehicles`. **Implemented and Windows/offline
validated; actual Master Rallye listening remains PENDING.** V4B.1's owner
Source-versus-Classic gameplay comparison remains a separate, nonblocking gate.

## Implementation and exact functionality

| Capability | Scope / evidence |
|---|---|
| Four-layer authoring | Engine, Whine, Spool, BOV through shared `AudioAuthoring` project service; GUI and CLI use identical methods |
| Local source import | Qualified RIFF PCM WAV, bounded parsing, explicit trim/gain/DC/crossfade, untouched originals, content-pinned project copies |
| Inspection | Current source/provenance, original PCM dimensions/duration, output canonical format, full hashes, peak/RMS, loop warnings, clipping rejection |
| Assignment | Existing default/current/preset source picker, preserving destination response |
| Parameters | Existing native-supported schema only; `RESPONSE_BOUNDS` now shared by validator and GUI |
| Enable flags | Engine remains active in candidates. Whine/BOV omission supported. Spool uses zero gain when disabled, retaining BOV estimator behavior |
| Audition | Original local MR engine DSP plus existing signed-load supplemental simulation; continuous phase/spool/BOV state over RPM sequences, drive/coast/neutral, release, Mute/Solo and mixed PCM/JSON outputs |
| Presets | Named per-project presets, linked style-version discovery, explicit cross-addon/version import with destination CarID/namespace rebinding, original baseline retained |
| Save/history | Project persistence, shared Undo/Redo/Restore all; audio-only restore/reset keeps named presets |
| Build | Existing author compiler and qualified 30-entry roster; private project snapshots freeze audio sources like other author inputs |
| Stock audio | Authoring deliberately unavailable for stock/family-only or addon projects without a qualified custom-audio baseline; passthrough preserved |
| Unsupported | MP3/OGG/FLAC, automatic GT sample attribution, arbitrary multi-bank GT engine, physical boost/throttle signal, stock Audio Studio overrides |

Code: `workshop/audio.py`, `audio_ui.py`, existing `service.py`, `gui.py`,
`tools/workshop_audio.py`. The existing import/compiler is reused; no alternate
GUI PCM conversion or replacement sound engine was introduced. Native engine,
supplemental hook code, voice allocator/lifetimes and register-preservation
implementations are unchanged.

## Audio architecture audit

- `addon_sdk/audio_profile.py`: pinned per-addon engine and optional source WAVs;
  namespace-derived resource names; canonical mono PCM16/48 kHz conversion.
  Existing gain guards, circular crossfade, resampling and clipping rejection
  remain unchanged. Response bounds were extracted into a shared constant only.
- `addon_sdk/project.py::_audio_artifacts`: profile/manifest tuning agreement,
  author-slot binding and existing runtime roster CarID rebinding. Audio Studio
  changes the private working project, never a donor or installed resource.
- `vehicle_audio_native.py`: original engine-name constructor interception with
  verified original-byte and executable guards; synthesis/control tables remain
  native. Audio Studio does not change this code.
- `vehicle_whine_native.py` / `native_audio/layers.c`: separate namespaced voices,
  actor/owner state, writable data ranges, constructor/publication/update/cleanup
  seams, failure handling, existing clock and ABI/register guards preserved.
- `audio_response.py`: estimated spool and BOV load-release proxy; RPM and signed
  crank torque / peak torque are qualified inputs, not a boost/throttle sensor.
- `vehicle_audio_audition.py`: original x86 DSP in Unicorn. `vehicle_audio_layers`
  now additionally supports continuous response state across scripted segments;
  legacy single-segment audition behavior is unchanged.

## Five isolated Lancer candidates

Private local root: `.research-output/vehicles/vsdk4d/t/`.
Each case has `candidate/Launch-SDK-Roster.cmd`, a source project under
`t/projects/<case>`, and `roster-validation.json`. Full hash pairs:
`t/matrix.json`.

| Case | Deliberate replacement | Changed game resource paths |
|---|---|---:|
| A (`t/a`) | Engine only | 1 |
| B (`t/b`) | Transmission Whine only | 1 |
| C (`t/c`) | Turbo Spool only | 1 |
| D (`t/d`) | BOV only | 1 |
| E (`t/e`) | All four | 4 |

These are **original generated demonstration tones**, explicitly not attributed
GT recordings or a new production audio tune. The original Lancer engine and
synthetic defaults remain available in `t/projects/base` and via Reset/Restore.
The accepted Source Fidelity candidate is the comparison baseline. Complete
resource-root byte comparisons require exactly the chosen WAV differences;
all geometry, material, physics, camera, UI, crew, brake-light, wheel, damage,
Subaru, Pajero and stock resource paths match. No options-file exception was
needed for this comparison. Runtime launcher/manifest metadata is regenerated
normally. Candidate source snapshots remain independent of later GUI Restore.
The generated native patch operation files also match the accepted baseline
byte for byte for all five source-only experiments. Existing legacy author-slot
IDs are preserved; the qualified roster binds Lancer to runtime28 and Pajero29.

Open `.research-output/vehicles/vsdk4d/Open-Audio-Studio.cmd`, or the normal
`Rally-Workshop.cmd` and choose the newly registered original-audio Lancer
project. The customized E project is also registered. Existing library entries
are preserved.

## Validation evidence

Private evidence stays under `.research-output/vehicles/vsdk4d/`:

- `t/matrix.json`: five successful isolated builds and exact resource differences;
  five SDK roster validators pass. This preserves qualified 30-entry composition,
  not an expansion or new live player/AI capacity claim.
- `win-release/windows-validation.json`: actual Tk import dialogs (including
  format/trim UI), source assignment picker, four parameter panels, Save,
  diagnostics, Undo/Redo, Restore, reopen, presets, validation and five GUI
  native-DSP/SFX auditions. Actual Windows PNG captures accompany the report.
- `native-engine-28.json`, `native-multi.json`, `native-sfx.json`: original x86 callsite/engine and
  multi-owner SFX CPU replay. Two custom owners plus stock passthrough, optional
  protected memory/register/ABI behavior and reentry exercised;
  24 voices freed in lifecycle replay. The second custom profile is a CPU-only
  fixture at 29, **not a Pajero audio edit**. Interner/Broker/allocator/clock
  stubs and excluded Windows SEH prologue are stated in the evidence.
- `native-optional-failure.json`: allocation failure injected separately for each
  of three optional voices. Surviving voices update and free correctly; reentry
  recreates all three without stale publication. Missing WAVs fail authoring
  validation. Missing DirectSound buffers/device failures still require runtime
  qualification; allocation injection does not claim device-loss coverage.
- `audition-final/`: seven standalone engine/whine/spool/BOV/combined/coast/neutral
  WAV+JSON pairs. Peaks respectively 5612/1343/1318/2930/8401/6203/8401 PCM16;
  zero mixed clipping. BOV solo/combined/neutral scripts each produce one release
  event; coast produces none. These are scripted diagnostics, not human gameplay
  listening or DirectSound device/spatial/timing parity.
- `reg/gui-validation.json`: actual Windows material RGB/binding/reflection,
  replacement, history/reopen, addon and stock builds and restored stock
  zero-override build pass.
- `paint-reg2/validation.json`, `style-reg/validation.json`, `zoom-reg/validation.json`:
  actual Paint/Crew, Classic generation/source navigation/approval gate and
  embedded/detached texture zoom regressions. Frozen old candidates are unchanged.
- `reference-reg/validation.json`: local stock material-reference browser and
  texture-binding impact/Undo. `classic-qualified/validation.json` repeats the
  frozen Classic recipe twice, compares exact outputs and replays native damage
  using private project clones; no extra style conversion was approved or installed.
- Full synthetic Windows checkout suite and final preservation hashes are recorded
  in `tests-release.log` and `preservation.json`; exact final count is in the commit
  ledger. No original EXE, graphics DLL or retail resource changes.

Intermediate harness issues were corrected before acceptance: a same-value
`addon.json` reserialization was removed; a keyword-only test build invocation
was corrected; an already-painted old regression fixture was reset in a private
clone before repeating the visible-paint test. No failed attempt is counted as a
pass. Earlier scratch captures are retained separately from final evidence.

## Owner listening checklist (all pending)

1. Compare original baseline and A at identical Engine/SFX slider settings: idle,
   rising/falling RPM, shifts and acceptable combined loudness.
2. B: accelerate/coast, neutral behavior, no interruption of the engine voice.
3. C: sustained load builds spool, lift decays it; neutral follows profile policy.
4. D: one pressure-release after sustained high load, none at idle/low load;
   rapid shifts/releases do not spam or overlap one-shots.
5. E: four simultaneous layers, player and AI isolation; stock cars unchanged.
6. Race exit → Results → race reentry, repeat vehicle changes; confirm no stale
   or missing voices. Check braking/damage/crew/fitment/UI remain as accepted.

Audition does not reproduce listener attenuation, menu sliders, DirectSound
timing or full race mixing. Source Fidelity/Classic owner visual comparison is
still pending independently. No fourth import, Blender Bridge, further Classic
generalization, capacity expansion, physics change, push or release was begun.
