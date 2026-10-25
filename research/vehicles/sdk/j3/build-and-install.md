# Building, installation and multi-addon limits

## Available J.3-A commands

```text
mrtool addon init --name ... --class T1|T2 --donor ... --output ...
mrtool addon project-validate <project> [--retail-data-sma ... --retail-data-root ...]
mrtool addon project-build <project> --output <new-directory> [...retail inputs...]
mrtool addon validate --manifest <file> [--manifest <file> ...]
mrtool addon build --manifest <file> [--manifest <file> ...] --output <new-directory>
mrtool addon verify <build-directory>
mrtool addon inspect <plan-or-Broker-capture>
mrtool addon check-frontend-state <Broker-capture>
```

`project-build` validates a donor VehicleProject, builds its addon plan and
asset closure, and can append the independently named donor physics-family XML
rows. `build` compiles metadata-only or externally staged manifest collections.
Both are offline compiler artifacts. `verify` verifies the exact files and
hashes. Existing destinations are never overwritten.

## Multi-addon collection

Use repeated `--manifest` options to compile multiple definitions. The
compiler rejects duplicate physical IDs, class-local slots, family names and
resource paths. Auto assignment is stable over addon ID, and the build records
the resolved mapping. The current target only has one added T1 and one added
T2 slot. Two T2 addons cannot be assigned to the one T2/addon slot.

J.3-A does not yet create the collection lockfile required for persistent
physical IDs across changed collections. Keep the exact manifest collection
and build output together; do not remove or replace an addon after saving a
game profile that refers to its ID.

## J.3-B runtime bundle compilation

The collection runtime compiler is separate from the J.0 offline planner and
accepts repeated manifests plus an optional validated ID27 author build:

```text
mrtool addon runtime-prepare --manifest <ID26.json> --manifest <ID27.json> \
  [--project-build ADDON_ID=<verified-project-build>] --output <new-runtime-bundle>
mrtool addon runtime-verify <runtime-bundle> --manifest <ID26.json> \
  --manifest <ID27.json> [--project-build ADDON_ID=<verified-project-build>]
mrtool addon runtime-launcher-build <runtime-bundle> --manifest <ID26.json> \
  --manifest <ID27.json> [--project-build ADDON_ID=<verified-project-build>] \
  --launcher-output <new-launcher-directory>
```

The currently audited runtime layout is exactly ID26/T1 Mercedes plus one
ID27/T2 vehicle. A T2-only collection fails closed instead of adding Mercedes
silently. Other class/ID layouts and donor families are unsupported.

The human-test handoff uses the original retail EXE path and invokes the
external launcher with `--integrated`; it does not stage a replacement EXE in
the game folder. The launcher sets the game working directory to the bundle's
verified `resource-root`, so generated physics, frontend, and model resources
resolve from the tested external tree. Run `--verify` immediately before
launch. Launching the pristine EXE directly disables the integration. Remove
only the generated external launcher and runtime bundle after game exit; do
not remove or rewrite saves/profile files or stock resources.

See [runtime compiler](runtime-compiler.md) for full scope and
[runtime handoff](runtime-handoff.md) for exact candidate hashes and test
steps. This remains a human-runtime candidate; the GlacierSprint identity is
not yet qualified by the game.
