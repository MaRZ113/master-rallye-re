# Detail ownership and lifecycle

The recovered owner is a procedural terrain decorator allocated by the world
draw integration, rather than an authored scene shrub entity. No original class
name/RTTI is claimed. Addresses below are canonical ELF VAs.

`330780` calls integration `3375a0` at `330d6c`. When the landscape model has
a non-null `+0x2c` spatial proxy and global `42dd2c` has no owner, the wrapper
allocates **0x106c bytes** and calls `34e698(owner, model)`. It obtains camera
X/Z from `+0xc0/+0xc8` and supplies width **60.0** to `357e70`. It then calls
packet builder `3581e8` with the render owner's `+0x404` frame key.
These links are `CONFIRMED_BY_EXE` through original direct/virtual targets and
loads; no runtime owner address was sampled.

| Owner offset | Recovered role |
|---|---|
| `+0x0000..0x0fff` | 1024 float alpha/fade lookup entries |
| `+0x1000/+0x1004/+0x1008` | Prior snapped X/Z center and region width |
| `+0x100c` | Placement pitch `float32(1.33)` |
| `+0x1010/+0x1014/+0x1018` | Current snapped X/Z center; Y explicitly zero |
| `+0x101c` | Landscape model pointer |
| `+0x1020` | First activation flag |
| `+0x1024` | Selected pool index; `-1` excludes |
| `+0x1028` | Compared with frame key in builder; constructor zero; later writer UNKNOWN |
| `+0x102c/+0x1030/+0x1034/+0x1038` | Grass/shrubs/stones/none interner IDs |
| `+0x1040..0x1048` | 100-slot resource-handle cache storage |
| `+0x1050..0x1058` | Scanline left/right bounds vector |
| `+0x105c..0x1064` | Two category records, **0x44-byte** stride |
| `+0x1068` | Render-context/packet-ring owner |

Each category record contains active/free ID vectors, a dense Vec3 array at
`+0x24`, active count `+0x30`, maximum count `+0x34`, used-ID count `+0x38`,
category lift/size `+0x3c`, resource-name ID `+0x40`. Pool 0 is shrubs and pool
1 grass. Constructor reservations of 1536 point slots and 3072 render records
are initial capacities; subsequent code grows them. They are not hard caps.

`357e70` runs from the frame integration, but only changed snapped regions
trigger pruning/generation. `357c38` recycles out-of-region points, compacting
with the last active point. `357378` appends points and maintains ID mappings.
`3581e8` constructs category packets and rotates the three handles at render
context `+0x14/+0x18/+0x1c` after completing a packet. `359610`, called from
`32ff28` at `32ff4c`, submits the completed ring handle to the common renderer.
Exact effective ring latency requires capture.

World teardown `338d88` calls `355af0` and clears global `42dd2c`. The destructor
releases category storage, name IDs/caches and render context. No original
assets or executable are rewritten. Resource manager and allocator internals
are followed only where they explain this owner/binding.

Open lifecycle questions: the `+0x1028` writer/same-frame guard, `+0x103d`
initial semantics, RNG-table guard `42fe78` writer/reset, and behavior if several
landscape models with eligible proxies coexist. The current evidence establishes
the actual stock integration, not an invented per-material object hierarchy.
