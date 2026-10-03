# R-COOKER3 Retail Source Cooker V1

## Responsibility

The Source Cooker produces a portable vehicle resource package:

```text
DataGx/Vehicles/<family>/
    complete.dx
    car.dx
    wheel.dx
    required *.dxt
```

It does not create vehicle IDs, menu slots, unlocks, AI entries, frontend art,
or physics configuration. Vehicle Composer and later registry work remain
separate consumers.

## Strategy flow

```text
source inventory + hashes
        |
        +-- all usable GXM roles --> isolated retail-native human cook
        |
        +-- all supported rev131 DX --> canonical R-COOKER2 adapter
        |
        +-- all supported rev135 DX --> validate and pass through
        |
        +-- rev127 DX only / mixed / unknown --> fail closed
        |
texture closure: valid DXT reuse, else existing offline GXI encoder
        |
format + collision + texture validation
        |
cache-only package + provenance manifest
```

GXM validation currently establishes supported material, geometry, and
triangle prefixes. The hierarchy/tail remains opaque. Retail-native support
is runtime-confirmed only for the exact Mercedes source and cook harness
described in the oracle records.

## CLI

Run from the repository root with `PYTHONPATH=src` (or install the project in
editable mode):

```powershell
python -m master_rallye.source_cooker --help
python -m master_rallye.source_cooker inventory --source <vehicle-folder> --family <name> --json <manifest.json>
```

For GXM, `vehicle --output` creates a fresh cook-job directory, not a final
package. It requires a copied, verified cook-harness template:

```powershell
python -m master_rallye.source_cooker vehicle --source <vehicle-folder> --family <name> --model-strategy retail-native-gxm --texture-strategy auto --retail-root <isolated-harness-template> --runtime-family <harness-family> --output <new-job-folder>
```

The job contains a staged runtime copy, source hashes, embedded authoring
reference report, copied GXI mirror, guarded PowerShell Junction helpers, and
human cook instructions. The command does not launch the game or execute those
helpers.

After the operator cooks the three roles, collect and validate:

```powershell
python -m master_rallye.source_cooker collect --job <job-folder> --output <new-package-folder>
python -m master_rallye.source_cooker validate-package <new-package-folder>
```

For supported revision-131 DX or revision-135 DX inputs, `vehicle` validates
and builds a package directly. Existing outputs are never overwritten;
choose a new output directory for each run.

## Safety boundaries

- Only the supported retail build and exact prepared harness are accepted for
  native GXM jobs.
- Canonical retail/demo installs are read-only inputs; the tool copies the
  isolated runtime template before preparation.
- The game is started by the operator. The tool only stages and validates.
- Junction setup/cleanup scripts verify job ownership, link type, and exact
  target. A mismatch stops the script; cleanup removes only the Junction node.
- DXT is handled independently from model cooking. A missing DXT is reused
  from a valid GXI only through the existing offline encoder.
- Output packages contain three rev135 model DX files, required DXT, and
  JSON manifests only. GXM, GXI, TXT and harness files are excluded.

## Version 1 limits

No arbitrary GXM support is claimed. One Mercedes family has a completed
native cook, deterministic DX outputs, cache-only runtime use, and collision
and damage runtime confirmation. Forester is the next clean source candidate;
its package preparation is statically ready, but the R-COOKER3 native cook and
runtime are pending. Rev127 DX without usable GXM remains unsupported.

The tool does not reconstruct original retail cooker algorithms. Broad
GXM/GXI serialization, headless cooking, R-DEMO2 secondary collision
descriptor generation, Vehicle Composer integration, and vehicle registry
work remain outside this phase.
