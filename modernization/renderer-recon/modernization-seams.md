# Future modernization seams and prerequisites

All difficulty ratings are STATIC_INFERENCE for future work, conditional on stock
parity and an appropriate backend. Addresses identify observed seams, not approved
patch locations. No listed feature was implemented.

| Feature | Difficulty | Why / seam |
|---|---|---|
| per-pixel directional sun | MODERATE | Normals must survive layout path; shader/backend work and light source unresolved; 0x00577DD0, 0x005867A0 |
| ambient / hemisphere lighting | MODERATE | Replace unlit/baked diffuse carefully without double lighting; 0x005867A0 |
| vehicle specular | MODERATE | Vehicle identity and normal-bearing layouts need runtime confirmation; 0x00586150 |
| vehicle environment reflection | MODERATE | Known stage1 normal mapping seam, no live cubemap capture established; 0x00586150, 0x00561A40 |
| gamma correction | MODERATE | Scene/UI boundary and texture color spaces must be identified; 0x0056CD80 |
| anisotropic filtering | EASY | Intercept known TSS filtering; caps/visual parity still required; 0x0053F930 |
| anti-aliasing | MODERATE | Creation MSAA/depth matching and alpha-test edges; 0x0055AB90, 0x0055A030 |
| extended draw distance | MODERATE | CPU bound rejection and fog scalar, not projection alone; 0x004F2380, 0x0054C9D0, 0x0056D020 |
| modern fog | MODERATE | Known fog/view scalar seam; reliable depth access depends on backend; 0x0056D020 |
| shadow maps | HARD | Shared buffers/damage/transparency classification, replay and receiver normals; 0x00576970, 0x00583B90 |
| SSAO | HARD | Depth sampling and scene/UI separation absent in stock observed path; 0x0056B900, 0x0056CD80 |
| tone mapping | MODERATE | Need offscreen scene target and correct UI composition; 0x0056CD80 |
| bloom | MODERATE | Need offscreen target; original values are LDR; 0x0056CD80 |
| skybox switching | MODERATE | Cloud resource seam exists; selection is scene initialization, live ownership not proved; 0x004B1180 |
| time-of-day presets | MODERATE | Sky/fog control known; sun/ambient native source unresolved; 0x004B1180, 0x0056D020 |
| rain particles | MODERATE | Billboard path exists; spawn, lifetime, orientation and pause timing need mapping; 0x005641C0 |
| wet materials | HARD | Road/dirt/mud/snow identity not connected to GPU material families; 0x00580360 |
| wheel spray | MODERATE | Existing water_drive particle inputs; wetness/surface trigger needs map; 0x005641C0 |
| night lighting | HARD | No known runtime light owner; night content/exposure missing; 0x005867A0 |
| headlights | HARD | New light projection/shadow path and vehicle association required; 0x0056BBC0 |
| selective HD texture replacement | MODERATE | Loose/cached upload seam known; identity, alpha and mip compatibility needed; 0x005587E0, 0x0064D530 |
| optional normal maps | HARD | No tangent stream established; requires UV-based generation and material identity; 0x00577DD0 |
| freecam | MODERATE | Final view seam known; scene culling uses original camera and pause-independent update unknown; 0x005614A0, 0x004F2380 |
| FOV control | EASY | Known angle helper and final projection; preserve baseline linear aspect rule; 0x004F2350, 0x005614A0 |
| photo mode | HARD | Freecam plus culling, HUD suppression, pause control, capture and optional depth effects; 0x005614A0, 0x0056D110 |
| exposure / DOF | BLOCKED / UNKNOWN | No stock HDR exposure or sampled depth established; backend and capture boundary prerequisite; 0x0056CD80 |

Freecam/photo mode: final view/projection override005614A0 permits FOV/roll
control, but CPU culling004F2380 and sky position must agree with the new camera.
Pause-independent input/update and capture are not established. Suppress actual
HUD/frontend packet boundaries, not all ortho/debug/video indiscriminately. Sky
selection is initialization-driven; safe live ownership is unknown. Exposure/DOF
needs a new scene target/depth policy. No proven developer freecam was discovered.

Rain: billboard/trail geometry exists, but a weather emitter, lifetime/orientation,
density and pause timing must be supplied or recovered. Wheel spray has water/dirt
particle leads. Contact Surface road/dirt/mud/snow identities are not connected to
GPU material categories, blocking a reliable wetness policy.

Time of day: cloud model/palette004B1180 plus renderer fog0056D020 are confirmed.
A coordinated preset can plausibly choose sky/fog; native sun/ambient source and
HDR exposure are unresolved. Source vertex diffuse may already carry baked lighting.
A complete sun+ambient+fog+exposure preset therefore requires additional ownership,
not just changing CloudNumber. Track/replay selection producers remain to be mapped.
