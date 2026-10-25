# Transmission source search and explicit fallback

The source search uses the unchanged local GT4 Beta extract and the previously
qualified supplied comparative Online-US CORE, SHA256
`962523fb4156aefa4e7d255c4937825614e0b99a9a48e94f1c9fcbe7c586c5c0`.
Its historical pairing with the Beta assets is unproved.

Bounded search records are private:
`.research-output/vehicles/vaudio2/gt-source-search.json` and ignored
`scratch/vaudio2/gear-refs.txt`. Search inspected all28 immediate
`sound_gt/sound` files, their exact hashes/headers, their gear/transmission
literals, the comparative CORE's defined ASCII sequences, the carsound
directory inventory and the relevant native data references.

The extract's carsound directories are `engine`, `normal0..3`, `turbo0..3`.
No independent named transmission directory was present. `sound_gt/sound/se.inf`
contains names including `shift_change`, `turbine`, `turbine2`, `in_car_l` and
`in_car_r`; these names do not identify a sustained transmission whine.
No unrelated effect has been relabelled as a transmission sample.

The supplied CORE contains a literal `GEAR` at file offset6258948,
VA`006F7130`. Ghidra12.1.4 with Emotion Engine Reloaded
`r5900:LE:32:default` reports a data reference at`006647B4` (also mirrored
addresses). Exact original data bytes show the array:

| Pointer address | Pointer value / string |
|---|---|
| `006647B0` | `006F7120` / `DRIVETRAIN` |
| `006647B4` | `006F7130` / `GEAR` |
| `006647B8` | `006F7138` / `ENGINE` |

Neighboring names run from`GENERIC_CAR`, `BRAKE`, `SUSPENSION` through
`CLUTCH`, `FLYWHEEL`, `PROPELLERSHAFT`, `LSD` and tyre tables. This is a SpecDB
table-name array, not evidence of an audio file. This pass analyzed original
table bytes/references; it did not infer PS2 instruction semantics from a PC
decoder. Opaque bank contents remain unclassified: the bounded negative search
does not prove that original GT4 never synthesizes or stores transmission noise.

The testable fallback is an original authored periodic loop, produced by
`tools/vehicle_whine_audition.py --synthesize`. It is explicitly synthetic and
contains no GT/MR sample. A4000RPM reference and12-tooth design choice give an
800Hz mesh tone, with second/third harmonics0.30/0.08 and40Hz phase modulation
of0.025rad. These numbers are not source-confirmed Lancer gearbox parameters.
Every component completes an integer number of cycles in one second.

```powershell
python tools/vehicle_whine_audition.py --synthesize --output .research-output/vehicles/vaudio2/authored-whine.wav
python tools/vehicle_whine_audition.py --resource PRIVATE_COMPILED_WHINE --profile PRIVATE_PROFILE --rpm 1000 --rpm 4000 --rpm 6000 --load 1 --load 0 --load -0.2 --output .research-output/vehicles/vaudio2/whine-audition.wav
```

Offline audition uses documented controls and continuous linear loop
resampling. It omits DirectSound spatial volume/cutoff, scheduling and full race
mix. V-AUDIO1's authentic engine22601 source and native engine DSP remain their
separate established path. A whine-disabled A/B profile omits the optional
declaration entirely, recovering the old process seams and resource set.
