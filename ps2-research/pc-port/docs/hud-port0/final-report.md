# HUD-PORT0 result

Phase: HUD-PORT0, research and design only.
Repository: `D:\Game\Master Rallye\master-rallye-re-general`.
Branch/HEAD: master / `0bddf7c7bc5e95831f98714ff6231da05ab073ea` at HUD audit.
Frozen renderer tree: `e33386bcf682db6983380c499e4928726c758fe0`.
HUD_PS2_CONTRACT: **PARTIAL**.
HUD_PC_INTEGRATION_FEASIBILITY: **PARTIAL**.
HUD_IMPLEMENTATION: **NOT_PERFORMED**.
HUD_RUNTIME_PARITY: **NOT_PERFORMED**.

The PS2 HUD is partly shared sprite content and partly different behavior.
The rectangular minimap has a real original procedural owner and untextured
stroke renderer. It cannot be obtained by swapping the PC circular GPS image.
The first safe implementation candidate is smaller: the static tachometer
plate, retaining the PC needle, speed/gear updates and current placement.

The source difference is concrete: the PS2 plate comprises four 64x64 GXI
quadrants/eight PSB triangles; PC stores a 128x128 plate texture. Source dial
positions differ (PS2 557,98; PC 565,75), while both authored needle configs
use angles -110..70 degrees, max 8000 revs and zero needle offset. The first
pilot should retain PC geometry/layout rather than use those authored PS2
coordinates as an unproved live transform. Source font numbers differ too:
PS2 speed/timer103,gear102 versus PC502/501. Fonts and counters are separate
owners from the plate and remain original PC behavior in that proposal.

Fresh hashes/structural verification covers all four canonical PS2 inputs,
four HUD PSBs/24 HUD GXIs plus the pause bank/texture, four original PC DXT
textures and the original PC HUD0 XML. These are `CONFIRMED_BY_BYTES`.
Rabbitizer 1.16.2 with explicit R5900 validates six direct-call edges and the
15-word COP2 matrix kernel. Its operation is vector A0*Bx+A1*By+A2*Bz+A3*Bw
for each of four rows. Caller matrix roles, selected video/display factor
and final ordinary-sprite display composition remain unresolved; the report
does not claim whole-HUD independent exact-R5900 revalidation.

PC F10 evidence is useful but stops at a precise boundary. Visible frame2579
contains 268 actual forwarded UI draws returning S_OK. Hidden frame26331
contains 268 suppressed UI attempts, whose S_OK values are proxy suppression
returns. Both have 32 complete current native packet identities, but **all
widget names are unmapped**. Thus the shared UI consumer, FVF, texture or draw
ordinal cannot currently authorize a SpeedDial-specific texture replacement.

The [first pilot proposal](pilot-proposal.md) names the missing interface:
original native SpeedDial creation/owner -> bank/key -> current entity/packet
-> exact native geometry/texture group. The existing PS2 PSB parser explicitly
rejects the PC DXB record grammar even though both headers say F001/125.
Read-only semantic mapping and bounded compiled/native sprite validation are
required before an opt-in plate override. It will need no new speed/RPM feed;
the later minimap does need independently verified PC vehicle/route/progress
inputs and must not borrow PS2 output offsets.

Pause research finds PS2 `Frontend/new/Tiles/textboxalpha` versus PC
`Frontend/Tiles/textbox`, with shared authored chooser keys/tile dimensions.
No synchronized pause capture or active PS2 pause packet was obtained.
Pause-menu implementation stays excluded.

Existing HUD math tests pass 29/29 with canonical inputs. In the existing
Rabbitizer venv, PSB tests pass 24/25; one raster test errors because Pillow
is absent, not because an assertion failed. No test or environment was
modified to conceal that dependency. The parent separately reran the same
canonical suite using the already installed bundled Python/Pillow12.3.0:
25/25PASS,0skips/0errors. Research-script compilation and scoped diff-check
pass. The parent task owns serial proxy builds, source integrity report and
compact handoff packaging.

No frozen renderer, source game file, Course SDK, overlay patch or PS2 pilot
implementation was edited by this HUD subtask. The once-per-D3D-frame HUD
context cache and strict per-draw Clean View/Freecam policy remain intact.
No new HUD DLL is claimed. Source images, original binaries/XML and raw logs
remain external/private.

One next HUD recommendation: **HUD-PORT1 — SpeedDial semantic packet mapping
and source plate pilot**, after the primary native physics work and explicit
implementation authorization. The [feature matrix](feature-matrix.md) and
[source evidence](source-evidence.json) provide the independent handoff.

