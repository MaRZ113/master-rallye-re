# Private reproducible workflow

Run at the worktree root. Original assets stay outside it; all commands below
write ignored outputs. Choose new output names on reruns: overwrites fail.

```powershell
$gt='E:/Games/GT_Model-Tools'
$gt4="$gt/VOL/GT4-Beta_Extracted/extracted"
$gt3="$gt/VOL/GT3_Extracted/GT3.VOL"
python tools/gt_sound_lab.py --gt4-root $gt4 catalog --game gt4 --output scratch/gt_sound_lab/catalog-gt4.json
python tools/gt_sound_lab.py --gt3-volume $gt3 catalog --game gt3 --output scratch/gt_sound_lab/catalog-gt3.json
python tools/gt_sound_lab.py --gt4-root $gt4 vehicle --game gt4 --vehicle mits0015 --output scratch/gt_sound_lab/lancer.json
python tools/gt_sound_lab.py --gt4-root $gt4 inventory --game gt4 --output scratch/gt_sound_lab/inventory-gt4.json
python tools/gt_sound_lab.py --gt3-volume $gt3 inventory --game gt3 --output scratch/gt_sound_lab/inventory-gt3.json
```

Full inventories can take minutes. GT4 actually decodes the numeric ENGN
streams; GT3 audits every frame/loop/allocation grammar and decodes selected
samples on audition. Catalogs contain private database information and are
not source-only deliverables.

## Inspect, compare and export

```powershell
python tools/gt_sound_lab.py --gt4-root $gt4 inspect --game gt4 --bank carsound/engine/22601 --output scratch/gt_sound_lab/engine22601.json
python tools/gt_sound_lab.py --gt4-root $gt4 compare --game gt4 --bank carsound/normal3/22601 --other-bank carsound/turbo3/22601 --output scratch/gt_sound_lab/compare22601.json
python tools/gt_sound_lab.py --gt4-root $gt4 export --game gt4 --bank carsound/engine/22601 --sample-rate 24000 --output scratch/gt_sound_lab/engine22601-nominal
python tools/gt_sound_lab.py --gt4-root $gt4 export --game gt4 --bank sound_gt/sound/gt4race2.ins --entry 11 --sample-rate 24000 --output scratch/gt_sound_lab/explicit-split.wav
```

Select INST `--entry` from the current inspection's stable entry ID; do not
infer an event from the numeric example. ENGN CLI without `--entry` exports every band into a
new directory, with full/loop-only WAVs and bank.json. The browser exports
exactly the explicitly selected entry. For GT3 use the exact member and
entry_id reported by inspection, for example an ENGN `table0:0` or an INST
`voice:7`. All nominal rates are explicit authoring choices.

For one GT4 ENGN recording, add `--entry 4` and choose a new WAV output path.
The export preserves that entry's RPM and loop provenance. For qualified
named-event routing and export:

```powershell
$core3="$gt/VOL/GT3_Extracted/CORE.GT3"
python tools/gt_sound_lab.py --gt3-volume $gt3 --gt3-core $core3 events --game gt3 --output scratch/gt_sound_lab/gt3-events.json
python tools/gt_sound_lab.py --gt3-volume $gt3 --gt3-core $core3 event-export --game gt3 --event b_off --output scratch/gt_sound_lab/gt3-event-b_off.wav
python tools/gt_sound_lab.py --gt4-root $gt4 events --game gt4 --output scratch/gt_sound_lab/gt4-events.json
python tools/gt_sound_lab.py --gt4-root $gt4 event-export --game gt4 --event turbine2 --sample-rate 24000 --output scratch/gt_sound_lab/gt4-event-turbine2.wav
```

GT3 named-event export verifies its original CORE, GTSE and INST bank hashes
and uses the recovered leaf pitch word with a nominal 48-kHz SPU2 clock;
later native modulation and the complete mix remain outside that WAV. GT4
named-event export uses the supplied CORE's static first-split dispatch, with
an explicit nominal audition rate. Missing programs and unsupported sequence
routes refuse export. Event identity remains evidence about a native route,
not a subjective acoustic classification.

The following optional mode validates the exact reconstructed supplied GT4
CORE before applying its anchor pitch rule:

```powershell
python tools/gt_sound_lab.py --gt4-root $gt4 --pitch-core scratch/gt_sound_lab/native/core.elf export --game gt4 --bank carsound/engine/22601 --output scratch/gt_sound_lab/engine22601-anchor
```

For a fresh research workspace, reconstruct GT4 privately with the existing
`inspect_gt4_core.py ORIGINAL_CORE NEW_PRIVATE_DIRECTORY` recipe and optional
PyCryptodome. GT3 reconstruction is supported by
`gt3_sound_lab.py --core ORIGINAL_CORE --output NEW_PRIVATE_ELF`.
Neither reconstructed ELF belongs in an archive.

## Browser and tests

```powershell
powershell -ExecutionPolicy Bypass -File tools/start_gt_sound_lab.ps1
$env:PYTHONPATH='src;tools;.'
python -m unittest discover -s tests/synthetic -p test_gt_sound_lab.py -v
python -m unittest discover -s tests/synthetic -p test_gt_sound_jam.py -v
python -m unittest discover -s tests/synthetic -p test_gt3_sound_lab.py -v
python -m unittest discover -s tests/synthetic -p test_gt4_audio_extract.py -v
```

The server binds127.0.0.1 only and accepts its own Origin/Host. It does not
upload files or serve arbitrary filesystem paths. Output into original
source directories, link ancestors and existing output paths is rejected.
WAVs carry original loop metadata where admitted; automatic normalization,
resampling, cosmetic fades and inferred effect labels are not applied.
