# Logical coordinates: proven pieces and remaining composition

## Direct ELF evidence

`2dd510` divides authored viewport X/width by **640.0**, Y/height by
**480.0**, then multiplies by physical raster dimensions at `42d29c/42d2a0`.
It constructs inclusive scissor endpoints x+w-1/y+h-1 and a GS center
2048 + viewport origin + (viewport extent - full raster extent)/2.
Thus 640x480 is a code-defined logical domain, not a screenshot-fit size.

`295d58 -> 292a48` copies XML Row3 to en2d translation +50/+54, with no
XML Y flip. Mode2 is global UI. `337a98` copies the matrix for rendering and
uses `338ab8` to select an orthographic UI camera in modes1/2. The sprite
producer initializes cursor X=-0.5, cursor Y=+0.5; a command with carry_cursor
false resets cursor to command position plus those biases. For each PSB
vertex it emits:

```text
sprite_x = cursor_x + signed local_x
sprite_y = cursor_y - signed local_y
```

Local PSB Y points down; the producer's intermediate Y points up. Sprite
vertex memory stride is 0x30 with UV +10/+14 and XYZ +20/+24/+28; packed
color is +2c. Local triangle data is read with the proven in-memory 0x48
stride. Scalar instructions, including EE nonzero-rd multiply sites, were
checked against original words where generic MIPS decompilation lost strides.

## Conditional logical rectangle

For identity linear matrix, global UI, zero command cursor and a unit
vertical factor, the candidate top-left logical equation is:

```text
x_screen = tx + local_x - 0.5
y_screen = 480 - ty + local_y - 0.5
```

This equation is implemented as a **conditional diagnostic**, not marked
as a proven final renderer transform. `final_logical_rect` is null throughout
the machine-readable report. `conditional_logical_rect` retains useful
geometry calculations without promoting them to final physical positions.

| Object | XML translation | Independent intermediate result / conditional logical result |
| --- | --- | --- |
| SpeedDial | 557,98 | template image0 bounds -> [492.5,318.5,620.5,446.5], before any matrix/display correction |
| SpeedNeedle | 0,0 | owner init replaces translation with 557,98; image2 zero-angle bounds -> [548.5,326.5,564.5,390.5]; current rotation UNKNOWN |
| GameRank | 22,401 | conditional anchor (21.5,78.5), final digit/font rectangle UNKNOWN |
| GameTimer | 494,430 | conditional anchor (493.5,49.5), font/owner layout UNKNOWN |
| ProgressBar | 320,55 | authored image8 cap bounds -> [319.5,409.5,351.5,441.5]; owner-generated strip extent UNKNOWN |
| Map | -65,-87 | translation unused by gaHudAiMap; direct center (74,392), clip box [29,349,119,435] |

The map has its own direct top-left logical coordinates, not the same sprite
matrix path. Treating its negative XML position as the displayed minimap
center would be incorrect.

## Aspect, video mode and screen adjustment

Orthographic bounds in `2dd510` are left=0, right=640/RasterW,
bottom=-480/RasterH * vertical_factor(`42d2c4`), top=0.
`3280d0/328168` build projection objects/matrices from these values. The
factor is not an ELF fixed constant: stores at `2f168c`, `2f252c`, `2f33c8`
use 0.5, while `2f4200` uses 1.0; the current video-mode selection has not
been connected to a captured frame. Aspect therefore cannot be replaced
with one universally valid screenshot multiplier.

`32f988` also reads PS2/ScreenPosX and PS2/ScreenPosY. Their selected values
and the resulting display offset/safe-area effect are UNKNOWN here. The
report does not claim a fixed safe-area margin or derive one by measuring
the screenshots. Original screenshot sizes are 1763x984 and 1920x1072,
which include PCSX2 presentation scaling beyond authored dimensions.

For map primitives, the final producer **is** traced: `318e10` computes
GS fixed-coordinate candidates for each expanded stroke vertex:

```text
gx = CVT.W(16 * (x/640 * RasterW + 2048 - RasterW/2))
gy = CVT.W(16 * (y/480 * RasterH + 2048 - RasterH/2))
```

CVT.W depends on FCSR. This establishes direct X right/Y down for map XY;
physical display origin and raster values still come from video state.
The packet code halves command alpha before packing, unlike a generic
RGBA32 texture payload.

## Exact outstanding evidence

The remaining ordinary-sprite chain is `337a98 -> 36a5a8 -> 3432b8`, with
projection/view supplied through `338ab8 -> 343458`, then sprite submission
`3376c0`. `36a5a8` copies current/interpolated world matrices into render
cache +50/+90, rather than evaluating the final screen equation. Full
composition and final consumption of these matrices with video state is
not closed by this bounded scalar investigation. Logical equation and
rectangle confidence remain conditional until that consumer is resolved.
This is the explicit UI2 PARTIAL blocker, not an absence of route data.

The submission calls `3432b8 -> 342b90 -> 3cb2d0`. The last function uses
COP2 vector loads, four packed COP2 operations per row and a vector store.
Generic MIPS decompilation displays opaque copFunction calls and 64-bit
loads/stores; those are not a validated model of the original VU operation
or 128-bit matrices. No conclusion interprets those placeholders as an
evaluated screen transform. Decoding that small VU matrix operation and
the subsequent sprite packet consumer is the exact next static boundary.
