# Sampling, speed and clock

Preparation `1a8330` builds **N XYZ controls and N cumulative times**. For
each ordinary chord `d_i=length(P_i-P_(i-1))`:

| Mode | Intervals | Closing time a0 | Consequence |
|---|---|---|---|
| Const=True | `d_i / speed` | `length(P0-P_last)/speed`, **also for open paths** | Curve speed varies within each chord-timed span; open endpoint has an extra stationary hold |
| Const=False | Common `delta=(L/speed)/N` | delta if closed, otherwise zero | Equal time per control span, so spatial speed follows chord/curve geometry |

In nonconstant mode `L` sums ordinary chords and adds the closing chord only
when closed. Open total time is `(N-1)*delta`, not `L/speed`. In constant mode
total time is `last cumulative time+a0`; open position stops at the earlier
last cumulative time. The closing value is set unconditionally at
`1a85f0..1a86a0` in the constant branch. No arc-length inversion, cumulative
curve-distance table or exact uniform-speed guarantee was recovered.

Internal flag +20 defaults zero and has no writer in ambient XML config.
If externally set, prep enters an acceleration-constrained branch:
`desired_a=((d/delta)^2-v^2)/(2*d)`, clamp with `15ace0` to
`[-owner.4c,+owner.48]`, `v_next=sqrt(v^2+2*a*d)`, and ordinary span time
`2*d/(v_next+v)`. Its closing computation uses `(v_next-v)/a` and appends an
additional endpoint record. This is a dormant internal branch, with zero-a
and repeated-point hazards; it is not what `Use Const Speed=False` selects
for the 24 configured ambient owners. The diagnostic does not expose that
unserialized mode or invent a per-frame acceleration state.

**Number Of Samples** is unrelated to route subdivision. Init allocates/fills
that many float zeros through `1551c0` into owner +110/+114/+118. Active ticks
advance +12c modulo +120 before banking, and bank uses +124=float(samples) to
subtract the overwritten sample's contribution and add the new one. Changing
the count leaves curve controls, time knots and position evaluation unchanged;
it changes the smoothing window and ring behavior. Buffer growth/capacity
details belong to a generic vector helper, not a second route table.

`1aa3b8` increments +68 by constructor constant +64 = `0x3d088889`, IEEE
float32 1/30. No elapsed-time argument is consumed by the owner. Rest seconds
are multiplied by integer 30 in config; bank estimates displacement speed
with float 30. Thus scene-units per **nominal controller second** is a useful
interpretation of speed, but actual host/emulator tick cadence, pause and
render interpolation require runtime measurement. Do not call it a proved
30-FPS display rate.
