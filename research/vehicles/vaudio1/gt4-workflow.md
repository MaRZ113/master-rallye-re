# Optional user-local GT4 engine sample workflow

No GT4 banks, tables, PCM or executable are bundled. Keep all extracted output
private and ignored. The generic SDK audio importer also accepts user-authored
PCM; it does not depend on this optional GT4 path.

Run from `master-rallye-re-vehicles`, branch `research/vehicles`:

```powershell
python tools/gt4_audio_extract.py mapping `
  --spec-folder '<user GT4 extract>/specdb/GT4_PREMIUM_US2560' `
  --car-label lancer_evo4_wrc_97 `
  --carsound-root '<user GT4 extract>/carsound' `
  --output .research-output/vehicles/vaudio1/gt4/mapping.json

python tools/gt4_audio_extract.py inspect '<user GT4 extract>/carsound/engine/22601' `
  --output .research-output/vehicles/vaudio1/gt4/bank-inspection.json

python tools/gt4_audio_extract.py extract '<user GT4 extract>/carsound/engine/22601' `
  --pitch-core scratch/scale1/gt4coreverified/core.elf `
  --output .research-output/vehicles/vaudio1/gt4/new-sourcepitch-extraction
```

The last mode admits only the previously reconstructed, exact-hash supplied
CORE and validates six native instruction words. For an unqualified CORE, use
`--sample-rate <explicit Hz>` instead; the result is marked nominal and no
native frequency proof is claimed. Outputs must be new directories. Source
banks are read only. Extraction preserves every admitted entry, emits full
and loop-only WAVs and `bank.json` with hashes, raw words, loop bounds, integer
rate, source provenance and approximations.

The first mapping is deliberately limited to the recovered US2560 table-key
layout; unsupported row sizes or table IDs fail. Other vehicles in the same
layout can use their own explicit generic-car label. New layouts must be
qualified rather than guessing byte offsets or matching numeric filenames.

For the present Lancer candidate, import
`engine22601-sourcepitch/table0-band04-loop.wav` through the shared MR audio
profile. Preserve the source file hash and explain the selected4000RPM band.
The MR importer may resample to its required native format; source extraction
does not resample. Use MR's supported RPM/playback controls and preserve a stock
fallback. Do not promise GT4 two-bank crossfades from one PCM source.

Synthetic regression:

```powershell
$env:PYTHONPATH='src;tools;.'
python -m unittest discover -s tests/synthetic -p test_gt4_audio_extract.py -v
```
