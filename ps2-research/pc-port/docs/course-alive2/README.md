# COURSE-ALIVE2: the PS2 BirdManager on PC

Opt-in `PS2Birds=1` in PS2Port.ini. The default 0 is Stock: nothing is loaded or drawn, and no other PS2 feature changes.

This is a port of the PS2 system itself (`gaAnimals_BirdManager`, SLES_509.06), not an imitation. It covers spawning,
the RNG, flight, wing animation, the sprite bank and the sprite draw state on all 36 courses, each with its own PS2
settings. The base is the AMBIENT2 static reverse (`ps2-research/ambient2/`). This phase closed AMBIENT2's open links
with new targeted reverse engineering; the evidence is under "Recovered in this phase".

## What the PS2 does (the contract that is ported)

Each game tick (30 per second, as measured for splines and water in COURSE-WATER1), the dispatcher runs the manager
first and then its birds:

1. **Gate.** `1af330` runs only when **both** named MarkerLists resolve: `FlightList` and `MillList`.
2. **Observer.** The observer is the camera position: camera manager `201350` entry 0, `+c0..c8`.
3. **Burst** (`1afa20`).
   - A random draw `U(0.1,1)` is compared with `(clock += 0.003) * 0.1`, so the first burst can come only after 333 ticks
     (about 11 s).
   - Number of birds: `min(R(0,RndFly), free)`.
   - Spawn marker: the nearest FlightList marker in X/Z (cached, ±5 window), plus `R(0,3)`, clamped to the list.
   - Distance test, strict: `MinFly² < XZ² < MaxFly²`.
   - Birds are taken from the back of the free pool. Each gets the marker position and goes to the **front** of the
     pending queue.
4. **Retirement** (`1b0238`). A flying bird with `MaxFly² < XZ²` goes back to the free pool.
5. **Conversion** (`1affe0`). One pending bird per tick (the queue is FIFO) gets a FlyBird and an ImageBankSwitcher.
6. **Copy** (`1b0508`). The carrier translation is copied to the en2d sprite translation.
7. **Birds.** In pool order, each flying bird runs its FlyBird step `1b0e68` (rise below 0.35, speed growth, origin plus
   direction times travel) and its switcher `1b17e8` (keys 0→1→2, the first change after 5 ticks, then every 5 ticks).
8. **RNG.** One process-global Schrage generator (48271 mod 2³¹−1). Its output is the low 24 bits × 2⁻²⁴.
9. **Draw.** The en2d world sprite path `337a98` is used.
   - Bank `Misc/Animals/BurdyBrown`, PSB key = switcher key, two triangles per frame.
   - Local vertex = (vx−0.5, 0.5−vy) × 0.1.
   - Y-locked billboard from the view matrix row 2 (`330530`): F=(side.z,0,look.z), R=(F.z,0,−F.x), U=(0,1,0).

## Recovered in this phase (new evidence)

| Question (AMBIENT2 open) | Result | Evidence |
|---|---|---|
| MarkerList registry on the 26 courses without a local MillList | Every scene teardown clears the registry (`2a1ea8 → 1fda80` frees every list and empties the vector). No other XML of the 82 in PackFS defines a MillList. So the gate stays closed: **no birds on those 26 courses on the PS2.** | decompile `1fda80`, `1ff6a0`, `1fdba8`; PackFS scan |
| Observer | Camera position. The camera entry stores its world matrix at `+90..cc` (row 3 `+c0` = translation; `200460` dollies along row 2; `200550` is the frustum test). `1b0a40` reads the same entry. | decompile `2006c0`, `200460`, `200550` |
| Ground (Miller) birds | Their producers `1af770` (milling spawn) and `1aff58` (milling conversion) have no reference in the ELF: no call, no pointer. The ground vector stays empty. Takeoff paths `1afc88`/`1afdd8` return at once and use no RNG. | reference search over the ELF |
| Pool size | `Animals/MaxBirds` is read only by the manager. No code or PackFS file produces the key, so the pool is 16. | ELF/PackFS search |
| Brown or white | `1af0b0` passes `+94` by value to a property writer. The authored "Bird Brown" (first value False on 17 courses) is never read, so the bank is always BurdyBrown. | decompile `1af0b0`, `1af1c0` |
| Pending order | Insert at the front (`1afa20`), pop at the back (`1affe0`): FIFO. Free pool: pop at the back, retire to the back. | decompile |
| Tick order | Birds and manager share tick queue 3. Inside it, entities are ordered by byte `+48`: manager 3, birds 1 (`21e740(...,1)`). The manager runs first. | decompile `21e290`, `2200d0`, `1af460` (STATIC_INFERENCE for the sort direction) |
| Billboard basis | `3387c8 → 36fc18 → 36fb28` builds the view matrix (transposed rotation, −eye). `DAT_00435e88` = 1 in the ELF, so the side vector is not negated, and row 2 gives a camera-facing horizontal F. | decompile + ELF data |
| Texture alpha | The PS2 loader halves GXI alpha: resident NOISE.GXI alpha 128 → 64 in all owner GS dumps. Burdy alpha 0/255 → 0/1.0: a plain binary source-alpha blend. | GS dumps |
| Atlas orientation | VRAM row r = GXI file row 63−r. The PSB UV band v 0.75..1.0 is file rows 0..15, where the sprites are. | PSB/GXI decode |

