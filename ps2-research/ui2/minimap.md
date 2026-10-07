# gaHudAiMap: procedural player-centered race map

## Object and lifecycle

Allocation at the HUD prototype registry proves size **0x8c**. Constructor
`146118` writes vtable `44cb00`; configuration is `146960`, initializer
`1461f8`, per-frame draw `147038`. The generic initializer call at `21e620`
proves the slot names, correcting UI1's speculative init/update reversal.
Every field is enumerated in `hud-runtime-structures.json` with accessors.

| Offset | Meaning |
| --- | --- |
| +00/+04/+08 | owner base header, interned type ID, vtable |
| +0c/+10 | HUD number / player ID |
| +14 | FinishArea/BestMarker |
| +18/+24/+30 | split BestMarkers vector / CarN name IDs vector / float RGBA color vector |
| +3c/+48/+54/+60 | route segments / split segments / polyline scratch / finish segments, Vec2 vector headers |
| +6c/+70 | LastMarker broker key / NumCars |
| +74/+78 | previous/current map heading Z / X |
| +7c/+80/+84/+88 | clip height / width / center X / center Y |

XML HUD0 custom values give W=90,H=86,C=(74,392). The Map visual has model
Null, visible false and translation (-65,-87), but these are not inputs to
its procedural draw. Owner config/fields drive the minimap. Initialization
uses HUD player ID and visibility; on invisible HUD it queues entity removal.
Shared globals hold half width (`40e5e0`), half height (`40e5e4`), scale
(`40e5e8=0.4f`) and frame counter (`40e5ec`). Width/height zero fall back to
50 half extents; zero centers fall back to 50. Split-screen independence is
not established because the clip/counter globals are shared.

Each update obtains the named RaceLine list. A missing list returns early.
Draw begins after the shared counter exceeds 15. Scratch/segment vector ends
are reset before generating the new frame; buffer capacity is reused.

## Course feed and representation

`1ff618` reads MarkerLists; `1ff6a0` interns each list's Name, creates it in
the marker manager and visits Marker children in **document order**.
`1ff7a8` reads Marker Type/Pos/Dir, builds the basis/position and appends an
80-byte record. Position is XYZ float32 at +40/+44/+48, W=1 at +4c; the
rest contains a basis and type ID. `147038` retrieves the list through
`1fde60 -> 1fdba8` with RaceLine identifier `40e818`, computes count from
begin/end divided by 80 and reads X/Z at +40/+48. This is actual pointer flow,
not a choice based on the name RaceLine.

There is no fixed-point/pre-normalized route, graph lookup or spline evaluation
in this path. The map draws consecutive world-space records; Marker No is
not a sort key in the ELF reader. The offline XML reader requires canonical
No=0..N-1 as an additional fail-closed input restriction and never reorders.
Null marker type does not introduce a segment break. Visible breaks arise
from clipping/rejected segments and exact endpoint continuity comparisons.

One real PS2 resource was extracted deterministically through PackFS:

```text
\TNG\DATASCENE\RACETEST\ITALYS1.XML
TNG.000 offset: 1224881262
stored size: 40712
decoded size: 353158
stored SHA256: e04042a11cd2658894e33a69de9757685c1614f7f3cdc18abfc02504a6e39f5f
decoded SHA256: 56603a9b51f509032a3f15953f161eeaa25044b2c00b5988a73e0c2cbc9c9a92
RaceLine records: 293
```

World bounds are dumped for inspection, not used to normalize the map.
Original route coordinates/XML and transformed coordinates stay ignored.
FinishArea/BestMarker and split BestMarkers are runtime broker values,
not literal XML fields in this sample. The current upstream nearest-marker
calculation is outside this map consumer reconstruction.

## Recovered math

Vehicle source is `CarN` + `gaVehicleOutputData`, queried with `1e3820`;
the returned wrapper has data pointer +8. Player world X/Z are data +f0/+f8.
Map heading starts with data +e0/+e4/+e8 plus 0.1 times +18/+1c/+20, is
normalized, flattened in Y, normalized in XZ and negated. Forward/velocity
are useful working names for these two vectors, but their producer semantics
remain STATIC_INFERENCE; the offsets/math are confirmed by the consumer.

The update compares candidate heading Z with owner +74 and candidate X
with +78. If Z difference exceeds 0.045, candidate Z moves toward **zero**
by 0.045; otherwise, if X difference exceeds 0.045, candidate X moves toward
zero by 0.045. It normalizes the pair again and stores it. This is not a
conventional interpolation toward the previous heading. The constructor
does not prove an initial value for +74/+78; the first-frame seed is UNKNOWN.
`hudruntime.py` takes the resulting unit state explicitly and does not invent
the initial heading or silently approximate its evolution.

For player P=(Px,Pz), world point W, stored H=(Hx,Hz), S=0.4f:

```text
dx=Wx-Px; dz=Wz-Pz
local_x = S * (Hz*dx - Hx*dz)
local_y = S * (Hx*dx + Hz*dz)
```

