# R5V-J.1 source review package

This archive contains the SDK source, native launcher project, generated-plan
tools, focused tests, documentation, and text validation output. It excludes
the retail executable, the research candidate executable, Data.sma and other
game assets, raw Broker dumps, user saves, screenshots, and generated runtime
resource packages.

## Reproduce the offline two-addon J.0 plan

Use Python 3.10 or newer. From the extracted source tree root, run:

```powershell
$env:PYTHONPATH = 'src'
python tools/mrtool.py addon validate `
  --manifest research/vehicles/sdk/examples/mercedes-ml320.json `
  --manifest research/vehicles/sdk/examples/r5v-qualifier-t2.json `
  --capabilities research/vehicles/sdk/capabilities/retail-2001.json

python tools/mrtool.py addon build `
  --manifest research/vehicles/sdk/examples/mercedes-ml320.json `
  --manifest research/vehicles/sdk/examples/r5v-qualifier-t2.json `
  --capabilities research/vehicles/sdk/capabilities/retail-2001.json `
  --output .research-output/vehicles/sdk/review-plan

python tools/mrtool.py addon verify .research-output/vehicles/sdk/review-plan
Get-FileHash -Algorithm SHA256 .research-output/vehicles/sdk/review-plan/addon-plan.json
```

Expected build and verification status is `PASS`, the plan hash is
`357d3cf10f32b63af27d28c23a858197d7eedbd0d7ef79e4deb2a63a6b170989`, and
`runtime_installable` remains `false`. The build writes semantic plans only;
the output is not a game-ready runtime package.

## Review the J.1 native integration

Read `research/vehicles/sdk/loader-decision.md`,
`research/vehicles/sdk/runtime-deployment.md`, and
`research/vehicles/sdk/j1-runtime-validation.md`. The focused J.1 unit tests
need the exact retail PE, which is intentionally not in this archive. Building
and verifying the full J.1 resource bundle also requires the qualified I.1
runtime package and retail data assets, which are external. The native launcher
project builds only on Windows x64 with CMake and MSVC; its tested candidate is
statically built but has not yet received a human game-startup or addon-runtime
qualification.

`archive-index.json` gives the SHA256 and byte size of every archive payload
except itself. The archive is source/evidence only; it contains no compiled
launcher or runtime package.
