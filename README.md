# Master Rallye RE

Clean-room interoperability and preservation research for *Master Rallye* (2001).

The repository contains only tools, documentation, machine-readable forensic
metadata, and synthetic test data. Original game resources remain external and
read-only.

## Current scope

Phase R0: asset archaeology and format mapping. R0 deliberately excludes
whole-program executable analysis and a production Blender importer.

## Reproduce R0 metadata

Run from this repository, with the extracted archive beside it:

```powershell
py -3 tools/scanner/inventory.py `
  --source "..\Data.sma_unpacked" `
  --inventory research/r0/inventory.json `
  --relationships research/r0/relationships.json

py -3 tools/scanner/text_map.py `
  --source "..\Data.sma_unpacked" `
  --relationships research/r0/relationships.json

py -3 tools/scanner/probe_dxt.py `
  research/r0/inventory.json `
  --output research/r0/dxt-probe.json
```

The generated paths are archive-relative; the external source location is not
embedded in the reports.

## Experimental tools

- `tools/prototypes/dx_mesh_probe.py`: parses only confirmed leading DX sections
  and emits diagnostic JSON. It intentionally does not emit faces while local
  draw-record vertex bases remain unresolved.
- `tools/prototypes/dxt_decode.py`: validates the custom DXT wrapper and writes a
  PNG with explicit `bgra`/`rgba` channel selection.

Run synthetic-only tests with:

```powershell
py -3 -m unittest discover -s tests\synthetic -v
```
