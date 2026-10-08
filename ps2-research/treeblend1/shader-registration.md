# Shader registration and material contract

Canonical ELF: `SLES_509.06`, SHA-256 `b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2`. VAs below use the canonical PT_LOAD mapping, file offset = VA−0xff000.

`390d98` searches case-sensitively for the substring `$shader`, then takes the first following parenthesized value. It does not trim whitespace or correct spelling. The established interner folds ASCII case and slash direction **after** token extraction. Thus `$shader(TREE)` resolves to tree; `$SHADER(tree)` is not the same property; `treeblnd` remains unknown. This is substring extraction, not a complete material-token grammar.

`391690` resolves material text for the mesh, with generic properties at `390f98` before registry dispatch through `3a6c58`, shader virtual slot+14. Unknown names retain the existing unidentified-shader/default path; the new diagnostic marks untraced categories UNKNOWN rather than inventing their final draw state.

| Shader | Original name VA | Registration | Shader vtable | Material callback | Render mode |
|---|---|---|---|---|---|
| treeblend | 004875e0 | 003a7468 | 00487d68 | 003ae618 | 2 |
| tree | 00487610 | 003a75b8 | 00487d08 | 003ae710 | 6 |
| object, control | 00487618 | 003a7628 | 00487ce8 | 003ae760 | 15 |

Original bytes, vtable entries, callback stores and registry call flow are `CONFIRMED_BY_EXE`. The selected PSM owner-to-callback association is `CONFIRMED_BY_BOTH`. Adjacency of the strings was not used as ownership proof.

## Callback writes

| Mesh field | treeblend | tree | object | Proven consumer |
|---|---|---|---|---|
| +28 | 2 | 6 | 15 | 3bca80 →31d230 →312610 mode selector |
| +2c | 1 | 0 | 0 | 3bca80 →31d1b8 →31d250 queue bucket |
| +3c | 1 | 0 | 0 | primary texture resolution3714e0 →2fd7d0, negated cache option |
| +40 | 0 | 0 | 0 | secondary texture-resolution option |
| +44 | 0x3e19999a,0.15 | 0x3e4ccccd,0.20 | 0x3f000000,0.50 | 31f4e0 strip scale × field →31b8c8 mip calculation |

Callbacks return the shader/owner argument and write the supplied mesh. They do not allocate an independent foliage owner, replace the source texture names or install a foliage-specific geometry writer. No time, camera position, wind parameter, fade range or plant count is read by these callbacks.

The generic `$alphatest()` marker does not override the later mode2 GS TEST write. Likewise a source `$mip(1.0)` does not justify treating final mesh+44 as one: the shader callback's concrete write is the consumer-relevant evidence. Exact generic marker fields beyond this material path were not reopened.

## Ownership and lifetime

These are shader registration objects plus material-owning meshes, not a separate TreeRenderer/plant-instance manager. `391d38` constructs the supported visual hierarchy and tag2 mesh; source vertex loading uses `3900f0`. `3714e0` resolves textures for model mesh entries. `361a58` builds/reuses the mesh wrapper/cache; `3bca80` later dispatches it into the common renderer.

Caches and texture references belong to the general model/resource systems. No foliage-specific per-frame generation or independent destructor/reload path was found in the traced callbacks. General model/resource teardown was not exhaustively reversed. Queue/dirty-state reset and new-mode state writes are shared renderer operations, not a proved save/restore around each foliage mesh.

`elf-functions.json` records 51 relevant functions, actual known bounds, input/field flow, caller/callee scope and prior-phase provenance. Labels `313270`, `3138ec`, `313e64`, `31679c` are **interior blocks of312610**, not newly discovered function entries. Empty direct-caller lists do not imply unused virtual callbacks.
