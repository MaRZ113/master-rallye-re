# Shared world submission, culling and terrain/road limits

**CONFIRMED_BY_EXE:** 3D entity packet+0x50 carries visibility, model handle,
transforms and compiled-instance pointer. `0x0056BBC0` obtains the model via
`0x0054B320`; `0x0054C9D0` traverses compiled draws and invokes virtual+0x30.
`0x00576910` / `0x00562560` submit to sorted queues, then `0x00576970` emits indexed
triangles. Material/pass/texture sorting can merge semantic categories.

`0x0054C9D0` checks model bounds and camera visibility before submission. Helper
`0x004F2380` rejects by sphere/distance, camera direction and four side-plane
tests. The hierarchy walker also rejects projected bound distance beyond its
caller-supplied scalar. Renderer+0x74 supplies 300/400/500 through ViewDist.
**STATIC_INFERENCE:** increasing projection far alone cannot extend visible world
geometry: CPU/scene rejection and fog scalar remain separate limits.

| Limit | Classification | Established seam |
|---|---|---|
| perspective far | renderer-level | `0x005614A0`, twice distance scalar |
| bound/frustum rejection | scene/renderer submission | `0x0054C9D0`, `0x004F2380` |
| ViewDist class | option-driven | `0x0056D020`, sky initialization |
| terrain sectors/chunks/LOD | UNKNOWN | course structures not linked to all render calls |
| vegetation-specific distance/LOD | UNKNOWN | no distinct threshold owner established |

**CONFIRMED_BY_EXISTING_RESEARCH:** R5T render-sort/BSP distinguishes render sort
planes from tag-100 physical collision BSP. Course data and material resources are
available, but no claim that the physical BSP directly partitions D3D calls is made.

Terrain-versus-road resource/owner mapping, chunks/LOD, repetition scale and surface
association remain unresolved. Base/noise/water fixed-function families are mapped,
but assigning every road/terrain to one family from its name would be guessing.
Future wet-road/shadow/SSAO work needs object/material provenance, not a blanket
override at the common DrawIndexedPrimitive site.

Additional negative evidence prevents false owners: literal `landscape` is used
by the physics-manager constructor0x0043DD40, camera geometry intersector0x00528510
and intersection helpers0x0042E360/0x0067AC50. These consumers do not establish a
terrain DrawPrimitive owner. `Track` lookup in0x00423C70 belongs to gaBSPVerifier;
0x00403D70 constructs a development scene using Test/gordontrack/track. Neither
is silently promoted to the normal retail race terrain pass. Physical surface
metadata is separately identified in [particle prerequisites](particles.md).
