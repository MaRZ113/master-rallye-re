# Native menu tree — retail

Evidence class: **CONFIRMED_BY_EXE**; retail EXE SHA256 matches the known identity. Shipped `dev.xml` has `Menues=false` and `DebugWindow=false` (**CONFIRMED_BY_CORPUS**).

## Main window

Builder `005B1320`; main window procedure `005B0880`; main dispatcher `005B0990`.

```text
&Game
  &Reset...  command 0x32
  —
  E&xit      command 0x2F
```

## Tool-local menus

| Tool / builder | Native tree and salient state |
|---|---|
| Particle `00655370` | `&File → &Close(0)`; `Particle &Edit → &New Particle(2), Rename &Particle(3), &Edit Particle(s)...(4), &Remove Particle(s)(5), &Cut Particle(s)(6), C&opy Particle(s)(7), &Paste Particle(s)(8)`; View Refresh(1); Help View(9). |
| Egg `00657750` | Common exact Egg labels/IDs/states; `&Hatch Egg(s)(0x10)` enabled and `&UnHatch Egg(s)(0x11)` disabled; camera and Edit Method checks reflect state. |
| Marker `0065AF40` | Common exact Marker tree plus enabled `&Reverse Order of Selected Marker(s)(0x22)`; Spline/Area view, Marker Direction camera, and Ceiling snap are disabled. |
| Broker `0065EEB0` | `&File → &New...(0), &Close(1)`; `&Edit → &New...(5), &Edit...(6), &Copy...(7), &Remove(8), &Branch` popup (enabled only when selected value name is `broker`), `&Options...(9)`, separator, `&Delete...(10)`; View Refresh(4), Debug Dump(2), Help View(3). |
| Flow `00662FB0` | Common Flow File/Load/Build tree plus enabled `&Convert → &Convert FL to SFL(10)`. File New/Open/Save/Save As remain disabled. |
| Generic parameter/tree editor `006644C0` | `&File → &New(0), &Save(1), E&xit(2)`; `&Edit → Cu&t(3), &Copy(4), &Paste(5), &Delete(6)`; `&Update → &Commit Changes(7), C&ancel Changes(8)`. |

The checked camera/snap items reflect local tool state. Some selection-dependent states are dynamic. Exact common labels/IDs/conditions and retail additions are in `menu-tree-cross-build.json`; Egg Edit Method pointers resolve to `en3d` and `en2d` in retail memory.
