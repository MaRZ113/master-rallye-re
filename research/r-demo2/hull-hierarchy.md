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

The top-level list contains `shell` and `$chull(Trooper)`. R-DEMO2.5 confirms the outer type-2/version-7 header at file offset zero (`0x00020702`) declares two children: `005bea30` dispatches `005bdf40` for the model body, then reads its name and children. `FUN_005c98d0` is later 2D processing, not the hierarchy loader. All 28 ranges are within the 1,979-record table.

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
| `+0x1c` | mesh record start | **CONFIRMED_BY_EXE** |
| `+0x20` | mesh triangle count | **CONFIRMED_BY_EXE** |

`FUN_004b1a60` maintains child/sibling/parent/last-child links. The `runtime_node_bindings` helper reflects the static mapping to named nodes and link slots; it does not fabricate process pointers. This reconstruction is **CONFIRMED_BY_EXE**, not a debugger-observed live node dump.

## Trooper hull node

`$chull(Trooper)` is one type-1/version-1 node, has no children, and is the second top-level sibling after `shell`.

| Serialized offset | Node | Start | Count | End (exclusive) |
|---:|---|---:|---:|---:|
| `0x36605` | `$chull(Trooper)` | 1911 | 68 | 1979 |

The serialized range agrees with the matching sidecar. The matching name and hierarchy topology make this the `$chull` node found by the static runtime search, with **HIGH_CONFIDENCE_INFERENCE** for mapping this file’s node identity to the runtime object.

## Current scope

R-DEMO2.5 resolves pre-hull provenance for the pinned 9.3.1 Trooper offline pair: the `$chull` positions cannot participate in a weld, and its 68 records retain their C indices. `FUN_005c9990/FUN_005ca370` range rewrites happen after hull construction. See `hull-runtime-input.md` and `vertex-welder.md` for Path B and the distinction between a static/offline reconstruction and captured native buffers. This does not generalize to other node types, sort-plane meshes, non-isolated weld classes or the 8.4.1 crash asset.
