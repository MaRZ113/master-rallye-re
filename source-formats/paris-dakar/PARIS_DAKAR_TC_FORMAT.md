# Paris-Dakar TC / Gex / PC TIM — qualified research revision1

29 October2026. Independent source-only reader in
`src/master_rallye/source_adapters/paris_dakar_formats.py`. This is a narrow
verified Windows build, not an extension-based universal TC claim.

## Evidence and original build

`dakar.exe`:1925177 bytes, SHA256
`94008b8708ddaf918397b56c2e194086ed9b088a7ec0e7e185effdebd51d1482`.
PE32 x86. Original `.data` file18b000 maps to VA58b000; the relevant data
addresses therefore map as file offset=VA-400000. Code mapping is similarly
verified in `.text`. REA/Ghidra12.1.4 and independent GNU objdump instruction
reads agree on these operations. Pseudocode is a static derived representation,
not original source and not a record of executing the game.

| Original function | Verified operation | REA evidence |
|---|---|---|
|00442210|Read80-byte header; repeating XOR key pointer005a1ef4; validate DEAFBEEF; table404-byte stride and key005a1efc|`ev_799337e...66cb`|
|00442680|Read member offset+8/length+12; clear payload when header is DEAFBEEF|`ev_440f93e...9765`|
|00491cf0|Gex/Iex dispatch; texture40/material84 tables; chained batches; byte indices/3; reorder32-byte source vertices to D3D FVF0x112|`ev_180a5ad...83c2`|
|004c7af0|PC TIM palette at8, image header1032, source alpha flag8, RGBA-to-D3D channel packing|`ev_fc06b1d...417f`|
|004c6cb0|Material name suffix:8 hexadecimal flag digits +3 type digits before underscore|`ev_bca6f17...157b`|
|004f7ed3|RallyCar assembly; four wheels, shared FrontWheel when RearWheel=NULL; alternating side argument|`ev_b1a7819...5c27`|
|0051a160|Side argument0/1 produces Y rotation0/pi|`ev_75f3f82...791b`|
|00519d30|Read suspension fields; game options alter attachment and suspension limits|`ev_13084f5...87ed6`|

Complete IDs, exact assembly, source digests and coverage limitations are retained
privately in `vehicles_scratch/paris-dakar/rea-evidence.json` and the matching
REA snapshot. Original code bytes are not redistributed in source archives.
The two large constructor dossiers exceeded MCP response size; retained
pseudocode pages were inspected instead of treating truncated output as complete.
Their high-pcode value-flow truncation does not qualify unexamined physics paths.

## TC container

All offsets below are zero based, little endian. There is no signature inferred
from `.tc` alone. `executable_keys()` requires the complete original EXE hash
and reads the two NUL-terminated strings through verified pointer mappings.
No proprietary binary or key-bearing EXE is shipped with the utility.

| Location | Field |
|---|---|
|File0..79|Repeating-XOR header; decoded u32+0=`0xDEAFBEEF`|
|Header+68|u32 resource count|
|Header+72|u32 absolute directory offset|
|Directory|Repeating-XOR records, each404 bytes; count*404 ends exactly at EOF|
|Record+0/+4|Raw type and timestamp-like u32; preserved, not authorization|
|Record+8/+12|Absolute payload offset, exact stored length|
|Record+20|NUL-terminated resource name in retained record; safe flat identifiers|
|Payloads|2048-aligned starts, disjoint spans, exact original hashes|

Remaining header/record words include opaque state/address-looking values.
They are preserved privately and never interpreted as pointers to dereference.
Original complete TC snapshots also preserve inter-member padding.

Selected Pajeros:65 records each, directory0x3f8000; Nissan Patrol72 records.
The decoded signature implies open payloads in the original loader. These three
files require **no decompression**. Other signatures, including the alternate
DEAFCEDE branch, fail closed; they are not silently decoded with guessed XOR.

## Gex mesh resource

`Gex#MainBody.x` is an internal resource header, **not a DirectX xof file**.
The original loader checks Gex#/Iex# codes directly; it does not send these
members to the DirectX `.x` parser. Current reader supports Gex only.

