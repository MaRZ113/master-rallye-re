# Native menu tree — 8.4.1

Evidence class: **CONFIRMED_BY_EXE** from the existing Ghidra program analyzed from a `RESEARCH_PATCHED_COPY`. The current pristine corpus EXE is authoritative for future analysis. The `.rsrc` bytes agree with the analyzed program; see `research/corpus/executable-provenance.md`.

## Main window

Builder `004EC530`; main window procedure `004EBB30`; main dispatcher `004EBC40`.

```text
&Game
  &Reset...  command 0x31
  —
  E&xit      command 0x2E
```

No editor, build, Game/Scene file, or BuildData command is inserted here.

## Tool-local menus

These are dynamically built and attached only after a tool window is opened. Their command IDs are local to that tool's window procedure, not the main dispatcher.

| Tool / builder | Native tree and salient state |
|---|---|
| Particle `0053A710` | `&File → &Close(0)`; `Particle &Edit → &New Particle(2), Rename &Particle(3), &Edit Particle(s)...(4), &Remove Particle(s)(5), &Cut Particle(s)(6), C&opy Particle(s)(7), &Paste Particle(s)(8)`; `&View → &Refresh(1)`; `&Help → &View(9)`. |
| Egg `0053C5D0` | `&File → &Close(0)`; `&Options → &General...(4)`; `&Egg List → &New List(5), &Edit List...(6), &Copy List...(7), &Remove List(8)` (Remove depends on selection); `E&gg Edit → &New Egg(9), &Rename Egg(10)` (depends on selection), `&Edit Egg(s)...(11), &Remove Egg(s)(12), &Hatch Egg(s)(16)` (enabled), `&UnHatch Egg(s)(17)` (disabled), `&Cut Egg(s)(13), C&opy Egg(s)(14), &Paste Egg(s)(15)`; `&View → &Refresh(3)`; Camera checks `Top Down(0x15), Bottom Up(0x16), Front to Back(0x17), Back to Front(0x18), Left to Right(0x19), Right to Left(0x1A)`; Snap `&Floor(0x13), &Grid(0x12), &Near Eggs(0x14)`; Edit Method checks `en3d(0x1B), en2d(0x1C)`; Debug `&Dump(1)`; Help `&View(2)`. |
| Marker `0053FF70` | `&File → &Close(0)`; `&Options → &General...(3)`; `Marker &List → &New List(4), &Edit List...(5), &Copy List...(6), &Remove List(7)` (Remove conditional); `Markers &Edit → &New Marker(8), &Edit Marker...(9), &Remove Marker(s)(10), &Cut Marker(s)(11), C&opy Marker(s)(12), &Paste Marker(s)(13)`; View as Markers/Open Line/Closed Line/Tris/Quads/Spline/Area IDs `0x1A–0x20` (Spline and Area disabled), `&Refresh(2)`; Camera `Top Down/Bottom Up/Front to Back/Back to Front/Left to Right/Right to Left` IDs `0x13–0x18`, `Marker Direction(0x19)` disabled; Snap `&Floor(0x0F), &Grid(0x0E), &Near Markers(0x10), &Ceiling(0x11)` (Ceiling disabled); Debug `&Dump(1)`; Help `&View(0x21)`. |
| Broker `00543B90` | `&File → &New...(0), &Close(1)`; `&Edit → &New...(5), &Edit...(6), &Copy...(7), &Remove(8), &Branch` popup (enabled only when selected value name is `broker`), `&Options...(9)`, separator, `&Delete...(10)`; `&View → &Refresh(4)`; `&Debug → &Dump(2)`; `&Help → &View(3)`. |
| Flow `00547C00` | `&File → &New...(3), &Open...(4), &Save(5), Save &As...(6)` disabled; `&Close(7)` enabled. `&Load → &Clear → &Speed Matrix(8)`; separator; `&Speed Matrix(9)`. `&Build → &Simple Game(0), &Race Game(1), &Rally Game(2)`. FL→SFL converter is absent in this build. |
| Generic parameter/tree editor `00548E10` | `&File → &New(0), &Save(1), E&xit(2)`; `&Edit → Cu&t(3), &Copy(4), &Paste(5), &Delete(6)`; `&Update → &Commit Changes(7), C&ancel Changes(8)`. |

The main menu and these local menus are separate roots. Exact enabled/check conditions are captured in the normalized item-by-item structure in `menu-tree-cross-build.json`. Finding a local menu proves the post-open controls only; it does not identify the command sender that opens its parent window.
