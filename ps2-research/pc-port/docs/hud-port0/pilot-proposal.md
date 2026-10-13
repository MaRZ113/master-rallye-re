# Proposed HUD-PORT1 — one PS2 tachometer plate

**Proposal only; not implemented or runtime-ready.** The first pilot should
replace only the original PC `SpeedDial` static plate using the corresponding
original PS2 image0. Preserve existing PC placement, needle, gear, speed,
race data, fonts, menus and other HUD parts. This isolates one visible source
asset difference without coupling the first HUD change to an unproved data feed.

Why this target: source ownership is authored on both platforms; the PS2 plate
and four texture quadrants are parsed/hashed; both source dial configs name the
same angle/revs/needle parameters. Minimap, complete fonts and moved groups
require substantially more semantic/state ownership.

## Required gate before changing any draw

1. Exact supported PC image and committed race HUD owner; current render thread,
   scene,device, UIepoch, racegeneration and entity lifetime.
2. Resolve one current `SpeedDial` entity from the **verified original native
   HUD creation/owner path**, including its bank/key0. Inspect original x86
   if needed; do not invent a name field in the captured packet structure.
3. Correlate that entity's current packet/content allocation with the existing
   validated native consumer and complete geometry/UV group.
4. Independently validate original PC compiled sprite geometry and the native
   stage0 texture upload/generation against the protected source DXT/DXB.
5. Reject same-texture frontend/other HUD groups, needle,key2,rank/damage,
   pause-only packets, stale allocations, unsupported builds, races and Reset.

Current blocker: all32live packet identities have owner names unmapped and PC
DXB is not supported by the existing PS2 PSB reader. Neither texture signature,
128x128size,screen position nor historical draw ordinal replaces gates2..4.
First targeted experiment is a bounded read-only widget/command mapping,
correlated to an F10 frame with HUD visible; use the existing consumer scope
instead of a second independently installed UI hook.

## Smallest effect after identity closes

Prepare a private local source-backed128x128plate from PS2 image0's four
original64x64quadrants using its PSB-local rectangles/UVs. This is offline
assembly of original image content, not an invented modern gauge. Keep it
ignored/private; package only conversion code, expected hashes and metadata.
Do not edit or distribute the original PC DXT/PS2 GXI files.

If the original PC target UV/geometry spans match that plate, use a scoped
stage0texture binding replacement around the **existing original draw**:

```text
complete current SpeedDial semantic + geometry/resource identity
 -> save original effective native stage0texture (retain COM reference)
 -> bind verified private PS2 plate
 -> original native DrawPrimitive exactly once; retain original HRESULT
 -> restore original effective native stage0texture exactly
```

Keep render states, projection, WORLD, original PC source diffuse/tint and
filtering policy unchanged in this first pilot. Multiple native calls can form
one authored sprite; prove the full target set before permitting each call.
If geometry/UV correspondence cannot safely support one assembledtexture,
stop for a precise design review; do not overlay an extra dial, skip all UI,
replace every matchingtexture or silently create a general HUD renderer.

Proposed future selector:0Stock /1verifiedPS2SpeedDialPlate, diagnostics0OFF.
These are design values, **not supported INI keys today**. Missing/bad private
asset,unknown version,ambiguouswidget,current reset/scene/owner failure->Stock.
Respect H/Freecam: when native HUD suppression would skip the target, do not
draw the replacement. Native-state work belongs solely to the staged proxy;
frozen renderer sources remain untouched. Current indexed foliage
`DrawSnapshot` is not a UI widget snapshot, so HUD-specific seam changes must
be reviewed and captured in exact staged integration patches.

## Focused verification for that future implementation

- Config0/missing/invalid remains Stock; no asset upload or additional HUD work.
- Exact widget admitted; shared texture/ordinal/callsite and stale packet denied.
- Original target draw exactly once; its HRESULT preserved on native failure.
- Native texture restored after success/partial failure; no logical state change.
- Reference ownership stable at creation,Reset,device loss,course restart/exit.
- Existing H/Freecam pause/menu behavior and once-frame HUD cache preserved.
- Baseline remains byte-exact; staged generator/patch checks and proxy exports pass.
- Cold menus,HUD visible/hidden,paused/unpaused,Freecam,replay and frontend negatives
  tested; bounded single F10 captures, no repeated per-frame identity logs.

Human comparison: same car/course/lens/settings, normal gameplay HUD visible;
capture Stock then plate-only. Assess plate shape/color/alpha edges separately
from the unchanged needle/counter/fonts/anchors. No PS2 pixel-parity claim.
Minimap and complete layout are later work with separate verified data feeds.

