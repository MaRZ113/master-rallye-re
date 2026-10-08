# Spline algorithm and numerical boundary

`1a9498` converts cumulative path time into a fractional **control index**
`x = i + (clamp(t,T_i,T_next)-T_i)/(T_next-T_i)`.
For a closed last span, `T_next=T_last+owner.a0`. Closed time >= duration
repeatedly subtracts duration; open lookup clamps at the last knot. On finite,
strictly increasing knots the cursor walk is equivalent to an ordered span
search. Cached index +a4 supports both increasing and decreasing requests.
Duplicate knot backtracking exists in the ELF but unsafe/degenerate routes
are outside the diagnostic's accepted domain.

Let `k=floor(x)`, `u=x-k`, and controls be `P[k-1], P[k], P[k+1], P[k+2]`.
Open indices clamp; closed indices wrap. Position is their weighted sum with:

```text
w0 = -0.5*u^3 + u^2 - 0.5*u
w1 =  1.5*u^3 - 2.5*u^2 + 1
w2 = -1.5*u^3 + 2*u^2 + 0.5*u
w3 =  0.5*u^3 - 0.5*u^2
Q  = ((P0*w0 + P1*w1) + P2*w2) + P3*w3
```

These are the uniform Catmull–Rom basis (`MATHEMATICALLY_EQUIVALENT`). The
actual operations at **1a9c9c..1a9d1c** have the following ordering:

```text
h=u*0.5; a=h*u; b=a*u; d=a+a; e=d+d; c=b*3
w0=(-b+d)-h; w1=(c-(e+a))+1; w2=(-c+e)+h; w3=b-a
```

Loads/stores and component weighted sums at **1a9d20..1a9e00** establish
three-dimensional output. The derivative of the displayed polynomial is
available mathematically, but **the owner does not use it for forward**:
`1a9e08` normalizes successive position displacement. Marker Dir is unused.
There is no Bezier handle interpretation, piecewise linear output replacement
or curve-subdivision array in these branches.

ELF +88/+8c cache behavior is unusual: it compares global x with a value that
stores local u. Closed evaluation explicitly invalidates the cache. The tool
retains that comparison for open evaluation rather than silently improving it.
Weights are usually recomputed; exact knot/end timing and any previous cache
state still matter for an arbitrary restored instance.

| Claim | Fidelity |
|---|---|
| Actual instruction sequence, constants, indices, branch/delay-slot behavior | EXACT_ELF_OPERATION |
| High-level Catmull–Rom formula / analytic derivative | MATHEMATICALLY_EQUIVALENT |
| Python per-operation rounded IEEE float32 timeline | FLOAT32_RECONSTRUCTION |
| Host sqrt, sin, cos replacing PS2 FPU/libm; SVG decimal formatting | APPROXIMATE_MODEL for platform arithmetic |
| Actual R5900 rounding/denormals/exceptions and gameplay trajectory bits | UNKNOWN |

`probe_basis_from_elf` verifies the ELF hash and **executes the original
instruction words** in the basis window with an independent scalar decoder.
It does not call the curve equation. Twenty-four coordinate/index probes
match the reconstruction's host float32 bits; rational-polynomial and straight
line tests independently constrain the mathematics. This is not an emulator
runtime oracle and does not prove PS2 bit equality.

Ghidra analysis uses read-only project `PS2PackFS_MIPS3`, Ghidra 12.1.4 and
ghidra-ai-bridge. Temporary LQ/SQ low64 surrogates, EE MULT-rd low32 surrogates
and positive-finite SQRT operand correction are rolled back. Original
`001a83ac=00431018` implements stride-12 inverse multiplication and
`001a7ed0=00621818` rest*30; their nonzero rd result is important. In the
evaluator, audited MFHI operations consume original DIV, not rewritten MULT.
Only its ignored local query copy bypasses the generic no-HI/LO guard for
that exact window. The original basis probe requires no such substitutions.
Raw listings, surrogate journals and that local query copy stay ignored.