Segment indices are max(LastMarker-32,0) <= i <
min(LastMarker+32,FinishArea/BestMarker); read points i/i+1. LastMarker <=0
or >=count becomes 0. Offline tooling rejects an impossible finish index
rather than permitting an out-of-range second endpoint. Y/elevation does
not affect the route geometry. No overall bounding-box fit occurs.

`1469f0` clips each segment against +/-halfW,+/-halfH using outcodes
top=1,bottom=2,right=4,left=8, shared-side rejection and intersections, then
adds C. `146d80` consumes endpoint pairs and submits open polylines. Its
comparison is unusual: the odd endpoint is compared with the cached even
point, initially the first endpoint, rather than the next segment's start.
Normal nonzero segments therefore flush **separately**. This was checked
against stack loads/comparisons at `146eec..146f10`, not assumed from a
conventional polyline-merging algorithm. The final iteration also reads
one point past the logical endpoint-vector end; offline tooling avoids
that read and does not claim the spare-capacity value is initialized.
The already-emitted ordinary nondegenerate pair is independent of it.
Segment clipping creates visual discontinuities. The dumper keeps runtime
queue batches separate from continuous strips used only by the debug SVG.

## Markers and primitive drawing

The player stays centered, drawing an open chevron with points
C+(-5,+5), C+(0,-5), C+(+5,+5). Its shadow is translated (+3,+3).
Opponents iterate Car0..NumCars-1 excluding PlayerID. Position uses the same
output fields/rotation/scale; each foreground X is two clipped diagonals
with +/-4 offsets. Shadow diagonals span -2..+6, and both layers use width4.
Colors come from Race/CarN/Colour (default white); foreground RGB intensity
250, shadow 40, submitted alpha250. Opponent orientation is unused.

Route shadow width6/RGB intensity127 and foreground width3/intensity250
use color (0.2,0.6,0.1). Split and finish crossbars are generated from route
segment midpoints/perpendiculars and BestMarker indices; they use factors
2.5 and 3 respectively. The offline preview omits crossbars instead of
claiming an unverified full HUD reproduction. Background and border are
also procedural strokes: the background is a dark wide line, the border
uses the closed polygon queue. No texture mask is required.

Concrete renderer vtable `485a00` maps color +9c to `32edf8`, width +a4 to
`32ee28`, line +ac to `32ee40`, open polyline +bc to `32f498`, closed polygon
+c4 to `32f710`. Renderer +468 holds the primitive object; commands are
24 bytes and vertices are Vec2 float32 (8 bytes). Open polylines permit at
most 64 points, closed polygons 63. Queues snapshot width/packed color/type,
vertex start/count. Width is stored as half-width.

Flush `32fce0` calls **318e10**. It expands each stroke to opposing vertex
pairs along the perpendicular; joins use normalized sums of adjacent
perpendiculars. Closed strokes repeat the first point. Degenerate exact
joins and GS floating-point edge cases are not emulated offline. Each
expanded vertex is scaled by RasterW/640 and RasterH/480, offset around
2048 and converted to 1/16-pixel GS coordinates. Command alpha is shifted
right one before RGBAQ packing (250 ->125).

Packet tag helper `318bd8` writes `0x10a6400000000000`, whose PRIM bits
are **0x14c: type4 triangle strip, TME=0, ABE=1**. Register definitions and
triangle-strip encoding were checked against the primary
[PCSX2 GS register definitions](https://raw.githubusercontent.com/PCSX2/pcsx2/master/pcsx2/GS/GSRegs.h).
This byte/code evidence rules out MAP128STRIPED in this traced route/frame/
marker path. Other uses of that asset elsewhere are UNKNOWN.

## Reproduce offline centerlines

```powershell
python ps2-research/tools/hudruntime.py --inputs 'D:\Game\Master Rallye PS2' `
  --player -2024.8299560546875 -702.0599975585938 --heading 0 -1 `
  --last 32 --finish 292 `
  --output ps2-research/data/ui2/new-frame.json `
  --svg ps2-research/data/ui2/new-frame.svg
```

This sample uses actual route point32 as the diagnostic player position,
explicit unit heading (0,-1), LastMarker32 and explicit FinishMarker292.
It is **not** a recovered player state or reconstruction of either screenshot.
All 293 points and their transformed XY are emitted; the runtime window
contains indices0..63 and produces **16 clipped segments**, sixteen
two-point queue batches and one continuous debug strip in this state.
The preview contains actual clipped route points and the generated player
chevron, with no manual screenshot tracing.

`--xml` reads a decoded local RaceTest XML. `--memory --offset --count`
reads the 80-byte array at an explicit file offset. Alternatively use
`--memory --vector-offset --base-address` to resolve a begin/end/capacity
header within one contiguous memory image. No live reads or dump scanning.
Outputs must be new paths under ignored `ps2-research/data`; originals and
existing outputs cannot be overwritten. Invalid counts, offsets, pointer
order/stride, missing route and non-finite geometry fail closed.
Arithmetic is Python precision with float32 input/scale; exact EE float
rounding, stroke joins and GS coverage are not claimed reproduced.
