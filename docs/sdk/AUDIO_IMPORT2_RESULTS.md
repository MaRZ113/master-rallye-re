# Audio Import 2.0 + optional GT Sound Bank Lab integration

26 October 2026, `research/vehicles`. **Implemented and Windows/offline validated.
Actual Master Rallye audio listening remains PENDING OWNER.** Physics/Camera /
Vehicle Identity was completed first in `53fa708ed1e1a2290fe50ddc3a1286c1488faf28`;
its candidate and source-only review archive remain separate.

## Working application

Open `Rally-Workshop.cmd`, select the qualified addon, then Audio:

1. **Import Audio 2.0…** for ordinary supported local files.
2. **Find Sounds for This Vehicle… (optional GT)** for private bank inspection.
3. Compare, explicitly Apply a source to a selected layer, save a preset,
   Validate and Build. Existing Mute/Solo, engine-DSP audition and response
   controls remain unchanged.

Private evidence root: `.research-output/vehicles/audio-import2/`.
The final demonstration project is `win-final/gui-project`; its exact GUI build
is recorded in `win-final/windows-validation.json`. Private launch/open shortcuts
are provided in the evidence root. No game files are edited in place.

## Exact functionality and limits

| Capability | Implemented |
| --- | --- |
| Ordinary audio | Supported RIFF PCM through established decoder; optional ffmpeg/ffprobe for FLAC, MP3, Ogg Vorbis/Opus and additional WAV PCM/float variants. No GT dependency |
| Bounds | Original ≤64 MiB/30 s, mono/stereo; optional decoder supports admitted 8000–192000 Hz input and converts to mono PCM16/48000; native selected interval remains 0.1–4 s. Codec/container and output budgets enforced; 60 s subprocess timeout, file/pipe protocols only |
| Review | Target vehicle/CarID, source format/duration, original/decoded/native SHA, exact converter peak/RMS, decoded full-scale count, waveform/seam warning, source excerpt vs converted Play/Stop, trim/loop/gain/DC/crossfade |
| Apply | Separate action; project-owned report and byte/hash guards; parameter changes during or after decoding invalidate review. Existing native compiler output is compared exactly before committing |
| Ownership | Immutable originals, private original copies and decoded pins; four independent sources; existing per-layer response remains explicit. Missing target response defaults require a compatible preset; no invented native layer behavior |
| Reversibility | Save/Undo/Redo/Reset/Restore/reopen and named/rebound presets; same PCM from multiple banks retains separate layer origins; compatible visual versions retain new provenance |
| Optional GT | Lab catalog schema + original local GT3 VOL/CORE or qualified GT4 extracted data/optional CORE ELF. Verified IDs/model-code associations, shared IDs, default/alternate banks, RPM/loop/record/encoded-span hashes, explicit nominal/native rate and source-to-layer assignment |
| Named routes | GT3 qualified native enum/voice/leaf pitch; GT4 comparative direct first-split b_off/turbine/turbine2 and drivetrain consumer evidence. Native modulation/ADSR/LFO/spatial mix and exact acoustic identity are not reproduced |
| Failures | Missing/ambiguous IDs, stale catalog/bank, foreign preview, unsupported codec/INST, absent program15, missing required PCM and gain clipping reject explicitly. No silent source/synthetic substitution |
| Stock/native | Audio authoring remains qualified-addon-only. Stock passthrough, native sound hooks/DSP, owner lifetimes, per-CarID namespace and roster architecture remain unchanged |

Original playback is approximated deliberately: each engine import selects one
recording through MR stock synthesis, not GT's neighboring-RPM mixing or its
separate engine/tuned/road-noise streams. Whine/Spool/BOV use the already qualified
MR signed-load/estimated-pressure controls, not a newly invented GT boost sensor.
Native BOV remains a one-shot even when source metadata contains a loop.

Compressed/float decoding can introduce quantization, encoder-delay differences
or saturation before authored gain. Native gain clipping is checked exactly;
source saturation remains diagnostic. Import-time hashes/options are preserved
separately from later current compiler output after manual parameter changes.

## Lab reconciliation and provenance

