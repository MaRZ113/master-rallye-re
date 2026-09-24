# Clean DXT regeneration experiment: Trooper 8.4.1

Status: original and offline reconstruction are **CONFIRMED_BY_BYTES** identical. A fresh runtime-generated DXT hash is **PENDING**. The user reports earlier DXT regeneration, but previously generated files had been present; the authoritative originals have since been restored. Do not use those older generated files as a baseline.

## Before launch: exact source identity

| Resource | Corpus-qualified relative path | Size | SHA256 |
|---|---|---:|---|
| GXI | `demo-8.4.1:DataGx/Vehicles/Trooper/Black-tga.gxi` | 1,032 | `f1e8c064908150ef3a0b354bfa2ae6de8493d2b43b895fb803987dc23cdac8a8` |
| Original DXT | `demo-8.4.1:DataGx/Vehicles/Trooper/black-tga.dxt` | 1,044 | `c8af53e3c1ea06c42178b3e1988dff0b3c64f150b722cba6bdd0450dc1357f82` |
| Offline reconstructed DXT | derived from the GXI above | 1,044 | `c8af53e3c1ea06c42178b3e1988dff0b3c64f150b722cba6bdd0450dc1357f82` |

GXI parses as 16×16 RGBA. Original DXT parses as 16×16 BGRA payload with header `edfe000001000000f6e53f6b1000000010000000`, version word 1, CRC32 `0x6b3fe5f6` (valid), and payload SHA256 `9503245a0161a939de15c2414db2d336e761822fa6cff8136e4148f58f1f782e`. Offline reconstructed payload and complete file match the original. The ignored metadata report is `.research-output/r-demo/runtime-tests/texture-baseline.json`.

## Scratch runtime protocol

1. Make a separate runnable copy of demo 8.4.1 outside the authoritative corpus. Confirm that its `Black-tga.gxi` and `black-tga.dxt` SHA256 match the table before removal. Record the scratch path and process version.
2. In that scratch copy only, remove `DataGx/Vehicles/Trooper/black-tga.dxt`. Keep `Black-tga.gxi`. Start Debug capture before launch if possible.
3. Launch the demo, display Trooper in the vehicle selection screen, start a race with Trooper, then exit cleanly. Record whether the texture is visibly requested and whether Debug mentions its exact path.
4. Hash the new scratch DXT if one appears. Preserve that generated file outside Git and run the comparison tool below. If no DXT appears, record the negative result and paths without asserting that the game never regenerates DXT.

```powershell
$env:PYTHONPATH = 'src'
python tools/scanner/r_demo_texture_compare.py --corpus-id demo-8.4.1 --corpus-root 'D:\Game\Master Rallye\corpora\demo-8.4.1' --gxi 'DataGx/Vehicles/Trooper/Black-tga.gxi' --original-dxt 'DataGx/Vehicles/Trooper/black-tga.dxt' --scratch-root '.research-output/r-demo/runtime-tests' --regenerated-dxt '.research-output/r-demo/runtime-tests/run-8_4_1/DataGx/Vehicles/Trooper/black-tga.dxt' --output '.research-output/r-demo/runtime-tests/texture-three-way.json'
```

Adjust `--regenerated-dxt` to the actual separate scratch copy path, and set `--scratch-root` to its common ignored parent if needed. The tool refuses a regenerated path under the authoritative corpus. Record original/offline/runtime full hashes, payload hashes, CRC validity, header-field differences and the three-way verdict. Runtime result remains **UNKNOWN** until that file or its complete comparison report is supplied.
