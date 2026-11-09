# Capacity-aware Extra Options

This source worktree is isolated from the accepted, dirty `rmod1` worktree.
`extra-source-baseline.json` identifies its HEAD and the four accepted dirty
files copied before the capacity changes. The original files remain untouched.

## Runtime contracts

The optional `MR_VEHICLE_REGISTRY_DESCRIPTOR` child environment variable contains
the absolute x86 address of an immutable MRVC v1 descriptor, in decimal or `0x`
notation. The launcher must finish the atomic native transaction before resuming
the game. Extra Options checks descriptor size, stride, getter, address spans,
class totals and every forward/reverse mapping before allocating state.
A malformed supplied descriptor disables customization with a diagnostic.

Without the variable, standalone retail/accepted SDK33 operation reads the native
registry allocation `PUSH imm32` operand at `0x45A3DF`. The count follows from
`4 + count * 52 + 39 * 44`. It never probes a guessed range beyond the registry.
MODEL choices, tyre choices and family cache are sized once for the process.
There is no 256-car array. Family names admit the SDK's 64-character identifier.
Per-player INI sections keep their existing physical `Car<ID>` keys.

`MRExtraVehicleRegistryAbi` returns `0x4D525601`. The Renderer-facing optional
`MRExtraOptionsAbi` remains `0x45583201`; no Renderer dependency was introduced.
`MRRegisterSdkRosterV1` retains its ABI and mode masks. Registration copies a
checked x86 input span and rejects duplicate IDs, invalid classes and mode bits;
the old 64-row/255-ID/64-KiB-offset guards were replaced with type/span checks.
A supplied MRVC descriptor also bounds every registered physical ID.
Race participant limits remain unchanged.

## Native hook composition

`tools/build_extra_capacity_candidate.py` builds a private core and proxy against
the supplied complete SDK runtime. It generates checks for the installed SDK
operations, extension shape and compiled registry count. MRVC counts cannot use
a proxy compiled for another count. It does not install SDK patches again.

G1 keeps owning its existing callback regions. The two Challenge instructions
are the sole permitted overlaps: their original `MOV EDI,[EAX+EDI+disp32]` replay
is composed from the new explicit RaceTest layout. The physical identity field
is `race_test_base + race_test_stride - 4`; the separate human/class field is
`race_test_base + race_test_stride - 8`. Unexpected overlapping opcodes or a
displacement inconsistent with the profile fail. The full existing startup
transaction and readback rollback remain active. Multiple sorted page-aligned
mutable ranges are supported; immutable snapshots and provenance hashes exclude
every mutable page. The legacy single-page manifest shape remains accepted by
the header generator. SDK page protection belongs to the launcher; Extra Options
only validates and snapshots the installed allocation.

Ghost/five-difficulty code and the existing Challenge eligibility rules are
unchanged. MODEL/GENERAL native menus retain their accepted behavior.

## Validation

MSVC x86 `/W4 /WX` compiled the production native callbacks and runtime core.
The native callback harness checked MRVC counts 33, 128, 129, 255, 256, 257 and
513, malformed descriptors and inconsistent inverse maps. Physical IDs 127,
128, 254, 255, 256 and 512 exercised MODEL choice, human wheel compounds and
per-player INI persistence. Renderer queries were called directly without a
Renderer DLL. The provider harness registered 487 rows (IDs 26 through 512),
rejected invalid rows and retained the original participant default.

Six Python binding tests passed, including explicit RaceTest displacements
for counts 33/128/256/513/4096 and existing Unicorn replay checks. A production x86 SDK snapshot/readback harness
verified that both separate mutable pages may change while an immutable middle
region change is rejected. Five source
integration tests for the accepted Renderer build workflow also passed.

The actual 34-record runtime produced a private proxy and core under
`.research-output/extra-set1/v-cap2-candidate34-03`; its `capacity-build.json`
records source/runtime hashes, all 263 SDK checks, two composed Challenge hooks
and the exported ABI. These are offline/native harness results, not gameplay
qualification. Rebuild after changing the composite SDK profile.

Example (run from this worktree, with the existing local `pefile` dependency):

```powershell
python tools/build_extra_capacity_candidate.py --output .research-output/extra-set1/owner-candidate --sdk-runtime D:/path/to/candidate/runtime --sdk-root D:/path/to/master-rallye-re-v-cap
python tools/test_extra_native.py --output .research-output/extra-set1/native-tests --core .research-output/extra-set1/owner-candidate/core/MRallyeRandomizerRuntime.dll
```

No files were installed into either game installation, and Renderer sources
were not changed. Owner testing must still exercise the exact final composite
package with Extra Options alone and together with the accepted Renderer.
