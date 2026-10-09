# Recovered physical update and mathematical contract

**1733a0 ->173b68** executes two substeps per manager invocation. Global **0x00479c98** stores word **0x3d088889**, float32(1/30). Each step uses half that value: **0.01666666753590107** source time units. This is not independent evidence of a measured 30Hz scheduler.

For each prop, **173cc8 ->269968** processes its integration wrapper; init selects mode1 RK4. The wrapper skips body states whose pause flag is nonzero. **268190** calls the body's force callback, then virtual derivative **266e20**. **266fb8** packs, and **267028 ->2670b0** unpacks, the following 13-value state:

```text
s = [x,y,z, qw,qx,qy,qz, Px,Py,Pz, Lx,Ly,Lz]
ds = [v, .5*((0,omega) Hamilton-product q), Fbase+Fextra, Tbase+Textra]
v = P/m
IworldInv = R * IbodyInv * transpose(R)
omega = IworldInv * L
```

Quaternion and angular vectors use wxyz and world-space omega. The multiplication order is proved by original scalar instructions, not selected to match a preview. Restore normalizes q (`2661e0`, length< float32(.001) -> startup identity) and forms R through **205580**. Body R is row-major, acting on column vectors; scene en3d top-left rows are transpose(R). Static initializer **21cec0** establishes identity quaternion and right/up/forward basis, so those globals are not guessed from zero BSS.

Initial matrix-to-quaternion helper **205628** is a proved caller dependency. Its positive-trace sqrt branch was inspected; the nonpositive-trace branch remains incompletely decoded. The evaluator consequently accepts an explicit quaternion rather than claiming reproduction of every authored initial matrix conversion.

Mode1 stages use original half-stage operation `k*.5*dt`. Weighted final update is:

```text
s' = s + (dt * (k1+k2+k2+k3+k3+k4)) / 6
```

**27d060** writes only gravity F=(0,-g*m,0), with **g=float32 word0x411cf5c3 =9.8100004196167**. Torque and extra force accumulators remain separate. The selected owner/callback paths have no wind or random input. This bounds the negative result; it does not rule out all other accumulator writers in the game.

Post-step `174178` uses contact helper23b6e8 and effective `Physics/RigidBody/MaxClampTime`; its constructor default is1, but live override is not captured. **267e00** checks |v|+|omega|<0.3, restores backup pose and increments a rest counter. Pause compares counter*halfstep against that clamp. No universal friction or damping coefficient is assigned.

The evaluator implements explicit derivative, bounded constant-force linear RK4, quaternion rotation and visual pose. It does not simulate the complete rotation/contact/rest pipeline. Host results are **FLOAT32_RECONSTRUCTION**; PS2 sqrt/division/FPU edge parity remains UNKNOWN.
