# R-DEMO2.4 — GXM hierarchy to runtime nodes

## Scope and identity

This reconstructs only demo 9.3.1 Trooper `DataGx/Vehicles/Trooper/car.gxm`; it is not a general GXM hierarchy parser. The immutable corpus file is 222,754 bytes, SHA256 `5caed6da1213f17e2638d0ee47860cf521d4715475418e028bfd13f7c0e87642`. The supported tail is 732 bytes at `0x36346`, and consumes exactly to EOF.

Reproduce the byte-derived tree with:

```powershell
python tools/scanner/r_demo2_gxm_hierarchy.py `
  --gxm <demo-9.3.1>/DataGx/Vehicles/Trooper/car.gxm `
  --sidecar <demo-9.3.1>/DataGx/Vehicles/Trooper/car.txt `
  --output <scratch>/hull-hierarchy.json
```

The parser is `src/master_rallye/gxm_hierarchy.py`; its deliberately narrow synthetic tests are in `tests/synthetic/test_gxm_hierarchy.py`. The committed JSON report contains node names, byte offsets, spans, child counts and serialized C-index triplets, but no vertex coordinates or game file bytes.

## Serialized record format

The tail starts with a u16-length ASCII `Model` name. It is followed by 28 recursive nodes. Each Trooper node record is:

```text
u8 type (=1) | u8 version (=1) | u16 child_count |
u32 mesh_start | u32 mesh_count | u16 name_length | ASCII name |
child_count recursive records
```

The top-level list contains `shell` and `$chull(Trooper)`. The second root is inferred by exact parse to EOF and sidecar agreement; the outer caller loop at `FUN_005c98d0` has not yet been fully decompiled. All 28 ranges are within the 1,979-record table.

`FUN_005bea30` confirms this association in the exact 9.3.1 executable: it reads the 4-byte type/version/child-count header, dispatches the type, reads the 8-byte range for type 1, reads the name, and recursively reads the declared children. The 0x24-byte type-1 object constructor is `FUN_005cd250`.

The child counts match the corresponding 9.3.1 sidecar nesting: `shell` has 19 direct children. `interior` owns the crew/head/helmet branches; `spare` owns `hub05`. The full detail is in `hull-hierarchy.json` and is reproducible from corpus bytes.

## Runtime object fields

| Object offset | Field | Evidence |
|---:|---|---|
| `+0x00` | vtable/type dispatch | **CONFIRMED_BY_EXE** |
| `+0x04` | first child | **CONFIRMED_BY_EXE** |
| `+0x08` | next sibling | **CONFIRMED_BY_EXE** |
| `+0x0c` | parent | **CONFIRMED_BY_EXE** |
| `+0x10` | last child | **CONFIRMED_BY_EXE** |
| `+0x14` | name pointer | **CONFIRMED_BY_EXE** |
| `+0x1c` | mesh start after loader normalization | **CONFIRMED_BY_EXE** |
| `+0x20` | mesh triangle count after loader normalization | **CONFIRMED_BY_EXE** |

`FUN_004b1a60` maintains child/sibling/parent/last-child links. The `runtime_node_bindings` helper reflects the static mapping to named nodes and link slots; it does not fabricate process pointers. This reconstruction is **CONFIRMED_BY_EXE**, not a debugger-observed live node dump.

## Trooper hull node

`$chull(Trooper)` is one type-1/version-1 node, has no children, and is the second top-level sibling after `shell`.

| Serialized offset | Node | Start | Count | End (exclusive) |
|---:|---|---:|---:|---:|
| `0x36605` | `$chull(Trooper)` | 1911 | 68 | 1979 |

The serialized range agrees with the matching sidecar. The matching name and hierarchy topology make this the `$chull` node found by the static runtime search, with **HIGH_CONFIDENCE_INFERENCE** for mapping this file’s node identity to the runtime object.

## Limit

This file proves serialized hierarchy and the loader's type-1 node layout. It does not prove that raw range `[1911,1979)` remains the final `+0x1c/+0x20` range after the recursive `FUN_005c9990` post-pass. That unresolved rewrite is documented in `hull-runtime-input.md`.