## Port

| Part | File |
|---|---|
| Portable manager, RNG, FlyBird, switcher, billboard (no D3D/Windows/proxy) | `renderer/ps2_birds.hpp` |
| Asset, camera extraction, geometry, pilot (course guard, 30 Hz clock, pause, restart) | `renderer/ps2_birds_pilot.hpp/.cpp` |
| Native seam (proof, draw, diagnostics) | `renderer/ps2_birds_native_integration.hpp` |
| Asset generator from PS2 data | `tools/prepare_ps2_birds.py` |
| Python reference model | `tools/ps2_bird_model.py` (AMBIENT2 primitives of `tools/bird_runtime.py`) |
| Verification | `tools/verify_ps2_birds.py`, `tests/ps2_birds_tests.cpp`, `tests/test_ps2_birds.py` |

Decisions:
- **Integration.** Same architecture as COURSE-ALIVE1: the course comes from the race certificate, and the same PS2
  course-package guard is used. The world proof is the verified gameplay VIEW/PROJECTION plus a later world draw.
  Drawing goes through the fixed `CourseObjectTransaction` at the pre-UI boundary, after the course, PS2 water and
  spline objects.
- **PS2 mode8 sprite state → D3D:**
  - ABE `(Cs−Cd)·As+Cd` → SRCALPHA/INVSRCALPHA;
  - ATE 0 → no alpha test;
  - ZTST GEQUAL (PS2 reversed depth) → LESSEQUAL;
  - ZMSK 1 → no depth write;
  - FGE 1 → native course fog;
  - TFX MODULATE with en2d colour (1,1,1,1) → texture × white;
  - TEX1 linear/linear → linear;
  - REGION_CLAMP of the atlas cell → one 16×16 texture per cell with CLAMP.

  Because the birds do not write depth and are drawn after the water, a water surface in front of a bird hides it
  through the depth test. Birds never cover water or other geometry that is in front of them.
- **RNG start state.** Like the PS2, one session stream starts at the constructor seed 12345 and carries over from race
  to race. Other PS2 consumers of the global RNG (cars, particles) are not interleaved, so the bird sequence of a real
  PS2 race cannot be reproduced bit for bit. Statistically it is the same generator.
- **Camera.** The PC gameplay camera stands in for the PS2 camera. The two follow the car in the same way, but their
  exact positions differ.
- **No interpolation.** Positions change at 30 Hz, as for the splines.
- **Diagnostics.** `PS2BirdsIgnoreListGate=1` (DIAGNOSTIC, not PS2) runs the manager on the 26 closed courses, for
  previews only. `PS2BirdsStockCourses=1` lifts the course guard.

## Verified automatically (`verification.json`, OVERALL PASS)

- The asset is deterministic and its digest is pinned (`f37cebd6…`).
- Configuration of all 36 courses equals the PS2 XML. The gate is open on exactly 10: France1, Italy2, Italy3, ItalyM2,
  ItalyS3Flip, ItalyS4, SpainS2, SpainW, TurkeyM, TurkeyS1.
- Resources: the 4 cells equal the GXI sprite band (176 opaque texels, binary alpha); the 4 frames equal the PSB.
- C++ vs the Python model, bit for bit, on all 36 courses: 18,000 ticks each (648,000 ticks) and 3,748,764 drawn world
  vertices. Compared: RNG state, clock, cache, counts and every entity's key, en2d and carrier.
- C++ FlyBird equals the committed AMBIENT2 trace (`ambient2/synthetic-flight-trace.json`).
- Restart repeats the same timeline, and a closed gate uses no RNG and makes no birds.
- Contract tests (ctest `ps2_birds_contracts`): RNG = 48271·s mod (2³¹−1) over 100,000 states, the switcher period, the
  clock wait, FIFO order, retirement, billboard fallback, camera extraction and asset rejections.

Synthetic camera statistics (camera path along each FlightList with a fixed seed, so not a race): first birds after
about 13.5 s (SpainW 51 s), at most 11–16 flying at once.

## Not verified (needs the game)

- Look against the PS2: size, colour, fog, transparency at the edges, mirror orientation of the sprite, draw order with
  water and foliage.
- Live timing in a real race, and pause, restart, course change and replay in the real menus.
- A PCSX2 GS capture of a PS2 race **with birds on screen** does not exist yet. None of the 22 owner dumps contains the
  Burdy texture in VRAM (all were taken at the start or on courses without birds).
- That the 26 closed courses really show no birds on the PS2. This is a strong static conclusion, but not observed.

## Limits

- Single camera only (no split screen).
- Birds update at 30 Hz with no interpolation; PS2 en2d interpolation is unknown.
- Translucent geometry drawn without depth write (foliage) is not sorted against the birds.
- The RNG is not interleaved with other PS2 consumers (see "RNG start state" above).
