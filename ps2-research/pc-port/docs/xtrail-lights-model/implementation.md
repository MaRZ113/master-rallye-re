# Source-backed headlight pilot

PC Xtrail CAR source record10 (22vertices/18faces) matches PS2 CAR root.19,
byte175376, mode20 carglass. Full unsigned geometry SHA256, every position hash,
original PC normal/UV/color and current mirror coverage/generation/revision are
required. No historical draw ordinal, numeric VB/IB or texture-only authority.
The native snapshot must also prove the current race certificate, world/texture
state agreement, expected FVF152/stride36 and normal-coordinate stage context.

Private resource preparation uses existing PackFS/PSM/DX readers. The asset pins
original PC and PS2 source-derived attributes and both source GXIs by one exact
SHA256. It has no world/model XYZ mesh export. It is retained locally and not
committed or packaged. Missing/invalid asset/config/build/capability fails Stock.
No disk reads in Stock; enabled reads once at construction. Managed textures
upload lazily at the first admitted cover, never in menus; bounded16-entry
identity cache avoids repeated geometry hashing. Revisions/reset invalidate it.

The admitted cover suppresses its original opaque draw and emits exactly two
native UP submissions of18faces, matching PS2 primary/secondary pass structure.
Primary: original PS2 UV/normal/color, WINDSCREEN32-TGA16x16, stored alpha unchanged,
MODULATE texture/diffuse, SRCALPHA/INVSRCALPHA, alpha test OFF, depth write OFF.
Highlight: WINDSCREEN-REFLECT32x32 RGB floor(*96/128), ONE/ONE, static camera-normal
mapping using the current verified environment matrix; fog OFF on this pass.
This uses static images, not the Mode4 framebuffer source. Preserve PC depth
function/enable and cull state. Texture0 sampler settings are inherited; no claim
of original GS filtering/mip/CLAMP parity. D3D8 alpha/255 differs from GS alpha/128.

Capture15 scalar states, texture0, texture0 matrix, stream0/stride and indices/base.
Attempt bits are set before each native setter, including failed calls. Restore
all altered native values/references in reverse order, report pending repairs,
block until repair/Reset on restoration failure. UP stream/IB side effects are
restored. No game-facing logical state writes. Native replacement draw HRESULT is
returned; the suppressed original draw has no HRESULT to preserve. Once primary
is submitted, never replay opaque geometry on highlight failure. Real Reset
releases/recreates textures; internal reset-echo does not invalidate this pilot.

Confirmed decal and body algorithms remain unchanged. Wheels are deferred until
model port. No tail-light/glow implementation and no COMPLETE suppression.
