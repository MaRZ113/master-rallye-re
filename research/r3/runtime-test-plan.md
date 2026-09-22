# R3 human runtime test result

## Final status

**RUNTIME VALIDATED — PASS (2026-09-22)**

The planned human validation was completed in the original Master Rallye
runtime. Both candidate roles were confirmed: the `complete.dx` position edit
was visible in the presentation/menu model, and the `car.dx` position edit was
visible during an actual race. The game and models loaded, and no new visual
artifacts were observed.

The correctly modified `car.dx` retained collision, normal damage/deformation,
and glass breakage. This validates same-topology positions-only writing; it
does not validate topology, UV, normal, or material writing.

The accepted archive procedure was: unpack `Data.sma`, modify the intended
resource, create a normal ZIP of the unpacked tree with 7-Zip, rename `.zip` to
`.sma`, and launch the game. This is the **RUNTIME-CONFIRMED REPACK METHOD**;
untested ZIP-format details are intentionally not inferred.

## Original test plan

Automated validation cannot establish that the 2001 runtime accepts a modified
DX. The ignored package under `.research-output/r3/runtime-test/` contains the
candidate bytes, `validation.json`, and `TEST_INSTRUCTIONS.txt`.

The available XML/TXT corpus identifies the Astero vehicle family but contains
no direct `car.dx` or `complete.dx` reference that proves which resource is
selected in every menu/race context. Therefore:

1. back up the matching original resource;
2. test `Astero-complete-one-vertex.dx` under the matching
   `complete.dx` name first;
3. restore the original;
4. only if needed, test `Astero-car-one-vertex.dx` under the matching
   `car.dx` name;
5. never install both candidates at once.

Report exactly:

- GAME LOADS / CRASHES;
- MODEL LOADS / FAILS;
- EDIT VISIBLE / NOT VISIBLE;
- OTHER ARTIFACTS.

Both candidates move one upper-body point by +0.08 source X, remain inside the
original AABB, preserve every non-position byte, and introduce no parser
warning. They remain narrowly scoped validation artifacts, not general-purpose
game mods.
