# Randomness, flight equations and group behavior

The original FlyBird path uses process-global RNG accessor`1d5f70`, state pointer`4262a8`, constructor`1d5de0` seed12345, integer update`1d5df0`. This is shared engine state; its constructor seed is not a recovered per-course spawn seed. Other consumers and prior calls change the sequence. Repeatability between loads or visits cannot be promised without their state/history.

For signed32 input s, signed division truncates toward zero:

```text
q = trunc(s / 44488)
r = s - q*44488
v = signed32(r*48271 - q*3399)
if v <= 0: v = signed32(v + 2147483647)
state = uint32(v)
unit = float32(state & 0x00ffffff) * 2^-24
U(lo,hi) = float32(lo + float32(unit * float32(hi-lo)))
R(lo,hi) = lo + floor(float32(unit * float32(hi-lo)))
if R == hi: R = lo
```

For normal positive states the integer recurrence agrees with Park–Miller multiplier48271 modulo2147483647. The original **float output uses low24 bits**, not state/modulus. Tests use an independent modular oracle over1000 positive states. Original DIV/MFLO/MFHI and EE MULT words at`1d5e0c..1d5e24` support the integer reconstruction. Explicit low32 MULT surrogates are used only at audited sites; HI/LO is not modeled by that surrogate. No original executable is patched.

FlyBird ctor`1b0950` installs vtable473bd0: origin O at+c/+10/+14, direction D at+18/+1c/+20, parameter24=100, speed v=15, travel L=0. `1b0a40` makes six RNG draws in this order:

1. v += U(0,15).
2. t = U(0,60).
3. parameter24 += t if unit>0.5, otherwise -=t.
4. r = U(0,0.12).
5. sign = +1 if unit>0.5, otherwise-1.
6. h = U(0.001,0.2).

Let W be normalized `(observer.x-O.x,0,observer.z-O.z)` and P=`(W.z,0,-W.x)`. Form `D=normalize(replaceY(-(1-r)*W + sign*r*P,h))`. Squared length<=2^-23 produces zero instead of a divide. Initial direction points mostly away from the horizontal observer with a small sideways term and positive rise. Marker Dir is not an input. The source observer comes from the registry; offline input is explicitly synthetic or captured.

Virtual wrapper`1b0e48` calls actual tick`1b0e68`:

```text
if D.y < float32(0.35): D.y += U(0.001,0.05) / 30
v += U(0.1,2.5) / 30
L += UPDATED_v / 30
position = O + CURRENT_D * TOTAL_L
```

Each arithmetic operation is rounded to float32 in the diagnostic. Rise is neither re-normalized nor clamped after an increment. Position is recomputed from fixed origin and total travel, **not** incremented by velocity from the previous position. Parameter24 is passed in f12 to`1b0f88` but the original helper does not read f12; no invented sinusoidal height/wing function is attached to it.

`1b0e68` writes carrier translation at entity+50 → carrier+50/+54/+58, homogeneous W+5c=1. `1b0508` copies these fields into entity+4c en2d. FlyBird does not produce a heading/yaw/pitch/bank basis. Rendering supplies the camera-facing basis separately. This establishes motion through actual world translation stores, rather than stopping at a hypothetical position output.

The fixed divisor30 is per invocation. Wall-clock frequency, pause and scheduler interleaving are UNKNOWN. The diagnostic exposes update count, not an invented arbitrary dt or fps. Numerical precision is **FLOAT32_RECONSTRUCTION** using host IEEE arithmetic/sqrt/div; original instruction selection/order is verified, but bit-exact PS2 FPU behavior is not claimed.

No route interpolation, target-arrival event, looping path, neighbor lookup, separation/alignment/cohesion or leader-following occurs in this FlyBird chain. A burst's common origin plus individually random directions explains a possible group without proving observed flocking. Classification: **INDEPENDENT_BIRDS_WITH_SHARED_SPAWN_ORIGIN**, CONFIRMED_BY_EXE. Live formation remains unobserved.

Miller (`1b1030`, `1b1128`, `1b1280`, `1b1408`) has a separate plane-normal/origin and random horizontal walking direction/speed. Its plane residual adjustment is not a general FlyBird terrain-height query. Normal Miller population activation is missing, so this phase does not build a speculative ground-bird simulator or collision integration.
