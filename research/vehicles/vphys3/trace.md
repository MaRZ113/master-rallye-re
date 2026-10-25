# V-PHYS3: why the V-PHYS2 ride reference was not applied

## Qualified cause

Static original x86 bytes and the SDK's actual record construction expose a
namespace mismatch. The V-PHYS2 adapter compared `Vehicles/LancerEvo4` against a
**raw registry name** `LancerEvo4` at the publication callsite. Its family guard
therefore bypassed the ride datum. This explains why the fitment candidate at
menu 0/0 still showed the high body: physical RideHeight remained 0 rather than
receiving the intended -0.15 m. It is not evidence that the intended reference
must be made more negative.

Original target: retail MRallye.exe SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
No original file was changed during this audit.

## Exact chain

1. `tools/build_vehicle_multislot_i0.py` emits `id27_internal_name` from
   `id27_record.internal_name`, which is `LancerEvo4`. The profile's
   `physics_family=Vehicles/LancerEvo4` is metadata, not that literal.
2. `patch_vehicle_registry_id26._emit_record_initializer` constructs a temporary
   string from that raw literal and passes it to native `0045A0B0`.
3. `0045A0D5` reads the supplied name; `0045A0F9` takes record+0x20 and
   `0045A10A` copies the name through `004D1990`. The registry has a four-byte
   header, so record+0x20 is registry+0x24+CarID*0x34.
4. `0044ED50` obtains exactly that registry field and copies it into the local
   string whose data pointer is caller ESP+0x18 at `0044F334`. The original
   LEA/PUSH/CALL at `0044F334..0044F33E` does not add a path prefix.
5. The configuration **reader** `00493E30` calls `00493770` first, at `00493E58`.
   `00493770` creates a new local string starting with literal `Vehicles/`
   (original VA `006B1968`), then appends the raw supplied name. Thus the named
   XML path is created in the reader, not retained in the caller's raw string.
6. `004938C0` publishes the supplied parameter block to `Vehicles/CarN`. The
   front suspension writer reads parameter+0x110 at `00497643`; rear reads
   parameter+0x17C at `004989B3`. These writes carry the supplied float directly
   to the configuration writer; no height clamp is present there.

The V-PHYS2 isolated reference test populated caller ESP+0x18 with the invented
prefixed string. It tested wrapper ABI and arithmetic, but did not qualify the
real caller's family spelling. Its successful result cannot establish real
participant publication.

## Smallest robust correction

Keep menu base0 and the already selected -0.15 m datum. Match the exact raw
family component including NUL at the publisher callsite. Leave `Vehicles/`
only in XML/resource-path contexts. Extend the native test through the actual
registry initializer and named-reader prefix builder, retaining negative cases
for prefixed input, stock/other family and longer shared-prefix names. Confirm
publication, wheel initialization and wheel transform from one continuous
native input chain where practical. No mesh, individual wheel, spring or
collision adjustment is justified to compensate for the namespace error.

## Other inspected relationships

`004451B0` transforms wheel attachment by
`body_world_position + body_rotation*(wheel_attachment - body_CG)`:
`004451E9` selects wheel+0x30, `0040DE90` subtracts body+0x94, `004EC170` applies
body+0xBC rotation and `0040E880` adds body+0xA0 position. This does not justify
a new visual offset. A wheel attachment alone is not a settled race wheel;
body origin and the dynamic jounce transform must also be accounted for.

Fitment260 and Handling260 have the same intended reference +0.15 m hub Y,
but different mass/rates/travel. Existing local upright force checks show
zero symmetric jounce at the native preload for both; fitment's corner sprung
masses are about268.86/221.14 kg and rates34500/33500 N/m. Those differences do
not explain an exact family guard that never activates. Whole-race contact,
terrain, pitch and landing remain human/runtime validation boundaries.

Private compact original-instruction evidence and both prior force summaries:
`.research-output/vehicles/vphys3/evidence/fitment-raw-family-chain.json`.
Original raw provider exports remain private in scratch/phys3 and the prior
vphys1/vphys2 evidence directories. Decompiled output is supporting analysis,
not original source or gameplay confirmation.
