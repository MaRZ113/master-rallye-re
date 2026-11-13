# Source Garage — external roots and reproducibility

28 October2026. Source files remain external and private. A game may be an
existing installation or extracted disc directory; duplication is not required.
`research/vehicles/source-garage/roots.example.json` supplies sixteen explicit
root aliases. Set `base` to a shared directory, or set an individual `path` to an
absolute existing location on another drive. A missing directory is recorded
as **MISSING INPUT** and does not become an invented installation.

Suggested layout:

```text
E:/RallyWorkshop_Sources/
  sources/             existing original/local installations, read only
  tools/               supplied third-party tools; source review before use
  research/
    source-garage-20261028/   private census, extracted test members, diagnostics
```

Private repository metadata/logs live in ignored
`.research-output/vehicles/source-garage/`. Ghidra, if needed in a later native
investigation, uses the existing ignored repository `scratch/` directory; no
new Ghidra project or dump was necessary for this audit. Dakar2 is an actual
PS2 source and is not routed through REA's unsupported Windows R5900 provider.

## Complete census versus small tracked manifest

```powershell
python tools/source_garage_audit.py --config research/vehicles/source-garage/roots.example.json --inventory E:/RallyWorkshop_Sources/research/source-garage-20261028/corpus-full.json --summary docs/sdk/DONOR_CORPUS_MANIFEST.json --workers 2
```

Both output paths must be fresh. For another run choose new paths, then review
the new summary before intentionally updating the committed manifest. The full
inventory hashes every regular file within the configured roots. The tracked
summary pins its exact path/size/hash, per-game tree hashes, all executable
identities, extension/signature counts and first100 lexical resource candidates.
The full file/directory list is not silently limited to those100 candidates.
Filename/extension roles are discovery leads, not decoded identities or formats.

Census budgets:100000 files and100GiB per game,4GiB per file,1MiB hash reads,
maximum4 workers. Links/reparse points are rejected/excluded, changed-during-read
files are errors, and inaccessible enumeration is reported. SHA256 proves the
identity of the local bytes, not original-disc authenticity. Edition/region and
archive versions remain unknown unless there is actual evidence. Root-relative
paths support installations on shared disks without copying them into Git.

Windows `FileVersionInfo` observations in the manifest are static version
resources, collected through PowerShell `Get-Item ... .VersionInfo`; they do
not execute games or independently verify advertised versions. Missing version
resources remain unknown. The separate private `executable-versions.json`
retains these observations. PS2 `SYSTEM.CNF` boot/version/video settings are
recorded as literal configuration, not mislabeled as a verified game revision.

## Representative tests

`tools/source_garage_smoke.py --help` exposes POD/SMF, V-Rally2 PC, Screamer COD
and Sega Rally2 probes. Supply the same `--config` and protect the external tools
root. Outputs must be new and outside all configured installations/tools. The
V-Rally2 probe loads only a pinned, separately supplied source tool; that tool's
implementation is not redistributed in the SDK. The final probe disables Python
bytecode creation for that external import. Early audit imports created tool
`__pycache__` files; donor-game inputs were unaffected, and existing caches were
not deleted.

`tools/source_garage_priority_probe.py` validates the selected historical/source
metadata and PSSG dictionaries. `tools/source_garage_revo_probe.py` probes a single
selected SBF and optional DDS diagnostic. See their result documents for exact
commands and limitations; no command invokes an MR compiler or game launcher.
Synthetic checks run with `python -m unittest discover -s tests/synthetic -p
test_source_garage*.py -v`. Optional image/VR2 dependencies are supplied by the
existing bundled Python runtime; no legacy tool EXE is required.

## Source-only review

After the validated local commit:

```powershell
python tools/package_source_garage_review.py --baseline b9a24f7 --revision HEAD --output .research-output/vehicles/source-garage/review
```

The packager reads committed Git blobs only and admits explicit text-source
extensions. It checks Python syntax, ZIP CRC and every member hash, then emits
full-source and changed-files ZIPs plus an external archive manifest. Existing
binary UI assets and embedded ZIP files are excluded and listed; external game
files, decoded assets, previews, runtimes and third-party tool implementations
are never traversed. Outputs are confined to ignored Source Garage evidence.
No push, release, publication or unrelated merge is part of this milestone.
