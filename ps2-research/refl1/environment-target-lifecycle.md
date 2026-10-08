# Environment target: actual writer and lifecycle

The target is mutable because executable code selects its storage as GS FRAME
and emits textured sprites into it. File naming was only the starting lead.
The source is **MIXED_STATIC_AND_FRAMEBUFFER**, CONFIRMED_BY_EXE.

`32f988` begins a presentation pass, clears global42dd38, increments manager+404
and establishes42dd34 from `1 XOR Frontend/SplitScreen`. Its vtable pointer is
stored at485a1c. `330780` draws a resolved visible model, invokes the renderer
draw/flush interface, then follows vehicle helper/data gates. If42dd34 is zero,
or42dd38 is already set, it does not rebuild the target. The first eligible call
sets42dd38. Thus updating is shared once per reset pass, not per car or assumed
per simulation step. The outer live-frame scheduling is not independently captured.

Initialization latch42dd5c looks up two names through2fd7d0:

| Container | Resource | Role |
|---|---|---|
|49b380|CommonTextures\\rendertarget64x64|Target texture cache handle|
|49b388|CommonTextures\\envsource64x64|Static source cache handle|

These addresses are **handle containers**, not invented fixed VRAM allocations.
`2fa058(renderer+144,&handle)` resolves each texture descriptor through42ea88.
`3179c8` drains pending host-image uploads before target generation. It uses
BITBLTBUF/TRXPOS/TRXREG/TRXDIR/IMAGE; the feedback itself uses textured draws.

At33257c and3325c8, original R5900 registers establish the full31a518 ABI:
a0=chain,a1=source FBP,a2/a3=source width/height,t0=source PSM,
t1=destination FBP,t2/t3=destination width/height; stack+0=destination PSM,
+8=FIX,+10=D selector,+18=vertical flip. Both source/destination PSM arguments
are2 at these calls (PSMCT16). The generic o32 decompiler's apparent fifth
argument is not sufficient; original `li t0,2` at332540 and3325b8 controls it.

| Pass | Source | D | FIX | Flip | ALPHA | Nominal color |
|---|---|---:|---:|---|---|---|
|1|ENVSOURCE descriptor|2 zero|80|No|00000050000000a8|Cs*80/128|
|2|Framebuffer42d298, W42d29c,H42d2a0|1 destination|48|Yes|0000003000000068|Cs*48/128+Cd|

The nominal result is0.625*EnvSource+0.375*FlipY(current framebuffer), subject
to PSMCT16 interpretation, filtering, rounding and GS color saturation. This is
not an offline pixel simulator or a claim of bit-identical RGB values.

The helper creates source-width32-pixel columns, maps them to the target extent,
sets FRAME/TEX0/CLAMP/ALPHA/TEST/ZBUF, emits UV/XYZ2 sprite corners, then restores
framebuffer FRAME/XYOFFSET and flushes textures. Its MSCAL373 packet feeds the
same embedded GIF copy/flush path and VIF1 chain as the vehicle renderer.

The target cache identity is shared: handler3ade58 writes the same interned target
name into mesh+38;3714e0 resolves it into mesh+e4, and312130 binds the secondary
TEX0. No per-vehicle target, alternate-name alias, ping-pong pair or framebuffer
storage alias is proved. Physical bases and image contents require a capture.

Two release callbacks are registered at330770/330778 for the handle containers.
Their exact teardown bodies and context-loss/reload behavior remain unexamined.
Missing-resource fallback in this selected producer is UNKNOWN; the diagnostic
fails closed on missing canonical resources.

No extra environment camera, mirrored scene traversal or six-face capture appears
in this bounded writer. Vehicles are not proved excluded from its framebuffer
source. The code runs after one model draw, so consumers before/after the writer
may observe different target generations. Do not describe all vehicles as sampling
the same instantaneous current frame without queue/capture evidence.
