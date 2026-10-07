# PS2-UI2 result

PS2-UI2 STATUS: **PARTIAL**. Dynamic minimap source/transform/markers/producer
and data-only reconstruction are recovered. Exact final PSB sprite matrix,
video-mode factor and display-offset composition remain UNKNOWN; completion
gates 3/4 are open. See [findings](findings.md) for all fifteen gates and Q1-Q10.

| Requested field | Result |
| --- | --- |
| Repository/worktree | D:\Game\Master Rallye\master-rallye-re-general |
| Branch | master |
| Starting HEAD | f138de2364ea0457a220413507cfafa04704b84e |
| UI1 commit | ff8049b8e7f04406298f5938ecbb7eefa73eeeb5, committed before UI2 |
| Preflight working tree | clean |
| Registry/factory | 15b190 /1fc760 /1fc500 /1fc4c0 |
| XML owner resolution | intern name ID, lookup prototype, virtual clone +14/config +24, attach/init +34 |
| Base HUD entity | 0x7c entity with four owner pointers +4..+10 and en2d +4c; 0x90 visual with matrix/commands/flags/cache |
| Logical width/height | 640 /480, ELF constants |
| Origin/X/Y | map direct top-left, X right/Y down; ordinary sprite local Y inverted before projection; final screen equation conditional |
| Conditional sprite equation | x=tx+localX-0.5; y=480-ty+localY-0.5, identity global UI/unit vertical factor |
| Scale/aspect/safe area | viewport ratios proved; actual sprite video/display composition UNKNOWN |
| Proof objects | SpeedDial, initialized SpeedNeedle, GameRank/GameTimer anchors, ProgressBar, direct Map center; final rectangles not promoted |
| XML model | authored bank name copied to command bank ID |
| PSB bank resolution | resource manager -> .psb loader -> F001/125 bank |
| Image selection | u16 mapping key -> image index -> 12-byte vector /72-byte triangles |
| Dynamic change | rank owner rebuilds same en2d bank/key command stream, localized font suffix |
| gaHudAiMap constructor/init/config/update | 146118 /1461f8 /146960 /147038 |
| gaHudAiMap object size | 0x8c |
| Important map fields | HUD/player +c/+10; finish +14; route +3c; last/car-count +6c/+70; heading Z/X +74/+78; H/W/center +7c/+80/+84/+88 |
| Map render producer | 147038 -> queues ->32fce0 ->318e10 ->318bd8 |
| Course source | named MarkerLists/RaceLine, actual PS2 RACETEST/ITALYS1.XML |
| Route structure | begin/end/capacity vector, contiguous 80-byte records |
| Point representation/count | float32 XYZ at +40; sample293 points; X/Z consumed |
| Segment model | consecutive points in document order, clipped visible discontinuities |
| Bounds | computed by dumper for inspection; no bounds-based fit |
| Axis mapping | S*(Hz*dx-Hx*dz), S*(Hx*dx+Hz*dz), XZ only |
| Scale/center | 0.4f /HUD0(74,392) |
| Rotation/clipping | player-heading-relative, Cohen-Sutherland +/-45,+/-43 |
| Player marker | CarN output wrapper +8 -> position +f0/+f8; centered three-point chevron width4 |
| Opponents | NumCars participants excluding PlayerID; same position/transform; clipped X strokes; RGB from CarN/Colour |
| Map primitive/vertex | untextured stroked triangle strips; input Vec2 float32, stride8; command stride24 |
| Map color/alpha | green route shadow6/front3 with intensities127/250; marker width4, shadow40/front250; packet alpha=command alpha>>1 |
| MAP128STRIPED participates | NO in the traced race minimap; packet TME=0; wider asset use UNKNOWN |
| Route JSON | ignored data/ui2/italys1-map-verified.json and italys1-packfs-verified.json |
| SVG/debug view | ignored data/ui2/italys1-map-verified.svg and italys1-map-preview.png |
| Offline state | actual route point32 position; explicit heading(0,-1), Last32/Finish292; not a live capture |
| Offline result | 293 world/transformed points, 16 clipped segments /16 pair batches /one debug strip, repeated JSON/SVG byte-identical |
| Screenshot correlation | two full-race JPEGs correlate by HUD regions/primitive classes; exact runtime build/state UNKNOWN |
| ELF functions total | 63 admitted function records, five HUD owner vtables |
| Structures | entity, en2d, command, gaHudAiMap, marker record/vector, primitive command/vertex |
| PackFS/UI1 regression | 26/25 tests PASS before and after; parser unchanged |
| Tests total/passed/skipped | 80 /80 /0 |
| Compileall/diff-check | PASS /PASS |
| Original files | all four canonical hashes unchanged |
| Commit message | research: reverse PS2 HUD runtime; actual hash reported in chat/git history |
| Push | none |
| Next phase | additional PS2-UI work: COP2 matrix and final sprite packet/display composition |

Files created: `tools/hudruntime.py`, `tools/build_hudruntime_report.py`,
`tests/test_hudruntime.py`; UI2 findings/runtime/coordinate/minimap/ELF/
validation/next/final-report documents and four machine-readable JSON maps.
Files modified: `tools/elf_ui_query.py` (UI2 output plus guarded optional
scalar surrogates), `README.md` (UI2 index). All live under ps2-research.

Raw proprietary assets, route geometry, screenshots, memory/decompiler dumps
are local and ignored. No PC renderer, gameplay, original ELF/TNG payload,
historical research directory, grass/water/reflection implementation changed.
