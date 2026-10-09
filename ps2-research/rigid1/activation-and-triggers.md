# View-qualified activation, contact wake and far pause

**1a0258** queries the first registry view and, if needed/available, the second (`201350`, registry count+10). For each, it calls `200550(view,entity en3d translation,radius=4)` and computes:

```text
d2 = (view.c0 - model.world.x)^2
   + (view.c4 - model.world.y)^2
   + (view.c8 - model.world.z)^2
near = shared_view_predicate && d2 <= 10000
```

The fixed boundary is inclusive and **three-dimensional**. It is not authored 5/15, a car-position test or a radius derived from the hull. Camera-entry ownership for a selected live frame has not been captured. DRESSING1 independently recovered `200550`: four side-plane tests with strict radius bound, plus optional graphics-config range/back-direction checks. The evaluator requires its explicit Boolean result instead of synthesizing a camera.

| Condition | Consequence |
|---|---|
| Initially paused, settled, near | retained paused; proximity alone does not wake |
| Successful active vehicle/paused-prop collision | dispatcher16e498 clears body pause and rest counter |
| Near and already active, not acknowledged | acknowledge contact wake |
| Near and owner far-decay state | resume body, clear counter, acknowledge |
| Far and active | pause; begin 60-invocation decay |
| Far and already far-decaying | keep remaining counter |
| Paused after physics sleep with acknowledgment | owner marks settled |

During far decay, each invocation except the last scales momenta/velocities by **float32(1/60)** and recomputes consistent momenta. On the last invocation it zeros them. This is a very strong invocation-dependent reduction, not `dt`-scaled friction. The counter is not restarted every far frame. Runtime owner cadence and pause/menu scheduling remain UNKNOWN.

`rigid_runtime.Activation` reproduces these branches for explicit state. It models neither narrowphase success nor live view ownership.
