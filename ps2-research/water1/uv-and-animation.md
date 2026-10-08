# UV, color and temporal behavior

The traced water paths do not write source/cached XYZ as a wave deformation.
They operate on authored strip surfaces through UV/color and ordinary scene
matrices. This negative evidence applies to these handlers and the decoded
compatible VU strip path, not every graphics effect in the game.

`316808` sets phase **T = float32(unsigned caller counter)/150.0** at42dc40.
When Game/PauseMenuEnabled exists and is true, this phase remains unchanged.
The original counter's real-time units and its caller cadence are unresolved;
one repeat per second, frame-rate independence and all pause behavior must not
be inferred from the literal divisor.

`328c90` initializes4096 sine samples using the original float32 full-circle
constant returned by `15acc8`, word **40c90fdb**. Host libm was not substituted
and claimed exact. FCSR rounding, EE underflow and fused/ordinary operation
details still limit numerical parity.

For puddle's cached UV update `320c78`, define lookup L by masked12-bit index,
and R as the original FCSR-dependent conversion. With source position x,z:

```text
a = .1*x + 1.61368*T
b = .1*z + T
A = L(R(a*1.13*4096/C)) - L(R(b*1.78*4096/C)+1024)
B = L(R(a*2.19*4096/C)+1024) + L(R(b*2.93*4096/C))
primary UV = (.05*x+.05*A, .05*z+.05*B)
```

Secondary UVs use the source normal perturbed by .6*A and .6*B, global basis
fields at42dc00..42dc28, .02*x/.02*z and .5 bias. The basis's exact setter and
camera/world ownership were not proven. Normal-dependent coordinates are real
operations; interpreting them as a complete dynamic reflection is only
**STATIC_INFERENCE**. The traced resource is a static common GXI.

Puddle load callback `320938` queries spatial source hits at X/Z, excluding
water-named hits when several hits allow a ground choice. It starts channels
at254 and, when a usable height exists, computes all four channels from
`clamp(rounded(255*(1-1/(2*abs(puddleY-groundY)+1))),2,254)`.
The first channel explicitly adds the gap twice; remaining channels reuse the
doubled gap. Packet production then multiplies source channels by .5. This is
an authored-surface/ground-dependent appearance weight, not geometry generation.

Ordinary water's load preparation `320f90 ->321098` computes normal/position
UVs and sets RGBA254. Its auxiliary frame-update callback is empty and flag0;
the traced renderer does not repeatedly invoke that UV preparation solely
because the frame counter changes. Generic cache rebuild or other transforms
remain distinct possibilities.

Waterfall/waterall's `321838` uses two hardcoded vertical layers:

```text
base = original_inline_floor(.05*first_source_Y + 6)
primary V   = (.05*source_Y + frac(2*T)) - base
secondary V = (.05*source_Y + frac(4*T)) - base
secondary U = primary U
```

The inline floor's negative subunit edge behavior is preserved through the
already tested `detail_runtime.ee_floor`; it is not blindly replaced by host
math.floor. `water_runtime.py waterfall-uv` evaluates this bounded formula with
explicit supplied counter/Y/U, labels inputs diagnostic and precision
**FLOAT32_RECONSTRUCTION**. It does not turn `$scroll(v,+1)` into a speed.

The statically decoded puddle VU helper3dc..3f1 additionally subtracts a common
integer UV minimum per packet, preserving relative coordinates while limiting
magnitude. Its CPU selector is3; ordinary water uses0. Program bytes and CPU
upload address are grounded, but live micro-RAM execution was not captured.
