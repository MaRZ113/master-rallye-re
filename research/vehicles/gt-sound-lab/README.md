# GT Sound Bank Lab

Private, source-qualified GT3/GT4 audio research, 2026-10-26. Worktree:
`D:/Game/Master Rallye/master-rallye-re-gt-sound-lab`, branch
`research/gt-sound-bank-lab`, based on `research/vehicles` commit `295e353`.
The developer's dirty Workshop files in the vehicles worktree were not changed.

The explorer connects vehicle database keys to original banks and individual
recordings. It preserves sample offsets, hashes, raw metadata, loops, shared
recordings and uncertainty. A decoded recording is not a complete game engine
sound. There was no PCSX2 driving or subjective listening qualification.

## Results and reports

| Deliverable | Location |
|---|---|
| GT3 architecture, database and INST | [gt3-architecture.md](gt3-architecture.md) |
| GT4 database, banks and RPM entries | [gt4-architecture.md](gt4-architecture.md) |
| GT4 native orchestration | [gt4-native.md](gt4-native.md) |
| Turbo, release, drivetrain and shifts | [events-drivetrain.md](events-drivetrain.md) |
| Reproducible private workflow | [workflow.md](workflow.md) |
| Machine contract and Audio Studio handoff | [integration-handoff.md](integration-handoff.md), [mapping.schema.json](mapping.schema.json) |
| Checks, scope and unresolved boundaries | [validation.md](validation.md) |

Raw database mappings, inventories, WAVs, original/reconstructed executables,
Ghidra projects and disassembly stay under ignored `scratch/gt_sound_lab/`.
Source-only archives live under ignored `.research-output/vehicles/gt-sound-lab/`.
They contain no original banks, database rows, decoded audio, executable files
or private native exports. Nothing was pushed or published.

## Run

Python 3.10+ and its standard library suffice for the explorer and synthetic
tests. Optional native evidence verification uses the already installed
Ghidra 12.1.4 Emotion Engine Reloaded and Rabbitizer. Optional GT4 CORE
reconstruction also needs PyCryptodome; the explorer can run at explicit
nominal audition rates without it.

```powershell
powershell -ExecutionPolicy Bypass -File tools/start_gt_sound_lab.ps1
```

This uses the authorized `E:/Games/GT_Model-Tools` corpus and prints a loopback
URL. Open that URL, choose GT3 or GT4, filter a vehicle label/model, inspect a
bank and select a PCM-valid entry. The optional `-PitchCore` argument admits
only the exact qualified GT4 reconstructed CORE. Each audition saves its WAV
and provenance sidecar in a new private run directory. Stop with Ctrl+C.

All available variants are inspectable. A native-derived default tuning bank
is a documented static candidate; current saved-game equipment and full
runtime selection remain separate. Shared event banks have no automatic
per-vehicle attribution. Unsupported entries are retained and export refuses
them. Missing files are not replaced with unrelated sounds.

The Lancer regression is unchanged at its core: `mits0015` /
`lancer_evo4_wrc_97` -> ENGINE row1605 -> Sound ID22601. Eleven ENGINE rows
share that ID. The corrected original default parts chain also reaches
MUFFLER table20 at DEFAULT_PARTS+152, category3, and turbine wastegate12;
the supplied CORE's rule consequently predicts `turbo3` alongside `engine`.
