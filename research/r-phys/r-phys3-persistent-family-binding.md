# R-PHYS3 — Persistent Vehicle Physics Family Binding

**Status:** persistent Navara-to-Trooper family binding is
**HUMAN_RUNTIME_CONFIRMED**. The user reported that the same patched executable
loaded the rebuilt Trooper model after the package was made available at
`DataGx\Vehicles\Trooper`. The runtime binding resolves both model resources
and the vehicle config/physics family. Generic carrier tests and restore
runtime observations remain separate gates.

## Purpose and confirmed starting point

R-PHYS2.2 confirmed that a Navara carrier can consume the complete surviving
retail Trooper physics family through the normal race setup. The human observed
`Trooper` at `FUN_00493E30`, `Trooper/Player1` at `FUN_00493FD0`, the normal
`FUN_004938C0` writer, a started race, correctly placed wheels, and handling
distinct from Navara. That test used a temporary x32dbg pointer redirect; it
did not modify the on-disk executable. The exact evidence is recorded in
[R-PHYS2.2](r-phys2.2-trooper-whole-family-binding.md).

R-PHYS3 replaces that process-local edit with a version-locked executable-copy
workflow. The persistent type-to-family value controls the identity used by
both model/resource lookup and the native vehicle-config broker. The tool does
not edit vehicle XML or copy the 147 base values; the selected family's model
package must already be available to the game.

```text
carrier type in race data
    -> static retail type/family initializer
    -> persistent vehicle family
         ├── DataGx\Vehicles\<family> model resources
         └── Vehicles/<family> base config
                + <family>/Player1 modification overlay
                -> native VehicleParams package
                -> Vehicles/CarN
                -> ordinary vehicle runtime
```

The JSON field is still named `physics_family` for compatibility, but its value
is the persistent vehicle family used by both branches. The executable patcher
does not install, rename, or rewrite model assets.

## Runtime catalog and persistent source

For the verified retail executable (`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`,
3,121,214 bytes), static analysis identifies this initialization chain:

1. `FUN_0045A3C0` returns the global catalog at `DAT_006F5ED4`.
2. `FUN_00458CD0` allocates/initializes a catalog with capacity for 26 records
   and calls `FUN_00458E70`.
3. `FUN_00458E70` initializes 25 records, type IDs 0–24. Each record uses a
   family-name string passed as an immediate `PUSH imm32` argument to the
   record initializer. `FUN_0045A0B0` is the per-record initialization path.
4. Records have a `0x34`-byte stride. The ordinary lookup addresses the family
   string object at `catalog + 0x24 + type_id * 0x34`. The 26th allocated slot
   is not initialized by this function and is not evidence of a hidden type.

The persistent mapping is **executable-driven**, not sourced from editable
vehicle XML. The retail XML contains physics values but no mapping from a
retail type ID to a family string. Navara is type 7; Jump is type 9. Trooper is
not one of the 25 statically initialized families. Earlier runtime heap
addresses, including the observed Navara pointer slot, are process-local and
are never used by this tool.

The retail executable contains no `Trooper\0` literal. Trooper config text is
present in XML, but no stable, long-lived runtime family string from that XML
loader has been established. R-PHYS3 therefore gives target names absent from
the static catalog owned storage in a new read-only `.rphys3` PE section.
Existing catalog family names such as `Forester` and `Newrav` can reuse their
verified static executable literals.

## Selected intervention

The implementation patches only the immediate pointer operand of the
selected carrier's exact initializer `PUSH imm32` instruction, before the
catalog is constructed. It does not patch a race lookup, runtime heap pointer,
physics constructor, or per-field config value. This is the earliest persistent
identity mapping found in the ordinary path and runs once during catalog
initialization.

The patcher is deliberately narrow:

- It accepts only the exact retail SHA-256 above, PE32 I386, image base
  `0x00400000`, and the audited initializer instruction bytes.
- It rejects dynamic-base images and images with base relocations.
- Names are ASCII path components. Variable-length targets are stored in the
  added read-only section, not copied over a shorter literal.
- Existing target families reuse their verified static executable strings.
- It creates a separate output executable. The source `MRallye.exe` is never
  overwritten.
- The output has an adjacent `.original` backup and `.physics-bind.json`
  manifest. Apply is idempotent for the same mapping; a different mapping
  requires restore first. Restore verifies both the backup and the current
  output hash before replacing the output copy.
- This PE layout has been verified offline, including section placement and
  checksum. Loading and running the patched image has **not** yet been
  verified in retail. That is the next human test.

A new `.rphys3` section is used for Trooper because an in-place `Navara` to
`Trooper` overwrite would exceed the old string's storage. A debugger-only
allocation is not persistent, and XML parser buffers do not have a proven
catalog lifetime. Config-package substitution is not used because identity
redirection preserves the native base and player-overlay broker behavior.

## Binding config and checks

The selector is strict JSON, keeping carrier type separate from physics
family:

```json
{
  "schema_version": 1,
  "bindings": [
    { "carrier_type": "Navara", "physics_family": "Trooper" }
  ]
}
```

Example files are provided for Trooper, Newrav, and Forester. No model-package
field is accepted: runtime resource availability is resolved from the selected
family name and checked by the interactive binder before apply.

Validation checks the exact supported retail EXE hash, carrier identity in the
25-entry catalog, the target family root in retail `vehicles.xml`, all six
broker groups and exact path/type schema (147 base fields), and the 13
`Player1/Modifications` float fields. It fails closed on incomplete or
unexpected schemas. Trooper, Newrav, and Forester each pass with the current
read-only retail XML inputs. Mercedes is rejected: its Engine group contains
42 fields rather than the broker schema's 45.

Dry-run example from the repository root:

