# R5V-J.3 implementation review package

This source-only archive contains J.3-A donor-based authoring and the J.3-B
bounded native/resource collection compiler, focused tests, reference
capabilities and metadata-only addon examples, J.2 closeout evidence, and
validation logs. It excludes retail executables, launcher binaries, Data.sma,
DX/DXT content, saves, raw Broker dumps, screenshots, and generated runtime
packages.

## Reproduce offline reference plans

Use Python 3.10 or later. From the archive root, set the source import path:

```powershell
$env:PYTHONPATH='src'
python tools/mrtool.py addon validate --manifest research/vehicles/sdk/examples/mercedes-ml320.json --manifest research/vehicles/sdk/examples/r5v-qualifier-t2.json
python tools/mrtool.py addon build --manifest research/vehicles/sdk/examples/mercedes-ml320.json --manifest research/vehicles/sdk/examples/r5v-qualifier-t2.json --capabilities research/vehicles/sdk/capabilities/retail-2001.json --output .research-output/j3-reference-plan
python tools/mrtool.py addon verify .research-output/j3-reference-plan
```

Expected reference `addon-plan.json` SHA256:
`357d3cf10f32b63af27d28c23a858197d7eedbd0d7ef79e4deb2a63a6b170989`.
This command creates an offline semantic plan only; it does not create a
runtime-installable package.

## Reproduce the bounded runtime plan

The source-only archive intentionally omits proprietary executable/assets and
the user-owned donor package. With those exact external inputs and their
qualified project build available, follow
[`runtime-compiler.md`](runtime-compiler.md) to run `runtime-prepare`,
`runtime-verify`, and `runtime-launcher-build`. The recorded Glacier bundle
used 42 validated model/texture resources plus the pinned I.1 stock baseline;
no donor files are in this archive. The compiler rejects ID27/T2-only input
instead of adding Mercedes implicitly.

## Reproduce the author project

The metadata-only Glacier Sprint project is under
`research/vehicles/sdk/examples/glacier-sprint-t2-project/`. Supply a
user-owned, compatible donor asset directory by editing its local
`vehicle-project.json`, then run:

```powershell
python tools/mrtool.py addon project-validate <project-dir>
python tools/mrtool.py addon project-build <project-dir> --output <new-output-dir>
python tools/mrtool.py addon verify <new-output-dir>
```

Optional `--retail-data-sma` and `--retail-data-root` inputs enable independent
physics-family XML generation. Both must be the exact pinned retail archive
and a byte-matching unpacked tree. Do not copy a proprietary donor package into
the review archive.

## Tests

The archive includes the source files and focused tests used by the recorded
J.3 validation. J.1/J.2 tests that need the proprietary retail executable will
skip when that external fixture is absent. See
`research/vehicles/sdk/j3/validation.md` for actual test counts and the full
suite's two sandbox-limited cases. The focused-test dependency closure includes
the first-party AI/audio/build helpers, the read-only resource inventory tool,
and the small derived stock-audio profile matrix; it excludes raw game data
and Ghidra databases. `archive-index.json` records SHA256 and size for every
other file in this ZIP.

Run the focused group from the archive root with Python 3.10+:

```powershell
$env:PYTHONPATH='src'
python -m unittest tests.synthetic.test_addon_collection_runtime tests.synthetic.test_addon_sdk tests.synthetic.test_addon_sdk_project tests.synthetic.test_addon_sdk_runtime tests.synthetic.test_addon_sdk_j2_composition tests.synthetic.test_j2_frontend_reentry -v
```

This command was also run against an extracted copy of the review archive. It
ran 42 tests: 40 passed and 2 skipped because the source-only archive
intentionally excludes the retail executable and verified J.1 runtime bundle
needed by those two test classes. The reproduction log is included in the
validation output.