| Resource offset | Field |
|---|---|
|0..67|`Gex#` + original NUL-terminated object/export name|
|68..91|Six float32 original bounds|
|92|u32 triangle count, checked against complete batch reconstruction|
|96|Opaque retained u32|
|100/104|u32 texture/material counts|
|108|Original vertex-count hint; not equal to repeated batched vertex count|
|112|Texture references,40-byte records ending `.3df`|
|After textures|84-byte material records|
|Material+18|u16 texture slot;32000 means original untextured material|
|Material+20..79|NUL material name; full84 bytes retained|
|After materials|First geometry batch|

Batch header128 bytes: u32+0 is next-batch relative displacement, or zero for
last batch; u32+32 material slot; +36 index count; +40 vertex count. Indices
are bytes at+64, at most48, divisible by3; **each stored index is divided by3**
before indexing its own batch. No signed-byte or triangle-strip guess is used.
Vertices start+128; next displacement must equal128+32*vertex_count. Last batch
must consume the resource exactly. Geometry/material/UV references are bounded.

Each vertex is8 float32 values:
`position.x, position.y, position.z, normal.z, u, v, normal.x, normal.y`.
The original CPU loader's field moves establish this unusual layout; independent
unit-length and face/normal checks corroborate it. Triangle order and original
floating values remain unchanged. UVS grouping does not weld batch duplicates.

RED:all1956 retained triangles have positive geometric-normal dot; Silver:
all2002. Patrol:2066 positive,8 negative,0 degenerate. Those eight original
normal/winding disagreements are a **WARN**, retained without an automatic
normal flip or polygon deletion. An unrelated valid resource thus exercises
the reader beyond the two Pajeros.

## PC TIM-like image resources

These are **not standard PS1 TIM files**, despite magic16 and original loader
terminology. Palette is directly256 RGBA32 entries at8; no PS1 CLUT block.

| Offset | Field |
|---|---|
|0|u32 magic16|
|4|Qualified raw flags0x40001 or0x40009|
|8..1031|1024-byte original RGBA palette|
|1032|u32 base image block size,12+width*height|
|1036|Original XY word, retained|
|1040/1042|u16 width/height|
|1044|Indexed8 base plane, followed by three smaller mip planes|

All four mip planes exactly exhaust each selected texture. High word4 and
four planes are observations; unknown flag semantics are not generalized.
Source indices, palette bytes, original alpha, all mip ranges/hashes and full
resource bytes remain available. Source flag8 is the loader's alpha-bearing
texture branch. Neutral preview uses its exact RGBA palette, without invented
glass opacity or MR reflection/damage transformations. Blend ordering,
specular/environment lookup, animated damage/livery transitions and original
renderer parity remain unqualified.

## Assembly and coordinates

`Description` is exact ASCII `RallyCar 1.00`, with body/wheel resource names,
four suspension records, detachable object names and positions, collision
points/spheres, texture variants and other physics values. Raw lines and byte
offsets are retained. Component offsets are member relative; add the TC member
offset for absolute file provenance.

Body positions remain in body space. Separate Bonnet, BackDoorR and bumpers
use their original Description translations. Shadow meshes are retained as
separate resources and excluded from the ordinary neutral body pass. One
WheelFL resource is instanced four times; right-side instances receive original
constructor Y rotation pi. No donor-MR wheel substitution occurs.

X signs and front/rear Z separation plus upright body establish X lateral,
Y up, +Z forward for these files. Normalization is explicit mirrorZ with unit
scale; the shared preview applies inverse-transpose normals and determinant
winding reversal. Physical metres are plausible but independently unqualified.
No dimension fitting or hidden scale factor is applied.

**Attach Point is a source datum, not a proven gravity-settled hub.** Original
Radius, Rest Position, Upper/Lower Limit and option-dependent loader behavior
are preserved separately. Rest Position is not blindly subtracted from Y.
Neutral zero-steer/spin assembly is the documented inspection pose.