```powershell
python tools/physics_bind.py validate `
  --install-root 'D:\Game\Master Rallye' `
  --config 'research\r-phys\vehicle-physics-bindings-trooper.example.json'
```

The command reports the source and config hashes, carrier type ID, group and
overlay completeness, initializer file offset, target pointer, planned
`.rphys3` section if needed, and `source_executable_modified: false`. The
verified local dry-runs were:

| Carrier | Type ID | Physics family | Target string source | Base groups | Player1 fields | Dry-run |
|---|---:|---|---|---:|---:|---|
| Navara | 7 | Trooper | new `.rphys3` string | 147 | 13 | valid |
| Jump | 9 | Newrav | existing EXE literal | 147 | 13 | valid |
| Jump | 9 | Forester | existing EXE literal | 147 | 13 | valid |

For the Navara/Trooper dry-run, the pointer operand is at VA `0x00459197`
(file offset `0x59197`); the target is planned at VA `0x00711000` in section
`.rphys3`, file offset `0x2FB000`. An in-memory patch audit produced planned
SHA-256 `ca2301742aade178d93424a9b3bdffc74618608b1f9fe026e59f4875bedf43d7`
and size 3,129,344 bytes; the stored PE checksum matched an independent
recalculation. The source remained byte-identical after the in-memory
operation. These are file-layout values for the hash-locked build, not runtime
addresses. At the time of this static patch-layout audit no candidate had been
emitted; the later user-confirmed persistent runtime copy is documented below.

The Navara/Trooper byte-diff ranges were: `0x11E+1`, `0x139+1`, `0x169+1`,
`0x170+3`, `0x2B0+7`, `0x2B8+1`, `0x2BD+2`, `0x2C1+1`, `0x2C5+2`,
`0x2D4+1`, `0x2D7+1`, `0x59198+3`, and appended aligned section bytes
`0x2FA03E+8130`. They cover PE metadata, the new section header, the initializer
pointer operand, and the appended section/alignment bytes. The pointer operand
changes from `10 3D 6B 00` to `00 10 71 00`; unchanged high zero byte is not
counted in the changed range.

## Apply and restore

After validation, a human can create a bound copy:

```powershell
python tools/physics_bind.py apply `
  --install-root 'D:\Game\Master Rallye' `
  --config 'research\r-phys\vehicle-physics-bindings-trooper.example.json' `
  --output-exe 'D:\Game\Master Rallye\MRallye_physicsbound.exe'
```

This creates `MRallye_physicsbound.exe`,
`MRallye_physicsbound.exe.original`, and
`MRallye_physicsbound.exe.physics-bind.json`. Launch the output copy normally,
with the game directory as its working directory. Do not launch the original
EXE for the bound test. The tool does not start the game.

After exiting the game, restore the output copy:

```powershell
python tools/physics_bind.py restore `
  --output-exe 'D:\Game\Master Rallye\MRallye_physicsbound.exe'
```

Restore writes the exact original bytes into the tool-owned copy and marks the
manifest `restored`; it does not delete the backup or manifest. The installed
`MRallye.exe` remains unchanged throughout. To check runtime rollback, launch
the restored output copy with the original model resources restored and verify
native Navara wheel placement and handling.

## Human runtime matrix

For each row, apply one binding at a time, run the game without x32dbg, observe
the listed behavior, exit, run `restore`, and verify native behavior using the
restored model package. Do not combine model and physics identity in the
binding JSON.

| Carrier type | Model/resource package | Physics family | Evidence / status | Race starts? | Wheels | Distinct handling | Engine / suspension / damage | Rollback |
|---|---|---|---|---|---|---|---|---|
| Navara | rebuilt Trooper package at `DataGx\Vehicles\Trooper` | Trooper | **HUMAN_RUNTIME_CONFIRMED**: the same patched executable loaded the model after the package was present | not reported for persistent test | P2.2 debugger evidence only | P2.2 debugger evidence only | P2.2 debugger evidence only | not reported |
| Jump | demo 9.3.1 `NewRav` package | Newrav | case-only folder/config spelling; schema complete; pending runtime | pending | pending | pending | pending | pending |
| Jump | retail `Forester` package | Forester | exact retail folder/config match; control; pending runtime | pending | pending | pending | pending | pending |

The Newrav case is a case-only name match (`NewRav` resources and `Newrav`
physics config); it does not infer an alias with `Rav4`. Forester is an exact
model/config control, not a cut-content claim. Test the two Jump mappings
separately. Mercedes is excluded because required Engine fields are missing.

### Persistent Trooper runtime result

The user confirmed that a persistent type 7 `Navara -> Trooper` executable
binding resolved both `DataGx\Vehicles\Trooper` model resources and
`Vehicles/Trooper` configuration, including the normal physics path. The first
attempt had no visible model because the Trooper model package was absent at
the runtime resource path. After the rebuilt package was supplied there, the
same patched executable loaded the model. This confirms a whole-family
binding; it does not by itself document a post-restore runtime check or the
Newrav/Forester controls.

The tool continues to create only a copy and leaves `MRallye.exe` unchanged.
The tested patched executable, `.original` backup, and manifest are local
installation files and must not be added to the repository.

## Status and gate

**Confirmed:** the ordinary broker accepted Trooper base and Player1 families
under the debugger experiment; the persistent type mapping is initialized
from static executable arguments; the same persistent binding loaded the
rebuilt Trooper model and resolves its config/physics family; copy-only PE
patching, backup, manifest, and restore are covered by synthetic tests.

**Still pending:** human observation of the restore workflow's runtime result,
Newrav and Forester controls, and additional generic bindings. The current
R-PHYS3.1 wizard dry-run is not an apply or runtime test. No cooker research is
started by this documentation update.
