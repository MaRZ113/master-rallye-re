# V-AUDIO1 — independent native engine audio

Status: **ready for human audibility/gameplay testing**. No game was launched
to claim player/AI sound qualification during this phase.

## Implemented

An optional `audio-profile.json` in an SDK author project selects a pinned local
PCM input, explicit trim, gain/DC treatment and optional circular crossfade.
The shared project/compiler emits one canonical PCM16 mono48kHz WAV under
`DataAudio/vehicles/sdk/<namespace>/engine.wav`. Build/collection validation
checks identity, source provenance, encoding, hashes, declared file set and
namespace collisions. Stock audio files are never replaced.

A bounded appended native wrapper changes only the constructor's engine-name
interner for the exact **physical CarID**. It rereads native Race/CarN identity,
separate from the stock tuning selector and race slot. Stock tuning tables,
RPM response, spatial state, shift effects and teardown remain native. Ordinary
stock tuning cases0..22 are qualified; special Icecream/UFO cases reject.
No runtime capacity expansion is introduced. The collection path used here
remains its existing qualified ID27 integration; multi-profile ABI tests are
not a claim of new installed roster capacity.

The normalized engine control is verified from original angular RPM/revlimit
through public per-car state to the native synthesizer. Throttle changes audio
through engine physics; no separate throttle/load layer is invented.
See [native-map.md](native-map.md) for exact addresses, formats and limits.

## Authentic source and controlled adaptation

Original local GT4 Beta database keys identify the Lancer's **shared sound22601**.
Eight engine bands and the available matching tuning banks are decoded.
The selected input is engine band04, reference4000RPM, source loop17668 samples.
Its nominal rate21457Hz follows the pitch interpretation from the explicitly
comparative supplied Online-US CORE; exact historical Beta pairing is unproved.
See [GT4 source findings](gt4-source.md) and [extraction workflow](gt4-workflow.md).

This candidate uses **one authentic source band through MR's own granular DSP**,
not GT4's original two-bank multi-layer mixer. Manual -3dB gain and DC removal
precede48kHz conversion. No unrelated recording or permanent playback is used.
Original GT4 low/high/tuning crossfades are not transplanted; all eight decoded
bands remain private alternative authoring inputs.

Output engine WAV SHA256:
`b778f1aee0e51138e5c944269da7d49ca44d6bcb48713ee7eae11df4f953b8e4`.
39523 frames, peak22295, RMS about8881; source conversion does not clip.
The unchanged native synthesis filter can saturate, as it does for stock input;
offline raw DSP amplitude excludes in-game listener/SFX attenuation.

## Candidate selection

Private root: `.research-output/vehicles/vaudio1/`.

| Candidate | Physics basis | Intended use |
|---|---|---|
| `candidate-audio-fitment` | unchanged V-PHYS2 Fitment260 | Audio-only A/B against the user's last named launch |
| `candidate-combined-fitment` | corrected V-PHYS3 Fitment260 | **Recommended combined test**, same driving values as last named launch |
| `candidate-audio-only` | unchanged V-PHYS2 Handling260 | Independent Evo handling/audio A/B |
| `candidate-combined` | corrected V-PHYS3 Handling260 | Optional combined independent Evo handling |

Use `Launch-Audio.cmd` inside the selected candidate. Root convenience launchers
are clearly labelled. Audio-only controls intentionally retain their old ride
binding; select the combined package to test corrected default height as well.
Old Subaru, V6, SCALE1 and V-PHYS2 packages remain untouched.

## Preview and reproduce

The lightweight `vehicle_audio_preview.py` panel chooses an audio profile and
source folder, RPM and rev limit, reloads on each render and plays a one-second
audition. It executes original local x86 MR synthesis in Unicorn. It omits
DirectSound timing, listener distance, full race mix and physics load response;
no artificial independent throttle slider is presented as native behavior.
The panel self-test rendered successfully without playing audio automatically.

```powershell
python tools/build_vehicle_audio_profile_candidate.py `
 --project <your-project-with-audio-profile-and-private-WAV> `
 --output .research-output/vehicles/vaudio1/my-audio-candidate

python tools/vehicle_audio_preview.py --exe ../MRallye.exe `
 --profile <project>/audio-profile.json --source-root <project>
```

The existing3D Previewer launcher accepts `--audio-profile` and
`--audio-source-root` to open the panel beside the vehicle window. The panel uses the
loaded physics XML rev limit (6500 for Fitment, 7000 for Handling), with an
explicit `--audio-rev-limit` override when needed. Optional
audition requires Tk/Unicorn and the exact user-supplied MR executable; no
original DSP binary is bundled. The normal importer uses the standard library.
[Native workflow](native-workflow.md) includes CLI auditions and custom WAVs.
Custom user-provided input works without any GT4 database, bank or CORE.

## Checks and remaining human tests

- 552 original-callsite/ABI cases across23 ordinary tuning IDs, four race slots,
  two independently named addon sources and stock passthrough.
- Original RPM normalization/control/DSP replay produces distinct deterministic
  outputs at the tested RPMs, including zero and over-rev control clamping.
- Audio-only revision adds exactly one owned WAV: all228 prior game resources,
  physics, meshes, wheels, UI, stock sounds and previous native payload prefix
  remain byte-identical. Combined revision has the same property against its
  corresponding corrected V-PHYS3 baseline.
- Canonical WAV/import rejection, source pinning, path/link safety, collection
  ownership, full synthetic regressions, native allocation and sealed launch
  preflights pass. Final counts are in validation-summary.json.

Start with setup0/0mm and fresh candidate saves. Compare stock Navara and Lancer
timbre/volume; idle, gradual acceleration, high RPM, automatic/manual shifts,
lift-off, braking, reverse and handbrake. Include an AI Lancer alongside a stock
car, finish/Results and two race re-entries. Check for silence, stuck/constant
pitch, clicks, clipping, duplicate/misassigned sources or leakage to stock cars.
Then repeat damage/brake/reflection checks on the combined fitment package.

No on-disk EXE or graphics DLL changes. No commits, pushes, GT asset bundling
or publication. Source handoff excludes all extracted audio/model/texture data.
