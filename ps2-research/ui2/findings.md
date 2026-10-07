# PS2-UI2: HUD runtime and dynamic minimap

**Status: PARTIAL.** The owner factory, entity/visual representation, dynamic
rank selection, complete map data flow, map transform, player/opponents and
untextured PS2 map producer are recovered for the exact canonical ELF.
Actual PS2 course data now reconstructs deterministic map centerlines offline.
The final ordinary PSB sprite rectangle remains conditional: composition of
the sprite projection, video-mode vertical factor and GS display offset is
not yet a fully validated screen equation. This fails completion gates 3/4;
the blocker is narrower than the original unknown course source.

This is static reverse engineering and offline verification. Existing PCSX2
screenshots provide correlation, not a fresh runtime test of this ELF hash.
No PC HUD/rendering code changed.

## Explicit answers

| Question | Answer | Grade / boundary |
| --- | --- | --- |
| Q1: owner resolution | Name interning -> registered AI prototype ID -> lookup `1fc500` -> virtual clone `+14` via `1fc4c0` -> configure `+24` -> attach/initialize `+34` via `21e620`. `295d58` reads version4 XML; `292a48` hatches it. | CONFIRMED_BY_ELF |
| Q2: common representation | `0x7c` entity with four AI pointers at `+4..+10`, `en2d* +4c`, `en3d* +50`; en2d is `0x90` with matrix at `+20`, commands at `+4`, mode `+64`, flags `+78`, render cache `+80`. Parent relationship UNKNOWN. | CONFIRMED_BY_ELF |
| Q3: coordinate system | Code uses logical 640x480. PSB producer emits X=cursorX+localX, Y=cursorY-localY, initial cursor (-0.5,+0.5); XML translation flows to en2d +50/+54. Authored bottom-origin / top-left screen equation is conditional pending matrix/display composition. | dimensions/bias CONFIRMED_BY_ELF; exact final rectangle UNKNOWN |
| Q4: bank/image choice | XML model -> interned command bank -> PSB resource/cache -> u16 key lookup -> mapped image -> 12-byte image-vector object -> 72-byte triangles. A key is not necessarily an image index. Rank switches bank/key command streams on the same entity. | CONFIRMED_BY_BOTH |
| Q5: dynamic map | Yes. `147038` creates route/split/finish endpoint buffers and submits primitives, independently of the Map entity's Null model and authored translation. | CONFIRMED_BY_ELF |
| Q6: source | Actual named `MarkerLists/RaceLine` loaded by `1ff6a0/1ff7a8`, retrieved by marker manager and ID `40e818` in `147038`. Actual PS2 `RACETEST/ITALYS1.XML` contains 293 route records. | CONFIRMED_BY_BOTH |
| Q7: world -> map | Player-centered rotating XZ map; float scale `40e5e8=0.4f`; route window last marker +/-32; rotated local segments clipped against +/-45,+/-43 then add center (74,392) for HUD0. No course-bounds fit. | CONFIRMED_BY_ELF; XML settings CONFIRMED_BY_BYTES |
| Q8: markers | Vehicle-output wrapper +8 -> data position +f0/+f8. Player chevron stays centered; opponents use identical world transform and clipped X strokes. Iterate NumCars excluding PlayerID. Colors from Race/CarN/Colour. | CONFIRMED_BY_ELF; semantic labels of heading input vectors STATIC_INFERENCE |
| Q9: primitive | Map -> concrete renderer slots +ac/+bc/+c4 -> command/Vec2 vectors -> flush `32fce0` -> `318e10` -> packet tag `318bd8`. Stroked untextured triangle strips, not PSB route sprites. | CONFIRMED_BY_ELF; packet bits checked against primary GS register definitions |
| Q10: MAP128STRIPED | **NO in this traced race-map path.** Packet PRIM has TME=0 and Map never selects a texture or PSB bank here. Other consumers of the asset remain UNKNOWN. | CONFIRMED_BY_ELF, bounded exclusion |

The prompt's possible fixed overview is disproved by player-position subtraction
and heading rotation. UI1's candidate init/update labels were reversed:
`1461f8` is initialization; `147038` is per-frame update/draw. UI1's PSB/GXI
parsers and retained evidence are unchanged; this document supersedes those
two speculative function labels only.

## Completion gates

| Gate | Result |
| --- | --- |
| 1 owner factory | PASS |
| 2 common entity / model fields | PASS, parent intentionally UNKNOWN |
| 3 exact final logical sprite transform | PARTIAL: dimensions, local bias and position flow proven; final composition unresolved |
| 4 independently proven final rectangles | PARTIAL: multiple conditional calculations and screenshot area correlation; no fitted coordinates |
| 5 gaHudAiMap layout/update | PASS |
| 6 actual course feed | PASS |
| 7 route representation | PASS |
| 8 world/route map transform | PASS for supplied recovered heading state |
| 9 player marker | PASS |
| 10 opponent markers | PASS |
| 11 primitive producer | PASS |
| 12 MAP128 relationship | PASS, excluded from traced minimap |
| 13 offline reconstruction | PASS for route/marker centerlines; exact GS raster coverage excluded |
| 14 PackFS/UI1 regression | PASS: 51 existing tests preserved |
| 15 no PC implementation | PASS |

See [runtime](hud-runtime.md), [coordinates](hud-coordinate-system.md),
[minimap](minimap.md), [ELF method](elf-hud-functions.md),
[validation](validation.md), and [remaining work](next.md).

Machine-readable records: `hud-runtime-map.json`,
`hud-runtime-structures.json`, `elf-hud-functions.json`, `minimap-format.json`.
Raw exports, route JSON, SVG, XML and logs remain under ignored `data/ui2`.
