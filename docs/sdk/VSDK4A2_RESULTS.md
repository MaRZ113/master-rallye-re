# V-SDK4A.2 / V-SDK4C material and Help tracks

25 October 2026. Implemented after committed V-SDK4A.1 `8085800`.

## Qualified functionality

Assign Existing Texture is a real draw/slot edit, distinct from pixel replacement.
The picker shows owned resources, native dimensions, alpha range, current usages,
source path, incompatibility reasons and an embedded filtered texture viewer.
Only diffuse slot 0 is qualified. Equal encoded ASCII name length, FEED format,
dimensions and full alpha plane are required. Unknown/effect slots, missing
resources, Null activation and shared/aliased native descriptor spans fail closed.

DX evidence: each physical record stores three inline length-prefixed ASCII
strings. This subset overwrites only the selected string payload. Length words,
UVs, vertex alpha, indices, collision, controls and other descriptors are untouched.
The existing attribute writer, project history and shared vehicle compiler compose
the recipes. No GUI-specific conversion implementation or retail resource mutation.

Offline Help has visible Help/F1, Material/Texture context buttons, search, six
stable topic IDs, English fallback and a locale-folder architecture. Native
Previewer F1 retains its qualified control reference. Unsupported future Studio
modules are described as unavailable, not as working controls.

## Actual Windows evidence

Private evidence directory: `.research-output/vehicles/vsdk4c/`.

- `tests.txt`: 810 tests, one optional skip, full Windows synthetic suite.
- `binding-windows-2/gui-validation.json`: actual Tk picker, native D3D9 before/
  after captures, Save/reopen, Validate, Undo/Redo, isolated addon and stock builds.
- The target already had source draw users; the newly assigned draw increases
  sharing without changing their descriptors or the texture file.
- Generated candidates: `workshop-builds/9304849d9997` (Pajero addon),
  `workshop-builds/d98030fa2fc0` (stock edit), `workshop-builds/85761d43637b`
  (restored stock, zero overrides). All under `.research-output/`.
- `help-windows.json`, `offline-help.png`: actual Tk Help/context window and F1
  binding. Display does not use a network service.

The first validation run was interrupted because its test fixture performed an
unnecessary all-pairs parse. The harness now prefilters metadata and tests one
compatible pair. The production picker still validates each offered assignment.

These are offline GUI/build/preflight results, not new gameplay qualification.
Native glass investigation/repair is reported separately in VSDK4C_RESULTS.
