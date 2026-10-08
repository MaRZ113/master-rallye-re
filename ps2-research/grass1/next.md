# One next phase

**Recommended: PS2-GRASS2 — VU1 residency and targeted detail capture.**

The highest-value remaining work is the exact final boundary of this proven
producer: prove upload/residency of the decoded `.vudata` MPG programs selected
by MSCAL449/37c, trace the final output-ring flush, then correlate one
unchanged-ELF detail batch with a controlled PCSX2 frame. This is a bounded
continuation of grass research, not a universal VU/GS renderer or a PC port.

1. **Enough to reproduce on PC later?** CPU source selection, category,
   grid/jitter/height and binding are well specified. Faithful final geometry
   and visual parity still require residency/last-flush proof and captured
   transform state; answer is partial despite the decoded corner/STQ contract.
2. **Deterministic placement?** The original fixed seed and world-coordinate
   hash give repeatable jitter for fixed inputs. Full populations also require
   clipping/history/order and FCSR/initialization provenance.
3. **Enough current PC terrain/material data?** Ground surfaces/materials exist.
   The PS2-specific detail categories and certified source-to-draw correspondence
   are missing; the current PC draw interface is not proved sufficient.
4. **Which future layer?** Material/Course SDK interface plus runtime generation
   and a renderer consumer. Asset reuse alone or an unannotated D3D8 wrapper
   is insufficiently supported. No implementation choice is finalized.
5. **How much PS2 geometry?** Targeted spatial-source records are decoded across
   36 models. The embedded two-corner sprite output is decoded. Need residency
   and, for parity, visual-strip
   equivalence; no full universal model/GS reverse is required.
6. **Runtime capture necessary?** Yes for independent corner/UV/state/visible
   confirmation and camera-history behavior. It also resolves the frame guard,
   ring latency and live projection/FCSR values.
7. **Common infrastructure?** Shared model vertices/spatial query, resource
   manager and packet-state helpers are useful leads. No water-detail equivalence
   is assumed from this fact.
8. **Surprising subsystem?** The decorator uses spatial/collision triangles and
   deterministic lattice jitter, with stones/singular shrub excluded. No new
   large visual subsystem was identified in this bounded path. CPU wind was
   not found; the matching embedded program also has no wind/time deformation,
   conditional on its residency. Projection is a screen-aligned GS sprite.
9. **Why this single next phase?** It closes the only essential primitive/render
   execution link left in an otherwise strong causal chain and verifies that
   the decoded sprite program is the program actually executed.

Turkey3's PS2 puddle discrepancy remains a visible, valuable future lead from
CDELTA1. Water, reflection, treeblend, BirdManager and AMBIENT1 runtime closeout
are deferred; none begins as part of GRASS1/its recommended bounded continuation.

## Read-only runtime experiment

Record canonical ELF SHA, ISO/container hashes, PCSX2 build/config, save/course
identity and captured camera/FCSR. Use France1 material4/source9174 region and
a nearby material8 none region; retain authored source hashes. Do not patch
the ELF or force categories.

Break/read at `3375a0/357e70` to record owner42dd2c and snapped region;
`357628` to capture source ref/material ID; `357378` to associate one generated
Vec3 with its source; `3597e0/31da60` to capture its record, resource handle and
group count. Resolve `31dce8` REF address and `31e010` DMA CALL. Capture resident
VU1 pc449 and state pc37c plus resulting GIF packet/registers, identifying the
bound grass/bush texture and final sprite corners/UV. Pair a paused screenshot
or short video with the same frame/batch identity, not an unrelated grass image.

Repeat with unchanged camera, moved/revisited region, shrubs, slope-pass none,
stones and singular shrub. Compare original captured inputs against the offline
float32 reconstruction before judging appearance. Record unsupported debugger
surfaces as BLOCKED/SKIP; a screenshot or synthetic diagnostic is never runtime
PASS. No supported running PCSX2/debugger session was available in GRASS1.
