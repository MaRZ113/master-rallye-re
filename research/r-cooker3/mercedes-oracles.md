# R-COOKER3 Mercedes runtime oracle record

**T1, T2, and T3 are closed.** This file started as a run plan; the original
procedure below is retained for history. Final observations and log hashes
are in [runtime-results.json](runtime-results.json), with concise per-oracle
records in `oracle-t1-texture-miss.md`, `oracle-t2-cache-only.md`, and
`oracle-t3-collision-damage.md`.

| Oracle | Final status | Result |
|---|---|---|
| T1 ordinary DXT cache miss | `CONFIRMED_BY_RUNTIME` | Missing `underdash-tga.dxt` was reported; no GXI read or DXT write occurred in this tested consumer path. |
| T2 Mercedes cache-only package | `CONFIRMED_BY_RUNTIME` | All three DX roles and 25 referenced DXT loaded; no Mercedes GXM/GXI or authoring-root access. |
| T3 collision | `CONFIRMED_BY_RUNTIME` | Normal solid barrier response without gross offset/pass-through. |
| T3 damage | `CONFIRMED_BY_RUNTIME` | External and internal damage observed working. |

The negative T2 assertion is Mercedes-scoped. The same log contains unrelated
global `Reading GXM` lines; that does not contradict Mercedes cache-only use.

All run outputs belong under the ignored current-branch path
`.research-output/r-cooker3/`. Do not write results into the parallel R5V
worktree. The prepared isolated runtime copies and local Junction helpers are
already there and hash-verified against their source workspaces.

The selected source is Demo 8.4.1 `DataGx/Vehicles/Copy of Mercedes`:

- `complete.gxm`: SHA256
  `95caced8716239d4fa093fc0320e737e13dc1eedc8b649456d4cc89444fe354d`
- runtime-cooked `complete.dx`: SHA256
  `ddad0c7b13be70388a60a541255eaaf3af7f9b1815f5aa02f2b60050862dc28b`
- `car.dx`: `5ec5f7480ddfc1380131a012b300a4cdeb28b869a1668b6f8bbe97210893ff44`
- `wheel.dx`: `8707d887a75c452eb739775e21f94109521d9fc6be07726cee28a8e911c590ff`

These Cook A/B outputs were byte-identical in the prior controlled run. This
phase adds three different runtime questions; it must not generalize beyond
this source/environment.

## T1 — texture cache miss

**Final state: CLOSED — `CONFIRMED_BY_RUNTIME` (negative cache-miss result).** See [oracle-t1-texture-miss.md](oracle-t1-texture-miss.md)
for the observed miss, absent GXI read/write events, and the limited inference.

Chosen dependency:

- DX texture slot: `underdash-tga`, present in the parsed `complete.dx` draw
  record and source GXM references.
- source: `Underdash-tga.gxi`, 65,544 bytes, SHA256
  `c8e3578ac885531aad2dc8c56ba2b5edcdf35237b325a09452626b6ae436ded5`.
- historical DXT baseline: `underdash-tga.dxt`, 65,556 bytes, SHA256
  `d2eda2c6196d9d50448f90828450d81c4f6dc1d8041b7c0ae04ddbbcb81f8a9f`.
- expected dimensions: 128×128. Existing DXT parses, and the prior offline
  encoder result equals the historical bytes; neither fact proves retail
  generated those bytes.

## T2 — cache-only portability

**Final state: CLOSED — `CONFIRMED_BY_RUNTIME`.** See [oracle-t2-cache-only.md](oracle-t2-cache-only.md). The original run used
`.research-output/r-cooker3/oracle-t2-t3/runtime/`. The already-removed
authoring Junction must remain absent. Its package manifest expects three DX,
25 DXT, and no GXM/GXI/TXT in `DataGx/Vehicles/Mercedes`.

## T3 — collision and damage

**Final state: CLOSED — `CONFIRMED_BY_RUNTIME` for collision and both reported damage behaviors.** See [oracle-t3-collision-damage.md](oracle-t3-collision-damage.md). The operator reported the collision and damage observations from the isolated T2/T3 runtime. No standalone raw T3 capture was present in the checked inputs.

## Runtime result record

| Oracle | Status | Observed evidence |
|---|---|---|
| T1 GXI → DXT cache miss | CLOSED | Missing Mercedes DXT reported; no `Reading GXI` / `Saved cached texture`; scoped negative path evidence |
| T2 cache-only package | CLOSED | complete/car/wheel and 25 unique DXT loaded; no Mercedes authoring access; unrelated game-wide GXM activity retained as unrelated |
| T3 collision | CLOSED | normal solid-object response reported |
| T3 external/internal damage | CLOSED | both observed working; glass breakage is not expected for this model |

These results close the Mercedes oracles. Native GXM cooking has not been
generalized beyond Mercedes yet; the Forester job is the next static-ready
candidate and still needs an operator cook before any runtime claim.
