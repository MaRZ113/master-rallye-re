# Next bounded PS2 work

Recommended next phase: **additional PS2-UI work**, completing the ordinary
PSB sprite transform. UI2 is PARTIAL because final sprite rectangles are not
fully proved; the minimap route source/math/producer is no longer the blocker.

1. Decode the actual COP2 matrix operation at `3cb2d0` and its callers
   `342b90/3432b8`; connect `338ab8/343458` projection/view inputs through
   `3376c0` to the sprite packet's final XY. Preserve exact-build provenance.
2. Resolve current video-mode selection for globals `42d29c`, `42d2a0`,
   `42d2c4`, and PS2/ScreenPosX/Y display offset. Prove logical coordinates
   separately from physical field/interlace and PCSX2 presentation scaling.
3. Validate independently on the dial, needle, progress bar, rank/timer
   anchors and the direct minimap center. Do not fit values to screenshots.
   Only after that promote conditional rectangles to confirmed results and
   assess UI2 completion gates 3/4.
4. For a runtime-correlated minimap frame, record exact ELF hash, course name,
   route vector, PlayerID/NumCars, vehicle-output position/vectors, map
   heading fields, LastMarker, FinishArea/BestMarker and split BestMarkers.
   Supply the actual heading state to hudruntime instead of a diagnostic
   state. Check the first-frame heading seed and shared-map clip/counter
   behavior if split-screen parity becomes relevant.

Optional later UI precision work: recover exact split/finish crossbar
vertices, degenerate stroke joins and font/locale advances. These are
explicit exclusions of the current centerline preview, not evidence gaps
about the source or general transform of the dynamic minimap.

Grass1/Bush1, WaterSurface2 and environment/reflection resource findings
remain preserved in UI1. They were not revisited. Starting PS2-GRASS1,
PS2-WATER1 or PS2-REFL1 now would leave the current UI coordinate gate open;
none is started by this task. No PC HUD implementation is authorized here.
