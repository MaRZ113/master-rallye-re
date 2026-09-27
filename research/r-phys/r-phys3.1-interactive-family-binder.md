# R-PHYS3.1 - Interactive Vehicle Family Binder (Historical UI)

R-VEH1 extends the same command into the **Master Rallye Vehicle Composer**.
This report preserves the P3.1 family-first interface history; for current
carrier / physics family / model donor choices, transaction behavior, and human
test plans, see [R-VEH1](r-veh1-independent-model-composition.md) and its
[runtime test plan](r-veh1-runtime-test-plan.md).

**Status:** implemented; synthetic tests pass; the real-install status and
Trooper preview were run read-only. No executable was written by the P3.1
checks. The human-confirmed P3 runtime result is recorded in
[R-PHYS3](r-phys3-persistent-family-binding.md).

## Corrected runtime architecture

The persistent initializer changes a retail type's vehicle-family identity.
The family name is used for both resource branches:

```text
retail type 7 / Navara
        |
        v
persistent family binding: Trooper
        +--> DataGx\Vehicles\Trooper\car.dx
        +--> DataGx\Vehicles\Trooper\complete.dx
        +--> DataGx\Vehicles\Trooper\wheel.dx
        +--> Vehicles/Trooper/*
        +--> Trooper/Player1/*
```

The user confirmed that the same patched executable loaded the rebuilt Trooper
model once that package was available at `DataGx\Vehicles\Trooper`. This
corrects the earlier physics-only interpretation. The original P3.1 binder
checked that model assets were already installed; R-VEH1 adds the separate
transactional model-donor overlay described in its current report.

## Inventory and completeness rules

The wizard reads the exact supported `MRallye.exe` build first. It reads
`vehicles.xml` and `Modifications.xml` from loose `DataGame` files when present,
otherwise from the install `Data.sma` without extracting the archive. The
reader handles both standard ZIP output and the retail archive's `SM` end
marker. If no archive exists, it can use an existing `Data.sma_unpacked`
fallback for the XML inputs. Model files are indexed from `Data.sma` and merged
with files below the runtime loose override root `DataGx\Vehicles`.

Loose resource files override an archive member with the same family-relative
path; non-overridden resources remain available from `Data.sma`. Provenance is
shown as `DATA_SMA`, `LOOSE_OVERRIDE`, `DATA_SMA+LOOSE`, or `MISSING`. The
required model files are `car.dx`, `complete.dx`, and `wheel.dx`, except that
the known Ufo family is complete without `wheel.dx`. A model-only family such
as `forklift` remains visible, but cannot pass the config broker checks.

In the P3.1 implementation, final family validation and executable patching
ran through `validate_binding_request` and `apply_binding_copy`; the wizard did
not implement a second patcher. R-VEH1 now builds and applies a composition
plan through `vehicle_composition.py`, which continues to delegate EXE bytes to
the same verified family-initializer patcher.

Every named family from `vehicles.xml` is shown, including release families,
cut/config-only families, and families that fail the strict broker schema.
Model-only packages are included as supplemental rows. Base completeness
uses the retail reader-aware schema: 120 fixed path/type requirements, including
the `Gears` and `TorqueEntries` count headers, plus the indexed Engine fields
required by those counts. Total field count varies by family. The status view
reports that total as diagnostic information, not as a compatibility gate.
Player1 completeness means the exact 13 expected float setup fields. The final
family validation and PE patch still run through `validate_binding_request`
and `apply_binding_copy` in `vehicle_physics_binding.py`; the interactive
workflow has no patching logic of its own.

The carrier menu comes only from the 25 initialized retail type records. A
config-only family can be selected as the new family, but never appears as a
carrier unless it is in that runtime catalog. In the P3.1 interface, family
selection happened before the carrier menu. The current composer asks for the
carrier and then explicitly asks for physics family and model donor.

## P3.1 user commands (historical interface)

The commands below remain useful for schema-v1 scripted compatibility. The
current interactive composition flow is described in the linked R-VEH1 report.

From the repository directory:

```powershell
python tools/physics_bind.py
```

The historical P3.1 wizard detected the nearest parent containing
`MRallye.exe`, verified the executable hash, and selected one coupled family.
The current composer still detects and verifies the install, but treats carrier,
physics family, and model donor as independent choices. Its current flow and
advanced incomplete-package overrides are documented in the R-VEH1 report.

The preview includes the source family, carrier type, both runtime lookup
paths, resource provenance, and output path. The usual output is named like
`MRallye_Navara-to-Trooper.exe`. One final `Apply this vehicle-family binding?
[Y/n]` confirmation writes the copy, `.original` backup, and manifest through
the existing backend.

For a no-write preview:

```powershell
python tools/physics_bind.py --dry-run
```

For current binding and resource status, including known manifests:

```powershell
python tools/physics_bind.py status
```

To select a known tool-owned copy and restore it from its verified backup:

```powershell
python tools/physics_bind.py restore
```

The previous scripted interface remains available:

```powershell
python tools/physics_bind.py validate `
  --install-root 'D:\Game\Master Rallye' `
  --config 'research\r-phys\vehicle-physics-bindings-trooper.example.json'

python tools/physics_bind.py apply `
  --install-root 'D:\Game\Master Rallye' `
  --config 'research\r-phys\vehicle-physics-bindings-trooper.example.json' `
  --output-exe 'D:\Game\Master Rallye\MRallye_Navara-to-Trooper.exe'

python tools/physics_bind.py restore `
  --output-exe 'D:\Game\Master Rallye\MRallye_Navara-to-Trooper.exe'
```

The tool never launches the game. The human runtime test remains the check for
loader behavior, race behavior, and rollback behavior.

## Read-only installation snapshot

At P3.1 implementation time, the supported local executable hash matched the
expected retail build. The current installation `Data.sma` index contained a
complete Trooper model package (`car.dx`, `complete.dx`, and `wheel.dx`), while
the loose runtime `DataGx\Vehicles` root had no Trooper override. Trooper's
base config was `COMPATIBLE`: 120 fixed fields, `Gears = 7`, and
`TorqueEntries = 6` produce 147 total fields. Its Player1 overlay was complete
at 13/13. The archive itself is an installation input; this inventory does not
claim that its contents are byte-identical to a pristine distribution.

The same inventory showed 35 named config families. The merged view had 37
rows including model-only packages; `forklift` had a complete model package
but no same-named config family, and Ufo was marked `COMPLETE_WHEELLESS`.
This inventory is local environment evidence; other installations will show
their own loose/archive provenance.

## Validation record

- 26 focused P3.1 tests passed, including retail `SM` archive indexing and
  member reads without extraction,
  loose-over-archive precedence, Ufo, forklift, config-only Trooper, family-first
  selection, retail carrier filtering, missing-model refusal, final confirmation,
  output naming, path-with-spaces handling, and restore discovery/backend use.
- The current installation status view recognized the existing applied
  Navara-to-Trooper manifest and verified its backup/output hashes.
- A live Trooper-to-Navara wizard dry-run validated the exact retail EXE and
  broker config, displayed the complete model package, and wrote no files.
- No new apply or restore was executed during P3.1.