Independent worktree remains read-only and at
`1dc5b16f44aa327345a8e4529b5b10414bd09e74` on
`research/gt-sound-bank-lab`. No merge, reset or rewrite was performed there.
The reviewed 24-file research change was reconciled into this phase:

- `gt4_spec.py` and `gt4_source.py` are identical to current main and were **not
  replaced**. Actual `master_rallye` and `addon_sdk` package initializers are
  unchanged; archive-only minimal shims were never copied over them.
- Shared `gt4_audio_extract.py` was reviewed: intentional shared body offsets
  retain every RPM record; native instruction identity uses equivalent SHA
  checks rather than copied instruction bytes. Matching synthetic test added.
- Lab parsers, optional standalone explorer, schema, research documentation,
  native-verification source and generated-fixture tests are preserved with
  origin hashes. New SDK adapter/configuration/UI call those parsers; no second
  bank decoder/database parser or new native mixer was created.
- Exports retain Lab commit, actual parser hashes, Core identity when provided,
  catalog/bank/encoded-span/WAV hashes, source records, RPM/loop metadata, explicit
  rate provenance and event association. GT3 decoded-member offsets remain
  separate from compressed RoFS locations. `authentic_effect_identity` remains null.

`lab-source-reconciliation.json` records the reviewed source files. The Lab's
**30/30 synthetic tests** were repeated in main. Its full numerical-bank corpus
audit and original native traces remain identified research evidence, not a
claim of newly repeated GT runtime listening or PS2 execution.

## Locally repeated source qualification

- Live GT4 catalog: **723 labels, 3572 banks, 384 Sound IDs**. Lancer
  `mits0015 → lancer_evo4_wrc_97 → ENGINE1605 → Sound ID22601`, shared by **11
  ENGINE rows**. Source row hashes and all nine available engine/normal/turbo
  variants were inspected. `engine/22601` has eight separately inspectable bands.
- Default-parts chain uses muffler +152 and statically suggests `turbo3` under
  the supplied CORE. Windows demonstration explicitly overrides it with
  `normal3/22601`, band2 at reference4000 RPM. Actual equipped tuning/historical
  Beta/Online-CORE pairing remains unconfirmed.
- Live GT3 source catalog: **244 CAR rows / 1215 bank members**. This is catalog
  qualification, not a repeated full 8500-span decode. No sb0097-to-CAR guess.
  The native b_off event export verifies admitted CORE/GTSE/INST identities and
  original leaf pitch with nominal SPU2 clock conversion.
- Repeated GT4 INST audit: **24 banks / 107 entries / 93 PCM-supported / 14
  unsupported**, all retained. Unsupported export rejects without output.
- `shift_change`: **DIRECT_PROGRAM_ABSENT**, program15; explicit refusal,
  preserved in `shift-change-blocker.json`. Original BOV producer thresholds,
  SE sequences and full native mixing remain unresolved/nonblocking.

## Candidate matrix and exact differences

`t/a`…`t/e` contain independent isolated candidate builds against accepted Source
Fidelity. Only the listed `DataAudio/vehicles/sdk/lancer_evo4/*.wav` resources
change. Geometry, DXT/UI, physics, camera, crew, damage, lights and other vehicles
are byte-identical. Native patch operation bytes are also **identical** in all
five builds. Generated WAVs/sidecars stay private.

| Case | Selected source | Changed WAVs |
| --- | --- | --- |
| A | GT4 turbo3/22601 band2, qualified comparative anchor pitch; explicit loop | engine |
| B | GT4 turbine2, race2 program12/split0; explicit nominal24000 Hz; source loop | transmission_whine |
| C | GT4 turbine, race2 program11/split0; explicit nominal24000 Hz; source loop | turbo_spool |
| D | GT3 b_off primary native voice; recovered leaf pitch; full one-shot | bov_release |
| E | All four, same independent source/response contracts | exactly four |

Conversion gain in this matrix is explicitly **−6 dB**, DC removal, original
forward loops for continuous layers; no circular crossfade added. Engine/Whine/
Spool/BOV native response values remain the accepted profile. The GUI combined
candidate uses the manually selected **normal3** engine variant; its other three
sources follow the same routes above. Its exact four-file report is separate.

