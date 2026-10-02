# Native menu tree — 9.3.1

Evidence class: **CONFIRMED_BY_EXE** from the existing hash-verified Ghidra program export; current loose corpus EXE whole-file identity mismatch is documented in `corrections.md`. The analyzed `.rsrc` bytes match the current file.

## Main window

Builder `00600570`; main window procedure `005FFB00`; main dispatcher `005FFC10`.

```text
&Game
  &Reset...  command 0x32
  —
  E&xit      command 0x2F
```

The menu has no editor, build, Game/Scene file, or BuildData item despite shipped `Menues/Enabled=true`.

## Tool-local menus

| Tool / builder | Native tree and salient state |
|---|---|
| Particle `006101D0` | `&File → &Close(0)`; `Particle &Edit → &New Particle(2), Rename &Particle(3), &Edit Particle(s)...(4), &Remove Particle(s)(5), &Cut Particle(s)(6), C&opy Particle(s)(7), &Paste Particle(s)(8)`; `&View → &Refresh(1)`; `&Help → &View(9)`. |
| Egg `006125A0` | Same exact Egg labels/IDs/states as 8.4.1; notably `&Hatch Egg(s)(0x10)` is enabled and `&UnHatch Egg(s)(0x11)` disabled. |
| Marker `00615D80` | Same exact Marker labels/IDs/states as 8.4.1; `&Reverse Order of Selected Marker(s)(0x22)` is absent. Spline/Area, Marker Direction, and Ceiling are disabled. |
| Broker `006199A0` | `&File → &New...(0), &Close(1)`; `&Edit → &New...(5), &Edit...(6), &Copy...(7), &Remove(8), &Branch` popup (enabled only when selected value name is `broker`), `&Options...(9)`, separator, `&Delete...(10)`; View Refresh(4), Debug Dump(2), Help View(3). |
| Flow `0061DAF0` | Same File/Load/Build tree as 8.4.1, plus `&Convert → &Convert FL to SFL(10)` enabled. File New/Open/Save/Save As remain disabled. |
| Generic parameter/tree editor `0061EFF0` | `&File → &New(0), &Save(1), E&xit(2)`; `&Edit → Cu&t(3), &Copy(4), &Paste(5), &Delete(6)`; `&Update → &Commit Changes(7), C&ancel Changes(8)`. |

The added Flow converter is local to an already-open Flow Builder window. It is not a main-menu route to that window. The complete normalized item/state data is in `menu-tree-cross-build.json`.
