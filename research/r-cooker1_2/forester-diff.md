# R-COOKER1.2 — Forester source and output handoff

## Read-only source inventory

The exact Forester source files currently present in the read-only Demo 9.3.1
corpus are:

| Output role | Source file | Size | SHA256 |
|---|---|---:|---|
| car | `DataGx/Vehicles/Forester/car.gxm` | 219,728 | `3d27573a2358f379de1c1914fb6a17ac525a5a709bd62ab824736d05ac4c2535` |
| complete | `DataGx/Vehicles/Forester/comlplete.gxm` | 257,541 | `3fa2cff8c100b66236b1f076c164a402ac199fe3502838e0bc18be8a381b790f` |
| wheel | `DataGx/Vehicles/Forester/wheel.gxm` | 27,272 | `2f1542430065108649a4629f613493de85332e15a7755dda96ce66d79ea3e48d` |

The source package also contains 24 `.gxi` files. Their names, sizes, and
SHA256 values are inventoried in [`prototype-results.json`](prototype-results.json).
This is an available-sidecar inventory; it does not assert which GXI is
referenced by each draw record.

The frontend source typo is intentional corpus evidence. In scratch only,
stage the `comlplete.gxm` bytes under the expected `complete.gxm` name; do not
rename or edit the authoritative corpus file. The operator reports this name
correction restored the frontend model at runtime.

The 9.10.0 corpus has no Forester vehicle directory, so it does not provide a
second source copy. It has no Forester directory from which to retrieve a
second set of GXI/GXM sources. There are no Forester DX files in the project's ignored
`inputs/9.3.1_dxForester/` or `inputs/9.10.0_dxForester/` directories yet.
The existing 9.3.1 `car.dx` (128,327 bytes, SHA256
`eb2909b1d623f9e053a11114fe1d6d17283495bf7cab902755f87d2ee299e7de`) and
`wheel.dx` (12,937 bytes, SHA256
`1e2fefdf5fdaa4eba94490a3287de2fbc14863b6812c5902ba8f4d3a089d3dd7`) are
listed for traceability only. They were not freshly produced for this paired
experiment, and `complete.dx` is absent; therefore none is treated as a
verified same-source output pair.

## Required output set

Generate all six DX files from the exact source bytes above:

```text
Demo 9.3.1: car.dx, complete.dx, wheel.dx   (expected revision 131)
Demo 9.10.0: car.dx, complete.dx, wheel.dx   (expected revision 135)
```

Keep each original demo installation and its corpus read-only. Use a separate
scratch clone for each cooker generation. If the cooker can only be triggered
by loading a registered model, stage the Forester GXM files in the same
existing package path in both scratch clones; `Jump` is present in both demo
corpora. Change no vehicle catalog, executable, or physics configuration.
The `car`, `complete`, and `wheel` source bytes
must be exactly the hashes above in both clones. Copy required texture-source
sidecars needed for loading into each scratch package and record their hashes;
do not substitute a different GXM because the 9.10.0 corpus lacks a Forester
directory. Remove only scratch DX cache files for the roles being recooked,
then trigger the ordinary resource load with that generation's original
cooker. If this staging method does not make the original cooker process the
staged sources, stop and report the exact limitation instead of changing the
roster or patching the executable.

Before sending outputs, record the actual source and output SHA256 values and
confirm the `car.gxm`, `complete.gxm`, and `wheel.gxm` hashes match between
the two scratch generations. A source-hash mismatch invalidates that role's
comparison.

Place generated files and source snapshots in ignored paths using these
names:

```text
inputs/9.3.1_dxForester/car.dx
inputs/9.3.1_dxForester/complete.dx
inputs/9.3.1_dxForester/wheel.dx
inputs/9.3.1_dxForester/car.gxm
inputs/9.3.1_dxForester/complete.gxm
inputs/9.3.1_dxForester/wheel.gxm

inputs/9.10.0_dxForester/car.dx
inputs/9.10.0_dxForester/complete.dx
inputs/9.10.0_dxForester/wheel.dx
inputs/9.10.0_dxForester/car.gxm
inputs/9.10.0_dxForester/complete.gxm
inputs/9.10.0_dxForester/wheel.gxm
```

Also include a small manifest with cooker generation, source path used in the
scratch tree, source hash, output hash, output size, and any sidecar hashes.
Do not add these proprietary files to Git.

## Why analysis stops here

Without both revisions generated from identical source bytes, it is
impossible to test whether Forester draw records follow the Trooper
11-byte-to-24-byte prefix formula. Therefore no Forester candidate was
generated, no canonical rev135 parse was attempted, and no runtime candidate
is ready. Once the paired outputs arrive, check every draw record first; a
single formula mismatch blocks conversion exactly as specified in the phase
gate.
