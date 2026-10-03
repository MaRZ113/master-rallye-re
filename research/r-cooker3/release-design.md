# Source Cooker v0.1.0 release design and verification

## Release boundary

The standalone product is `Master Rallye Source Cooker 0.1.0`. It orchestrates
the supported retail-native GXM workflow and exposes the existing R-COOKER2
revision-131 converter and revision-135 pass-through. It does not implement a
GXM serializer, DXT conversion beyond the already supported offline GXI
encoder, a triangle optimizer, or game/vehicle registration changes.

The runtime package is built by the positive allowlist in
`tools/build_source_cooker_release.py`. It contains only the public CLI,
Python modules in the runtime import closure, `docs/source-cooker.md` copied
as the release README, and the MIT license. It does not archive the repository
tree. Inputs, research outputs, corpora, executables, archives, models,
textures, and generated jobs are excluded and are separately rejected by the
release validator.

## Shipped dependency closure

The allowlisted runtime modules are:

```text
authoring_paths, bounds, collision, collision_analysis, collision_oracle,
collision_oracle_analysis, collision_writer, demo_dx, dx,
dx_revision_upgrade, dx_writer, dxt, errors, gx_image, gxi, gxm,
gxm_chull, model, sidecar, source_cooker, source_cooker_jobs,
junction_lifecycle, version
```

The package requires Python 3.10+ and only the Python standard library.
Retail-native GXM cooking additionally requires Windows and user-supplied,
hash-verified retail harness files. No game data is bundled.

## Build and validation

From the repository root:

```powershell
python tools/build_source_cooker_release.py
python tools/validate_source_cooker_release.py dist/MasterRallye-SourceCooker-v0.1.0.zip
```

The builder uses a fixed allowlist, normalized ZIP member names and
timestamps, content/path validation, then extracts the artifact to a fresh
temporary directory with `PYTHONPATH` and `PYTHONHOME` removed. It runs
`--help`, `--version`, `compileall`, and a synthetic offline revision-131
plan/cook/package/validation path. The output is local and ignored; it is not
tagged, uploaded, or published in this phase.

## Release candidate record

The final candidate is recorded after the final source and documentation
changes have been built and validated:

| Artifact | SHA256 | Size | Files |
|---|---|---:|---:|
| `MasterRallye-SourceCooker-v0.1.0.zip` | `94fb75ce9109d16c73ac195cf75ec6ac71003399fe9e3ed6838baf40c5ea1524` | 88,547 bytes | 27 |

The archive must be reproducible byte-for-byte from the same source tree and
Python/zlib environment. Any source change requires rebuilding and replacing
this record. Publication remains a separate, explicit operator decision.
