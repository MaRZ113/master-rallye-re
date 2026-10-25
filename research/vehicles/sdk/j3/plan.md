# R5V-J.3 — Public Vehicle SDK productization

**Current state: J.3-A authoring and J.3-B bounded runtime compilation are
implemented; the GlacierSprint collection is READY FOR HUMAN RUNTIME, not
runtime-qualified; no SDK release claim.** J.2 is closed. This document records
the product scope and current evidence boundary.

## Product boundary

Turn the accepted J.0 manifest/compiler foundation and J.1/J.2 external runtime
pipeline into a reproducible author workflow. Keep four layers distinct:

1. author assets and a portable addon project;
2. validate and compile one or more addon definitions;
3. stage verified resources and native integration for the exact supported
   retail build;
4. launch the original, byte-unchanged executable through the removable
   external runtime component.

Do not distribute game assets or a modified retail executable. The ordinary
offline addon plan must continue to report `runtime_installable=false`; a
separate typed runtime artifact owns runtime readiness and qualification.

## Work areas

### Stable project and manifest

- Freeze and document a versioned project layout, manifest schema, path rules,
  and upgrade policy.
- Provide actionable diagnostics with file, JSON pointer, observed value,
  expected constraint, and suggested correction.
- Make ID allocation deterministic across addon order and reject collisions,
  unsupported identities, unsafe resource overrides, and unknown policies.
- Keep class placement sparse and explicit. Generated reverse mappers must
  write the selected class's own ordinal field using
  `local_field_offset = 0x14 + 4 * class_id`.

### Portable author workflow

- Reuse the existing donor-based Vehicle Authoring SDK and deterministic
  DX/DXT validation/packaging tools; do not merge authoring and runtime
  integration into one opaque command.
- Supply metadata-only sample projects and tutorials that point to user-owned
  compatible assets. Include no proprietary donor assets.
- Make resource dependency closure inspectable and produce a reproducible
  package inventory with hashes.

### Generic multi-addon compilation

- Compile multiple manifests in one invocation without editing Python source
  per vehicle.
- Emit resolved physical IDs, class-local maps, registry plan, frontend
  resources, unlock/audio/AI/Results policy tables, resource inventory,
  compatibility profile, and deterministic artifact hashes.
- Keep ordering policy append-only for this release. Custom UI ordering is
  explicitly out of scope.
- Report separately the compiler's synthetic capacity and runtime evidence:
  physical IDs 26/T1 and 27/T2 are the only added IDs currently qualified in
  game. Do not claim arbitrary-N runtime support.

### Installation, removal, profiles, and conflicts

- Document verified install/staging, launch, disable, and clean removal between
  runs. Never write the retail EXE or stock resource archive.
- Keep user save/profile locations explicit; explain which external-root files
  are user state and must be retained on uninstall.
- Detect exact-build mismatch, missing resources, malformed plans, conflicting
  patch preimages, overlapping operations, and resource-name conflicts before
  process resume. Fail closed without leaving a partly installed game process.
- Document graphics-wrapper compatibility only for combinations actually
  tested. Do not promise hot-unload.

### Examples and release qualification

- Keep Mercedes ID26/T1 and R5VQualifier ID27/T2 as independent metadata-only
  references, not bundled runtime content.
- Add an independent author exercise that changes identity and policies
  without code edits, using external user-provided assets.
- Gate release on clean reproduction, negative-path tests, unchanged retail
  executable checks, install/remove verification, and a fresh human run of the
  supported reference package.
- Keep J.2 evidence intact. Any new runtime claim needs its own exact artifact
  identity and evidence provenance.

## Release evidence labels

Use separate labels for schema/compiler synthetic support, deterministic
package verification, exact-build preflight, bootstrap runtime, and human
in-game qualification. Runtime-qualified physical IDs remain 26 and 27 until
new evidence explicitly qualifies another identity. A successful synthetic
allocation test is not evidence that the game can instantiate that ID.

## Explicit exclusions

No ID28 runtime research, UI ordering, class expansion, new AI/audio/unlock
architecture, cooker research, or arbitrary-N runtime claim is a J.3 release
prerequisite. Resume those topics only in a separately authorized phase if a
demonstrated product blocker requires it.

## Implementation evidence and remaining gates

J.3-A now has `addon init --name`, `project-validate`, and `project-build`.
The bridge reuses VehicleProject validators and emits independent model-family
assets. Optional physics generation verifies the exact retail Data.sma hash and
matching unpacked resources before byte-preserving donor-family cloning. The
metadata-only Glacier Sprint T2 example resolves to an independent ID27/T2
identity without SDK-source edits. Synthetic tests exercise the build, output
hashes, the retail archive gate, and target-family collisions.

An actual local Navara-donor smoke build produced 47 verified artifacts,
including a 44-row resource inventory and independent GlacierSprint entries
in both DataGame configuration files. Its addon-plan SHA256 is
`1d64c320cc104d177db3c012986631590183175cdd167051267e68568ad5f492`. A second
build in a separate output directory had the same 48 file paths and exact
SHA256 for every file. The generated build and donor assets remain in ignored
`.research-output`; neither is included in source control or the review
archive.

J.3-B adds `runtime-prepare`, `runtime-verify`, and `runtime-launcher-build`
for the exact ID26/T1 plus ID27/T2 layout. The reference pair reproduces the
J.2 RVP and image; the GlacierSprint project produces a separate verified
native/resource bundle and launcher preflight. T2-only input is rejected
explicitly. J.0 offline output still reports `runtime_installable=false`.
Remaining gates are the human GlacierSprint runtime test, clean removal and
conflict qualification, and the broader public author workflow. This bounded
compiler does not establish arbitrary layouts or arbitrary-N runtime support.
