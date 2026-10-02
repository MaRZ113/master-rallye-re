# Native menu tree — 9.10.0

Evidence class: **CONFIRMED_BY_EXE**; raw corpus identity matches the documented hash. Shipped `dev.xml` has `Menues=false` and `DebugWindow=false` (**CONFIRMED_BY_CORPUS**).

## Main window

Builder `00631FC0`; main window procedure `00631550`; main dispatcher `00631660`.

```text
&Game
  &Reset...  command 0x32
  —
  E&xit      command 0x2F
```

## Tool-local menus

| Tool / builder | Native tree and salient state |
|---|---|
| Particle `006419F0` | `&File → &Close(0)`; `Particle &Edit → &New Particle(2), Rename &Particle(3), &Edit Particle(s)...(4), &Remove Particle(s)(5), &Cut Particle(s)(6), C&opy Particle(s)(7), &Paste Particle(s)(8)`; View Refresh(1); Help View(9). |
| Egg `00643DD0` | Common exact Egg labels/IDs/states; `&Hatch Egg(s)(0x10)` enabled and `&UnHatch Egg(s)(0x11)` disabled; `en3d` and `en2d` method checks. |
| Marker `006475C0` | Common exact Marker tree plus enabled `&Reverse Order of Selected Marker(s)(0x22)`; Spline/Area view, Marker Direction camera, and Ceiling snap are disabled. |
| Broker `0064B530` | `&File → &New...(0), &Close(1)`; `&Edit → &New...(5), &Edit...(6), &Copy...(7), &Remove(8), &Branch` popup (enabled only when selected value name is `broker`), `&Options...(9)`, separator, `&Delete...(10)`; View Refresh(4), Debug Dump(2), Help View(3). |
| Flow `0064F6B0` | Common Flow File/Load/Build tree plus enabled `&Convert → &Convert FL to SFL(10)`. File New/Open/Save/Save As remain disabled. |
| Generic parameter/tree editor `00650BC0` | `&File → &New(0), &Save(1), E&xit(2)`; `&Edit → Cu&t(3), &Copy(4), &Paste(5), &Delete(6)`; `&Update → &Commit Changes(7), C&ancel Changes(8)`. |

The Marker reverse-order item is a local editor action, not a sender for the global Marker Editor open command `0x3B`. Item-level states are in `menu-tree-cross-build.json`.
