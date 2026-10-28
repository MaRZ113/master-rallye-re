# Source Garage — audit closeout and review gate

28 October2026. Repository `master-rallye-re-vehicles`, branch
`research/vehicles`. The initial checkout was clean at `b9a24f7`; this matches
the attached handoff snapshot, with implementation `138df440`. The actual tree
and current GT/automatic/Heritage documentation were used as authority. Attached
Master Planv6.6 and handoff were treated as context; historical implementation
instructions did not trigger unrelated work. Their hashes are preserved in
private `preservation-before.json`.

## Result

All16 configured new-game sources exist locally. **38762 files /45961878729
bytes** were hashed without read errors. The11,047,585-byte external full
inventory SHA256 is
`2013e6e7c2de743410229690648b4ae6c8cfda162277db700df1df8801200516`.
This is a local collection identity, not authentication of pristine game copies.
Several installations include patches/wrappers; exact edition/region is unknown
where unverified. GT3/GT4 remain established research sources outside discovery.

| Outcome | Evidence |
|---|---|
| Source inventory, per-game hashes/sizes/signatures/platforms | [DONOR_CORPUS_MANIFEST.json](DONOR_CORPUS_MANIFEST.json), pins full private file list |
|16-title readiness and independent personal priority | [DONOR_FORMAT_MATRIX.md](DONOR_FORMAT_MATRIX.md) |
| Tool authors, versions/build claims, licenses and limitations | [DONOR_TOOL_AUDIT.md](DONOR_TOOL_AUDIT.md), [exact local tool hashes](DONOR_TOOL_SOURCES.json) |
| Five actual PC structural probes | [DONOR_SMOKE_RESULTS.md](DONOR_SMOKE_RESULTS.md): Evo1/2, Screamer, VR2, SR2 |
| Paris-Dakar/Michelin attention and separate DiRT dictionaries | [DONOR_PRIORITY_RESULTS.md](DONOR_PRIORITY_RESULTS.md) |
| One Revo car SBF plus individual DDS | [DONOR_REVO_RESULTS.md](DONOR_REVO_RESULTS.md) |
| Proposed first adapter and acceptance criteria | [DONOR_FIRST_PILOT_DECISION.md](DONOR_FIRST_PILOT_DECISION.md) |
| Future common source interface; actual existing reuse limits | [UNIVERSAL_VEHICLE_SCENE_PROPOSAL.md](UNIVERSAL_VEHICLE_SCENE_PROPOSAL.md) |
| Configurable external roots, commands and archive workflow | [SOURCE_GARAGE_LAYOUT.md](SOURCE_GARAGE_LAYOUT.md) |

Recommended future pilot: **Evo2 Toyota4Runner SR5 Sport Package2WD**, exact
catalog record `T4RSR52.TRK`, qualified POD/SMF/TIFF inputs and separate wheel
structures/placement records. L1 remains **WARN**, L2 is an inspected diagnostic
only. The wireframes preserve local coordinates and do not prove assembled
textured source rendering. Original source runtime behavior, glass/alpha,
equipment/variants and units still require qualification.

Paris-Dakar remains the historical lead: both Pajero TC resources were found,
but V60/V20 mapping and any shared geometry with MR remain unproven. Michelin's
catalog/scripts associate ID25/RAV4 and ID6/Megane F2 with actual PDO resources;
PDI1 directories validate, inner payload/model decoding does not. The F2 label
does not establish Maxi geometry. These priorities are independent of choosing
the technically simpler pilot.

## Validation and preservation

- **50 focused tests PASS**, covering malformed structures, decompression/array
  budgets, path containment, missing inputs, source immutability and actual
  unsupported semantics. `focused-tests.log` in private evidence.
- **1017 complete synthetic/CPU tests,2 pre-existing private-fixture skips,
  no failures** under installed Python3.15/Pillow13/NumPy2.5.4/Unicorn2.1.4;
  `full-synthetic-validated.log`,62.148s. The first bundled-runtime attempt lacked
  Unicorn (6 import errors,5 skips); it was superseded by this complete installed
  environment run. No dependency installation or test weakening was used.
- Independent complete directory enumeration matched every original path/size
  for16/16 roots, with no enumeration errors. Census reader was then hardened
  for invalid file-as-root and inaccessible-directory cases, plus current-date
  metadata; the raw census retains its actual earlier reader digest. The small
  manifest identifies the final reader separately and contains curated readiness/
  version observations. The coverage check did not repeat all SHA256 reads.
- **23/23 content checks match**: six protected MR files across current/Pristine
  installations plus17 representative original donor files were rehashed.
  Accepted Workshop projects and existing GT/Heritage code were not edited.
  Both protected Data.sma variants retain their own baseline hashes; they are
  not incorrectly described as identical to one another.
- REA's available target-free PE resource parser verified the two high-priority
  executables and absence of RT_VERSION; exact Evidence records are private.
  No native disassembler, source-game EXE, old tool EXE or MR game was launched.
- No MR GUI/renderer parity regression or gameplay test is claimed from this
  source research. Existing Trooper owner acceptance is preserved; Clio's pending
  gameplay status is unchanged. Source Fidelity/Classic candidates, alternative
  CarID29 projects and the30-entry roster limit are untouched.

Private evidence root: `.research-output/vehicles/source-garage/`; original
geometry/texture diagnostics and extracted members remain under
`E:/RallyWorkshop_Sources/research/source-garage-20261028/`. Early VR2 Python
imports created tool-cache files only; the final utility disables bytecode writes
and protects tool roots. No cache cleanup deleted existing material.

## Source-only handoff and next step

The scoped local commit is identified by subject
`feat(research): qualify Source Garage donor formats and tools`; the post-commit
review manifest records its exact revision. Full-source and changed-files ZIPs
are generated from committed text blobs into
`.research-output/vehicles/source-garage/review/`. The packager excludes donor
assets/private diagnostics/tool implementations and lists excluded pre-existing
binary UI resources/ZIPs. It verifies every archived member hash, CRC and Python
syntax. Archive hashes/counts live in `review/archive-manifest.json` after packing.

**Audit delivered; stop for owner review before the first cross-game importer.**
No new importer/UI integration/native vehicle build, capacity patch, original
game modification, push, publication, release or unrelated merge was performed.
