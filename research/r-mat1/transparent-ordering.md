# Vehicle transparent submission and ordering

**CONFIRMED_BY_EXE:** the relevant path separates opaque and alpha-blend
queues and sorts them before emission. It does not simply preserve source
draw order, nor sort individual triangles in a material node graph.

## Call chain

`0054D450` builds compiled draws. Compiled draw constructor `00576570`
sets vtable00692364; virtual+30 is `00576910`. The hierarchy walker `0054C9D0`
calls this submission method. `00576910` finds the pass count and submits
through `00562560` into the queue returned by `00570B10`.

`00562560` tests `[compiled+38]->shader+14 &1`; `00565DA0` sets that flag
only for the base_alpha/base_env_alpha vehicle families. Each 24-byte record
stores instance, compiled draw, pass index and key at+10/+14. Opaque/alpha
records use queue vectors+24/+34 respectively. `00562810` sorts and flushes
opaque records first, then alpha records; both emit through `00576970`.
Alpha-test families belong to the opaque queue.

## Depth and exact alpha key

`0054C9D0` calls `00562430` to place a shared object/bound depth at queue+14.
The projected expression is:

```text
d = clamp(((bound.center - camera.position) dot -camera.direction
           + bound.radius) / max(camera_far_scalar, minimum_scalar), 0, 1)
q = trunc(d * 16383.0)
```

The bound is shared by subsequent submissions from that walker; this is
camera-direction depth plus radius, not Euclidean camera distance or a
per-triangle centroid. Constant006911D0 contains float32 `0x467FFC00`=16383.
The integer conversion helper005C2E5C changes the x87 control word to truncate.

Assembly `00583880` produces a 64-bit unsigned alpha key:

```text
K = ((pass_index & 7) << 61)
  | ((16383 - q) << 47)
  | (min(order_counter, 32767) << 32)
  | ((shader_id & 0xFFFF) << 16)
  | (first_compiled_texture_handle & 0xFFFF)
```

Focused instructions establishing the depth field:

```asm
005838EB FLD  [ESP+20]       ; depth argument after register saves
005838EF FMUL [006911D0]     ; 16383.0
005838F9 CALL 005C2E5C       ; __ftol, truncation
005838FE MOV  ECX,3FFF
00583903 PUSH 8000          ; multiplier HIGH dword
00583908 SUB  ECX,EAX
0058390F SBB  EAX,EDX
00583911 PUSH 0             ; multiplier LOW dword
00583913 PUSH EAX
00583914 PUSH ECX
00583915 CALL 005C4DF0       ; __allmul: factor = 0x8000 << 32 = 1 << 47
```

The high dword position is essential: treating this as multiplication by
0x8000 would incorrectly overlap shader/depth fields and obscure depth order.
`00562810`/`005635A0`/`00563950` compare key high dword first, then low,
ascending unsigned. Thus within the same pass, larger projected bound depth
is emitted first. Counter/shader/texture break depth ties, not the other way
around. The order counter increments per alpha submission when queue+1C is
enabled. The traced key and condition are exact; all scene callers configuring
that grouping flag are not reconstructed. Equal complete keys have no proven
global stable source-order guarantee.

Opaque key `00583820` groups pass/state/texture:
`((pass_index &7)<<29) | ((shader_id &0x1FFF)<<16) | (first_handle &0xFFFF)`.
It contains no depth field. Scope ends at the relevant flush and key routines;
no general renderer reconstruction is needed.

## Blender implication

The scene-level queue, shared bounds, quantization, pass ordering, and depth
instance overrides cannot be encoded exactly in a static material graph.
V3 records `COMPOSITE_RUNTIME_SORT_NOT_REPRODUCED` and uses Blender's available
transparency approximation with overlap enabled. A node-test or screenshot
does not prove equal in-game ordering. No new runtime probe is needed to
resolve the static queue model; no new human sorting PASS is claimed.
