# Linear vertex fog and environment parameters

**CONFIRMED_BY_EXE:** common emission `0x00576970` enables fog only when renderer
flag+0x7C allows it, parameter block+4 enables it, and instance+0xAA enables it.
It writes FOGENABLE28=1, FOGCOLOR34=packed RGB, FOGVERTEXMODE140=3 (LINEAR),
FOGSTART36 from block+0x24 and FOGEND37 from block+0x20. Disabled branch clears fog.

Setter `0x0056D020` stores this block at renderer+0x54. It fixes near+0x1C=0.2,
distance/end+0x20=300/400/500 for ViewDist0/1/2. Fog span at block+0x18 is clamped
0..1; start=end*(1-span) when enabled, otherwise start=end. Sky initialization
`0x004B1180` supplies enabled=true and span0.9, hence start30/40/50 for those presets.
Projection far is twice end, so far clip and fog end must not be conflated.

Sky CloudNumber0..6 selects RGB and sends environment data through renderer virtual
+0x38 (`0x0056D020`). Network session routines0x004343C0/0x00433EC0 serialize/consume
CloudNumber; complete local track/event/replay selection policy still needs tracing.
`Sky/fog color` and bottom-height fields are present in scene data,
but initialization overrides the first sky layer's RGB by selected cloud palette.

Table fog mode defaults0 and range fog defaults0 in runtime state tables. No active
exponential/density/range-fog path is established in the reviewed common emission.
**STATIC_INFERENCE:** this is a renderer-global environment block with per-instance
enable, fed by sky/quality setup. Other camera groups may select different values;
runtime logging must verify the actual scope and transition order.
