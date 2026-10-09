# Collision representation reaches the body

Body registration follows `171c78 ->16df68 ->16e1d8`. The last uses virtual +24 of the installed collision backend. The original interface accessor `2015d8` begins with a no-op default backend; its presence is not proof that collision is disabled. Concrete PS2 init instructions at **2dc664** call **2e29b0**, and **2dc680** stores the result in singleton+8. The containing init function start is intentionally UNKNOWN.

Concrete vtable **0x00484110** selects **2e2f10** for attach and **2e3270** for pair tests. Attach resolves the entity's en3d model ID through resource helper **303038**, obtains model+34, then **244108** instantiates its convex container. **244230** writes the physical body pointer to instance+10, both representations+2c and base+08. **244250** similarly assigns the surface category. This is the actual model-to-body shape link (`CONFIRMED_BY_BOTH`).

`2e36e0` attaches a small collision carrier AI (`2ef400`) to the same scene entity. `2e3630` avoids a second carrier for an entity already associated; this is not deduplication of separate Eggs with identical transforms.

```text
tag101 model+34
 ->303038 model resolution in2e2f10
 ->244108 convex instance
 ->244230 body pointer /244250 category
 ->entity carrier and detector registration
 ->16e498 pair dispatch through2e3270
```

All arrow roles are grounded in original load/store/call evidence. The dispatcher selects convex/convex `24d870`, convex/BSP `2470f8`, and convex/cylinder `24ace0`; full algorithm interiors and representation-stage selection were not reconstructed. No static hull is promoted into a live contact capture.
