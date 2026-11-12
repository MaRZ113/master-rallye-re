# ForesterSTI PS2 race body and body-scoped brake lamps (fix 05)

Base: a882c48 (fix 04), owner host `host-roster-v4-forester-04` (renderer
9f7d8918, loader 80561f21, roster da2dd875). New candidate:
`.research-output/hosts/host-roster-v4-forester-05` (copy of fix 04; fix 04 is
preserved unchanged).

## Why the PS2 body never appeared in races

The renderer since c0dd9d0 expects `FORESTER-CAR-FLEET.ps2model` SHA256
`b17b595c...` (14 chassis sources, lit brake records excluded). The owner hosts
`host-roster-v4-01` and `host-roster-v4-forester-04` still carried the earlier
asset `49f52831...` (16 sources) copied by `roster_v4_host.py` before fix 03
regenerated it. The race fleet child therefore never loaded and every race fell
back to the PC body without a fleet gate note (owner log 2026-11-11 23:28:
menu PS2 replacement at frame 843, races with no `fleet` effect at all, while
Jump in the same session was replaced). Fix 05 installs the current asset; the
old file is kept in `provenance/`.

## Why the brake ON layer disappeared on the PC model

Fix 04 put the original PS2 ON core and glow (positions of the PS2 body) into
the native PC model. The PC (Demo) body is the PS2 body rescaled: the PS2 OFF
lamp `root.15.1.0` and the PC OFF lamp of the `blight` group are the same
16-vertex mesh with bit-identical UVs, displaced by 4-5 cm (fitted per-axis
scale 1.048 / 1.031 / 1.020, affine residual up to 5 mm). The PS2 ON core sat
inside the PC body and was hidden.

## Two exact sets, selected by the presented body

`tools/forester_ps2_lamps.py` (rewritten) authors, from `FORESTER/CAR.PSM`:

| set | OFF (layer 2) | ON core (0) | glow (1) | registry policy |
| --- | --- | --- | --- | --- |
| PS2 | `root.15.1.0` exact | `root.15.0.0` exact | `root.15.0.1` exact | `PS2_BODY_ONLY` |
| PC  | native PC OFF lamp (unchanged) | PS2 ON vertices moved one-to-one onto the PC OFF lamp (via the UV correspondence) | inner ring as the ON core; halo vertices keep their PS2 offset from the bordering inner vertex, scaled by the fitted body scale | `PC_BODY_ONLY` |

Topology, UVs and vertex colours are PS2 in both sets. Source UVs are used
unflipped: the PC OFF lamp UVs equal the PS2 source UVs. The `blight` group is
OFF = [PC OFF, PS2 OFF], ON = [PC ON, PC glow, PS2 ON, PS2 glow], like the PS2
node, whose ON branch has no OFF lamp under its opaque core. Body, glass and
collision bytes are checked unchanged; the top-level record count stays 18.

`MR-ADDON-LAMPS 3` adds `PS2_BODY_ONLY` / `PC_BODY_ONLY` (layer 2 is accepted
only in a body-scoped set; v1/v2 files read as before). Renderer:

- `draw_fleet_lamp` identifies the row (exact identity, or the healthy
  witness of the same owner and mesh material for damaged geometry) and draws
  only the set of the body presented for that owner: PS2 when the same owner
  submitted a PS2 body in this or the directly preceding frame
  (`Ps2BodyPresence::recent`), PC otherwise. The other set is suppressed.
- PC set: native draw with ordinary PC lamp art. PS2 set ON/glow: the PS2
  lamp art with `BrakeGlow=1`, native art with `BrakeGlow=0`. OFF lamps always
  keep native art.
- The catalog is read regardless of `BrakeGlow`, so the set choice also works
  without lamp art and in races without a single-car fleet certificate (AI or
  multi-car: no PS2 body, PC set).

## Round 2 (owner test 2026-11-12): strip winding and glass

The owner confirmed the PS2 body in races. Two defects remained:

- Every other triangle of the PS2 lamps was missing. PS2 strips alternate
  winding; fix 04 and round 1 only swapped the first two corners. The tool now
  orients each PS2 triangle by its vertex normals ((b-a)x(c-a) . n > 0, the
  convention of every native PC record). All lamp and glass triangles of the
  candidate pass this check.
- PC glass panes (native conditional records) drawn over the PS2 body with an
  offset. The PC and PS2 panes differ in shape (PC windscreen 8 vertices, PS2
  10; best affine fit still 14-16 mm off), so a transform cannot place them.
  Each pane state (intact/cracked, one draw per case as the native glass
  selector requires) now holds the untouched PC triangles followed by the
  original PS2 triangles (`root.11/12/13 .0.0` intact, `.1.0` cracked). Rows
  `layer 3 ... SPLIT:n` let the renderer submit only `[0,n)` for a PC body or
  `[n,count)` for a PS2 body, from the same native state and material. Glass
  damage switching is preserved in both modes.

## Checks

Overlay build (baseline + PS2 CTest), registry/native/bootstrap tests via
`tools/test_vehicle_lamp_native.py` on the fix 05 candidate. Gameplay checks
are pending (owner):

1. ForesterSTI, MODEL = PS2, Quick Race: PS2 body visible; braking shows the PS2
   ON core and glow on the PS2 tail lamps with PS2 lamp art.
2. MODEL = PC: Demo body; braking shows the transferred ON core and glow on the
   PC tail lamps with PC lamp art; nothing inside or floating off the body.
3. Optional: `BrakeGlow=0` restart, both models: same geometry, PC art only.

Known limits: the ghost car and shadow/reflection passes draw the native
records without set selection (both lamp sets / both pane halves). PS2 cracked
panes use the PC cracked texture of that state.
