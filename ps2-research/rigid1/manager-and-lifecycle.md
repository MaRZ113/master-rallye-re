# Simulation manager and lifecycle

The factory calls **1715c8 at 15cd44** to construct the 0x74 `gaPhysicsManager` with vtable 0x00474050. This is a real owner of the registered prop-body vector, not only a scene configuration name. `19ff18 ->171c78` unconditionally allocates the physical body (0x1dc), constructs it with `2662f8`, appends it to the manager's +20 vector and invokes virtual pose initialization `2668b8`. Proximity is not the allocation trigger.

Init binds landscape/vehicle systems (`172dd8`). Prop scheduling is shared with that manager, while vehicle integration `1782c0` and publication `178028` remain separate and outside this reverse. Owner initialization also attaches the physics transform AI to the same scene entity through `21e620`.

```text
manager update 1733a0
 -> prepare 1733e0
 -> two physics substeps 173b68
 -> post-step / pose publication 174148
    -> sleep decision 174178
    -> prop publication 174318 ->267f60
 ->174588 bounded empty helper
```

Manager destructor **171a10** destroys body entries and relevant helpers. Physical-body destructor **2667e0** destroys its integration wrapper (`2682d0`) and base. Owner destructor **1cfe90** does not itself own/delete the body vector. Individual carrier-AI teardown, mid-course unregister and course restart ordering remain bounded unknowns; no complete reset claim is made.

Initialization renames the entity to the finite `RigidBody%d` pool, sets entity+6c to 2 and calls `21e740(entity,3)`. The semantic scheduling names of these flags are not invented. The en3d 64-bit field at +70 gets bit32 set; bit0 at +74 is the same high-half bit, not another independent flag. DelayInterpolation later changes high-half bit2. None of these operations alone proves a shadow render.
