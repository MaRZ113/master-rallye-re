# Retail vehicle record and ownership

`RAW_GHIDRA_SUPPORTED`: registry allocation has 26 records of stride `0x34`; normal initialization covers IDs 0–24. Record25 receives only default construction. The default constructor `0x45A080` installs object/vtable state, initializes `+0x20` to an empty/null owned string state and four `1.0f` values at `+0x24..+0x30`; the seven integer fields `+0x04..+0x1c` have no proven writes for record25. Allocator zero fill is not assumed.

| Offset | Observed contents |
|---|---|
| `+0x00` | vtable/object state |
| `+0x04` | stored vehicle ID |
| `+0x08` | class |
| `+0x0c..+0x18` | four integer stats |
| `+0x1c` | integer, semantic role still untyped |
| `+0x20` | owned C-string pointer, internal name for normal records |
| `+0x24..+0x30` | four float words |

Initializer `0x45A0B0` passes `&record+0x20` and temporary string data into `0x4D1990`; that helper frees a prior destination pointer, allocates `strlen(source)+1` through the program's `operator_new`, and copies bytes. A null source leaves null. The initializer then frees the temporary argument via `0x5B4C00`; destructor `0x458D60` frees the record-owned pointer. Default empty string uses null rather than a shared heap buffer in the observed constructor.

Thus a future call of the original initializer with a newly constructed temporary `Astero` string is a plausible ownership-safe way to populate record25. Raw `0x34`-byte copying of record16 is unsafe because it aliases `+0x20` and risks double free. The initializer ABI is now known, but the complete runtime safety of invoking it on record25 also depends on the unresolved selection/resource/physics paths.
