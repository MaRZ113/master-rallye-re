# Geometry layouts and resource lifecycle

**CONFIRMED_BY_EXE:** `BuildFVF_00575E70` constructs layouts from descriptor flags:
XYZ or XYZRHW, optional normal, point size, diffuse/specular packed colors,
texture count and coordinate dimensions; it also supports blend-position variants.
Support in the descriptor compiler is not evidence that retail uses every layout.
`0x005781B0` derives descriptors from passes/materials; `0x00577DD0` copies XYZ,
normals, packed diffuse and selected UV arrays into compiled interleaved vertices.
Normal offsets and UV count depend on the descriptor. No stock tangent channel or
active skeletal skinning path is established.

Concrete FVF: `0x142` = XYZ|DIFFUSE|TEX1, 24-byte vertices (position at0, ARGB at12,
UV at16). Global VA `0x006E9A78` stores it; billboard particles `0x005641C0`, trails
`0x00571EC0` and shadows `0x00587DB0` use this family. Base/environment compiled
meshes have descriptor-generated values, so an exhaustive corpus FVF list remains
open. [layout JSON](data/vertex-formats.json) distinguishes observed from examples.
A resource CreateVertexBuffer FVF argument of **0** does not describe its later
SetVertexShader/FVF binding.

Debug world/screen paths use FVF0x42 (XYZ+DIFFUSE, stride16) and FVF0x62
(XYZ+PSIZE+DIFFUSE, stride20), as recorded at VA0x00589DBA/0x0058ABC5 and
0x0058A1F3/0x0058A6C9. They do not use the textured particle layout.

VB constructor `0x00584960` calls CreateVertexBuffer at `0x005849B5`; recreation
`0x00584A10` / release+recreate `0x00584AA0`. IB constructor `0x005878F0` calls
CreateIndexBuffer at `0x00587958`; recreation `0x005879B0` / `0x00587A50`.
For both: game flags bit2 selects DYNAMIC (0x200) and DEFAULT pool0, otherwise
MANAGED pool1; bit4 adds SOFTWAREPROCESSING (8); absence of bit1 adds WRITEONLY
(0x10). IB width2 selects INDEX16 (101), otherwise INDEX32 (102).

`0x00587070` suballocates shared buffers; new static backing VB allocation is at
least 0x80000 bytes, IB at least 0x20000 unless request/flags choose a dedicated
allocation. The returned slices retain buffer identity and offsets. A buffer
therefore can contain multiple semantic owners; VB identity alone is insufficient.

`LockVB_00584B50` calls resource slot11/+0x2C, uploads a requested stride*count
range, advances allocation offset, and uses NOOVERWRITE (0x1000) until wrap,
then DISCARD (0x2000). `0x00584C10` unlocks via +0x30. Buffer destructors unlock
when needed, Release and clear handles. Index lock/release follows parallel
resource methods. CPU source model arrays survive independently of GPU buffers.
Dynamic-resource ownership is cleared before Reset; exact eager/lazy rebuilding
of every compiled slice still needs tracing/observation.

## Descriptor-derived major material layouts

**CONFIRMED_BY_EXE:** pass constructor `0x005A29F0` stores stage count+4,
UV count+8 and flags+0xC. Base `0x00586560` sets (1,1,1); env `0x005860A0`
sets (2,1,3); noise `0x00585880` sets (2,2,1); water `0x00585290` sets (2,2,3).
Descriptor initialization `0x00575CC0` zeroes blend count; `0x005781B0` adds normals
for pass flag2, diffuse for flag1 AND material byte+0x20, and UVs only when material
byte+0x21 is enabled. Ordinary mapped compiled families therefore do not need
skinning just because the generic FVF builder can describe blend positions.

**STATIC_INFERENCE (derived layouts, not captured GPU bindings):** with UVs enabled,
base gives FVF0x102/0x142 stride20/24; env0x112/0x152 stride32/36;
noise0x202/0x242 stride28/32; water0x212/0x252 stride40/44. In each pair the second
adds packed diffuse. UV-disabled material branches remove TEX1/TEX2 fields.
The parsed sky records specifically derive0x102/20. Full active corpus/camera/damage
layout usage still needs logging. Linked sprite helper has a confirmed0x144/28
RHW+diffuse+UV layout but unresolved game reachability. JSON keeps those scopes apart.