Auditions under `t/auditions/` run original x86 MR engine DSP plus existing
supplemental response simulation. **The near-listener scripted E sum clips 2747
samples across four segments**; individual imported native WAV gain checks pass.
There is no hidden limiter or claim of game-perfect loudness. The audition omits
actual engine/SFX slider balance, attenuation and DirectSound device mixing;
listen later and adjust explicit gains as needed. Do not interpret this scripted
clipping as confirmed in-game clipping or as an automatic quality pass.

## Validation and regression evidence

- Full Windows checkout: **894 tests, OK, one optional fixture skip**. Nine new
  source-independent import/adapter tests plus the reviewed Lab tests cover
  ownership, clipping, loops, identity, catalog/hash drift, missing pitch proof,
  per-layer/preset origins and no GT dependency for ordinary PCM input.
- `win-final/codec-validation.json`: original WAV, FLAC, MP3, Vorbis, Opus and
  stereo float WAV96kHz, using installed **FFmpeg8.0.1 full build**. Every original
  hash unchanged; only selected layer output changes, then Undo restores.
- `win-final/windows-validation.json`: actual Tk windows, typed source settings,
  stale-result rejection, waveform and source/native playback calls, catalog /
  vehicle / alternate bank / event inspection, four explicit assignments, preset,
  Save/Undo/Redo/Reset/reopen, Validate and actual Build. Device calls are not a
  human listening judgment; gameplay remains pending.
- `t/matrix-validation.json`: 1/1/1/1/4 named resource diffs, sealed roster
  validators and identical native patch bytes. Standalone audition outputs.
- `windows-regressions.json`: repeated Material/Binding/reflection addon+stock
  candidates and zero-edit stock restoration; legacy Audio imports/presets/five
  auditions; full Physics/Camera/Details/Art GUI build; Paint/Crew; new Classic
  versions/approval gate; stock reference browser; 56 texture zoom captures.
- `cross-module-versions.json`: four GT imports preserve active physics/camera/
  names/aliases/art; RevLimit edits preserve sources/preset; Source Fidelity and
  Classic retain four per-layer origins without losing immutable defaults.
- `native-*`: original engine path/register ABI, interleaved two-owner native
  SFX lifetime, stock passthrough, re-entry, gain/neutral/spool/BOV controls,
  RX/RW protection and three optional allocation failures. Typed device/Broker
  mocks are explicit; no DirectSound/gameplay qualification.
- `preservation.json`: all **736** accepted Source/Classic resource hashes,
  EXE, graphics DLL, retail/installed SMA and independent Lab tree preserved.
  No source extraction data enters Git or review archives; no push/publication.

## Reproduce / owner checklist

Ordinary import needs a qualified addon and a local file; use the Audio dialog
or `tools/workshop_audio_import.py <project> prepare <audio>`, inspect the emitted
`import.json`, then `apply <report> <layer>`. Existing WAV/legacy tools still work.
For GT, configure an explicit source/catalog/Core with `gt-source`, then `find`,
`inspect-bank` / `event`, `export` and the same prepare/apply workflow. No manual
JSON editing is needed in the Windows application. Offline Help documents exact
source/decoded frame, pitch, loop and unsupported-record boundaries.

Future owner listening:

1. Launch each A–D alone, compare idle, acceleration, drive/coast and neutral.
2. Check spool smoothing and sustained-load lift/BOV without idle/shift spam.
3. Compare E at actual Engine/SFX slider settings; inspect loudness/headroom,
   clipping, source pitch and loop continuity. Single engine band is an MR
   approximation; no original GT orchestra parity is claimed.
4. Compare AI and stock/other addon sounds; exit, Results and race re-entry.
5. Reset/load presets and return to accepted baseline if desired. Test prior
   Classic and Physics candidates separately using their own checklists.

**Stop here for source/owner review.** No Heritage Garage, new vehicle, capacity
expansion, Blender Bridge, native multi-band player or unrelated audio refactor
was started. Current real-game listening remains deferred and nonblocking.
