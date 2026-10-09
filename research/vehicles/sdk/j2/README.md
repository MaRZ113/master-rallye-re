# R5V-J.2 two-addon runtime qualification record

This folder records the 2026-10-09 Observatory evidence for the single
combined Mercedes ID26 + R5VQualifier ID27 J.1 runtime bundle, its static
composition checks, and the remaining human release gates. It contains no raw
Broker dumps or proprietary game resources.

The derived machine-readable capture summary is
[`runtime-evidence-2026-10-09.json`](runtime-evidence-2026-10-09.json); every
raw dump SHA/length was rechecked from the owner-supplied archive. The detailed
interpretation and limits are in [`runtime-evidence.md`](runtime-evidence.md).

## Reproduce the offline two-addon plan

Use Python 3.10 or newer with the full repository checkout. The planning path
uses the Python standard library. From the checkout root, in PowerShell:

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
  --output .research-output/vehicles/sdk/j2/reproduced-plan

python tools/mrtool.py addon verify .research-output/vehicles/sdk/j2/reproduced-plan
Get-FileHash -Algorithm SHA256 .research-output/vehicles/sdk/j2/reproduced-plan/addon-plan.json
```

Expected result: `PASS` and plan SHA256
`357d3cf10f32b63af27d28c23a858197d7eedbd0d7ef79e4deb2a63a6b170989`.
The output remains a semantic offline plan with `runtime_installable=false`.
Reproduce the focused SDK checks with:

```powershell
python -m unittest discover -s tests/synthetic -p 'test_addon_sdk*.py' -v
```

The native runtime candidate itself is not emitted by this plan build. Its
current combined package and exact hashes are documented in
[`bundle-audit.md`](bundle-audit.md); validating or launching it requires the
ignored local J.1 output and the user's pristine game installation.

## Review-package boundary

The compact source/evidence ZIP under `research/vehicles/sdk/archive/`
contains SDK source, manifests, selected tests, docs, static reference-plan
outputs, hashes, and text test output. It omits the retail EXE, launcher
binary, Data.sma, DX/DXT resources, raw Broker dumps, user profiles/saves,
screenshots, and compiled runtime packages.

J.2 is **PARTIAL_RUNTIME_CONFIRMED / READY FOR REMAINING HUMAN GATES**. Do not
start J.3 or ID28 from this record.
