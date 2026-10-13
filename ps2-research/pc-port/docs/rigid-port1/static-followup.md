# Native interface closeout after Grass2

**PS2-RIGID-PORT1: BLOCKED_ON_NATIVE_COLLISION_RESOURCE_AND_OWNERSHIP.**

This second bounded read-only check resolves much more than a candidate physics class, but it does not supply a safe spawn implementation. Exact PC executable identity remains `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. REA/Ghidra and installed GNU objdump independently supplied the following contracts. Runtime validation was not performed.

## 1. Egg creation and ownership are concrete

Native Egg construction is **0x004F5670**. The original RaceStarter allocates 0x78 bytes and calls it at **0x0048E6C1**. The constructor initializes four AI slots, allocates a separate 0x78-byte en3d object through **0x004F5A80**, and links the Egg's +0x60 node into the entity manager's pending list. It does not immediately make the Egg a fully admitted live object.

**0x004F59F0** changes the interned name at Egg+0x5C by unregistering/re-registering through **0x0050E650 / 0x0050E450**. **0x004F61A0** transfers pending entities through **0x00509750** and then runs the live AI update callbacks. These are native insertion and admission routines, not justification for editing intrusive lists manually.

**0x004F5840** marks the Egg retired and queues deletion; **0x004F5780** unregisters its name, destroys AI/render resources and unlinks its nodes. **0x004F60F0** drains the full scene's deletion, pending and priority lists. AI slot setter **0x004F5950** destroys any previous slot owner, so a new physical pilot must own a fresh Egg rather than borrow a stock object's AI slot.

## 2. Actual installed collision backend and shape binding

Engine initialization **0x0053F060** allocates the 0x34-byte concrete backend with **0x0056EB40**. Store **0x0053F12B** installs it in the collision service singleton +0x08. Its actual vtable is **0x00692318**; +0x0C selects **0x0056EEF0**. This replaces the generic default-backend uncertainty for the selected static initialization path.

The attachment sequence is:

```text
Egg+0x50 -> en3d+0x0C model resource ID
 -> 0x0054B320 resource lookup
 -> returned wrapper+0x04 model
 -> model+0x0C convex prototype
 -> 0x00621220 clone, native allocation0x1C
 -> 0x00621310 bind physical body
 -> 0x00621330 bind category
 -> native backend instance vector+0x14/+0x18/+0x1C
```

`0x00621310` stores the body in instance+0x0C, both representation objects+0x38, and base object+0x08. The category setter writes instance+0x10, both representations+0x3C, and base+0x0C. Attachment also writes the Egg name ID to instance+0x14. **0x006212C0** destroys the cloned representations/base. The original clone/insertion path uses native insertion helper **0x0056FE10**, not a foreign allocator or a renderer-side vector.

The PC tag101 producer is also concrete: **0x0057CE60** creates a 0x1C-byte prototype, reads base via **0x0057D640**, then two representations via **0x0057D140**. Model-load store **0x0055170C** places its result at model+0x0C. This agrees with the strict existing Course SDK tag101 wire reader and explains the exact native attach field. It does **not** make a PS2 PSM interchangeable with PC DX as a whole.

The missing private-resource interface is precise: a validated native input stream to `0x0057CE60`, owned registration/cache result consumed by `0x0054B320`, and its release ordering. Creating a fake native model wrapper or silently substituting the PC hay hull would bypass those unresolved contracts. Directly cloning/inserting a source prototype could avoid a visual DX dependency, but its complete allocation/rollback/unregistration contract is still unproved and is not enabled here.

## 3. Teardown exposes a real stale-pointer hazard

Native nonvehicle body **0x004FE980** stores the entity name at body+0x1D0 and a resolved entity cache at +0x1D4. **0x0043F450** removes a body only after attempting resolution when that cache is already zero. Collision-manager cleanup **0x0043AB70** uses the same condition. Backend cleanup **0x0056EDE0** similarly re-resolves convex instance+0x18 only when it is zero.

Therefore, retiring/destroying an Egg alone is not a proved safe one-object removal operation: a nonzero cached entity pointer can survive the lookup path. The inspected `AISimulateeTransform` deleting destructor **0x004F5320** frees that owner without visibly invalidating body/collider caches. Full manager destruction **0x0043E020** owns body deletion, but the inspected static code does not certify every scene exit/restart ordering for an injected entity. Do not call the body destructor separately while manager/collision vectors still own it.

Original physics manager update vtable `0x006900B8` +0x10 selects **0x0043F2C0**. Existing verified physics-observer callsites inside the per-car update/substep routines can establish thread/timing context; they are observers, not an already approved safe injection callback. D3D EndScene is not a physical-scene mutation boundary merely because it runs on a render thread.

## One remaining targeted experiment

Perform **one read-only cold Turkey3 native convex lifecycle capture**, from course/model loading through normal race exit. Use one original vehicle's convex instance as a shared-interface control, recording `0x0057CE60`, `0x0056EEF0`, `0x00621220/0x00621310`, actual backend vtable, model/resource IDs, body/entity caches, physics-update thread and deletion order. Include same-course restart in that same bounded lifecycle capture if practical. Do not spawn a new object for this observation.

That capture can corroborate the common reader/clone ABI and original ownership ordering; it cannot certify a private tumbleweed by itself. The subsequent one-object implementation must add and test an owned bounded stream/resource bridge, use the original hull and mass5/MOI(2,2,2), and prove cache invalidation/unregistration before runtime removal. No physical collision or vehicle impulse is claimed from passing source tests.

Yellow barrels retain their separate blocker in `checkpoint-boundary.md`: their authored visual Eggs do not use `gaAiRigidBody`. No barrel physics is derived from the newly resolved PC hay/tumble candidate path.

See `static-followup.json` for exact function bounds and REA Evidence IDs. Ghidra's default database left `0x0056EEF0` and `0x0056EDE0` undefined; their entries come from original vtable bytes, and their relevant instructions were decoded independently from the original PE. No guessed Ghidra functions, game patches, process writes or broad physics implementation were introduced.
