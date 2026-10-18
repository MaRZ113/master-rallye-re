# PS2-BINARY-DIFF1 — PS2 vs PC graphics feature inventory and port ranking

Read-only research. Nothing under `pc-port/renderer`, `overlay`, `tests`, `.build`,
`.staging` or `dist` was touched; nothing committed; no branch change.

| Input | Identity |
|---|---|
| PS2 ELF `SLES_509.06` (EE R5900) | SHA-256 `b15a80c5…7001a78f2`; VA→file offset = VA−0xff000 |
| PC `MRallye.exe` (retail, `corpora/retail`) | SHA-256 `bf8aef32…b069b444c5f96b4`; image base 0x400000 |
| PS2 Ghidra | 12.1.4 + EER `r5900:LE:32:default`, `EERevalidation2` opened `-readOnly -noanalysis` |
| PS2 byte check | Rabbitizer 1.16.2 `InstrCategory.R5900` (`tools/r5900_constants.py`) |
| PC | REA/Ghidra 12.1.4 (open/resolve only) + GNU objdump (`/c/msys64/ucrt64/bin/objdump`) |

Addresses: PS2 values are EE VAs; PC values are absolute VAs (RVA = VA−0x400000).
Evidence labels: **PRIOR** = existing report in this repo (cited);
**NEW-BYTES** = verified in this phase on original bytes (Rabbitizer or objdump);
**NEW-DECOMP** = Ghidra pseudocode only (not original source; instruction check pending);
**UNKNOWN** = not established. No claim here implies PS2 pixel parity.

## 1. New findings in this phase

### 1.1 Damage HUD colour ramp — PS2 has an orange band, PC does not (NEW-BYTES)

| | PS2 `0x1412f8` (also copy `0x142068`) | PC `0x4a4420` |
|---|---|---|
| Input | `t = 1 − clamp(d,0,1)`, `d` = channel damage | same form (`fld/fcom 1.0, 0.0`, `fsub`) |
| White (1,1,1,1) | t > 0.8 | t ≥ 0.75 |
| Green (0,1,0,1) | 0.6 < t ≤ 0.8 | 0.5 ≤ t < 0.75 |
| Yellow (1,1,0,1) | 0.4 < t ≤ 0.6 | 0.25 ≤ t < 0.5 |
| **Orange (1,0.75,0.3,1)** | **0.2 < t ≤ 0.4** | **absent** |
| Red (1,0,0,1) | t ≤ 0.2 | 0 < t < 0.25 |
| Black (0,0,0,1) | — | t ≤ 0 |

PS2 thresholds: `lui 0x3F4C/0x3F19/0x3ECC/0x3E4C` at `1412f8..1414e8` (upper halves
of 0.8/0.6/0.4/0.2; lower halves via the paired immediate, not separately printed),
orange components `lui 0x3F40`(0.75) / `0x3E99`(0.3) at `141480/141488`.
PC thresholds are `.rdata` floats `0x690de4`=0.75, `0x68f958`=0.5, `0x68feac`=0.25,
`0x68f538`=1.0, `0x68f53c`=0.0 (read from file); colour stores at `4a4473..4a4536`.

The caller structures match: PS2 update `0x1414e8` (vtable `0x44cd40` slot `+0x34`
via `0x1412d0`) and PC `0x4a45be..0x4a4830` both read car output fields
(PS2 `+0x108/+0x104/+0x10c`, PC `+0x104/+0x100/+0x108`) and the same max-of-four
groups (`+0x9c,+0x48,+0x144,+0xf0` and `+0xa0,+0x4c,+0x148,+0xf4`). PS2 repaints
only when the value rises by >0.001 and bumps en2d `+0x88` + dirty bit `+0x78|4`.
Channels are bound by name: `Car%d_Damage_Steering/Engine/Suspension/Gear/Tyres`
(PS2 strings `0x44bc60..0x44bcc0`, consumer `0x1410d8`; PC pushes at
`0x4a42de..0x4a43be`, e.g. `Car%d_Damage_Engine` `0x6e4ea4` ← `0x4a4316`).

Consequence: the orange damage icon is a **PS2-only colour band in an otherwise
shared controller**. Band edges also differ, so PC band → PS2 band is not a
1:1 recolour (PC yellow 0.25–0.5 spans PS2 orange and yellow).

### 1.2 Rising/fading damage notification = `gaHudAiCarDamage1` (PS2-only class)

PS2 (NEW-DECOMP, field strings NEW-BYTES): class string `0x44bcd8`, vtable `0x44cd00`
(dtor `141ac0`, factory `141be0`, serialize `141d00`, update `142018`, init `141db8`),
ctor `141970`. Authored fields: `StartPos`/`TargetPos`/`EndPos` (`0x44bcf0/0x44bd00/
0x44bd10`, object `+0x68/+0x74/+0x80`), `Scale` (`0x446958`, `+0xbc`),
`Birth/Death Time` (`0x44bd18`, `+0xb0`, default 30 ticks), `Life Time`
(`0x44bd30`, `+0xc0`, default 30). Update `142018` calls:

* `1422f0` — per channel (ids 0 steering,1 engine,2 suspension,4 gear,3 tyres)
  computes the ramp colour with alpha forced 0 (`142068`), compares with the last
  colour (`142260`, eps `0x3a83126f`≈0.001) and on change pushes a 0x24-byte
  record {channel, phase=0, StartPos, RGBA} into vector `+0xa4..+0xac`.
* `142ab0` — phase machine: birth (1) for `+0xb0` ticks, hold for `+0xc0` ticks,
  death (2) for `+0xb0` ticks, then pop.
* `142b90` — draws at most 2 records: birth = `StartPos + (Target−Start)·k`,
  alpha `clamp(k)`; death = `TargetPos + (End−Target)·k`, alpha `clamp(1−k)`;
  `k = tick/BirthDeath`. Each record emits the channel image and image 5
  (white overlay, same alpha) through en2d `2062f0/2063a0/206338/205ce0`.

PC: no `gaHudAiCarDamage1`, `TargetPos`, `Life Time` strings (`tools/string_presence.py`);
`Birth/Death` exists at `0x6f5280` with no code push-reference found. **Absent on PC.**

### 1.3 Other string-anchored PS2/PC pairs (NEW-BYTES, presence only)

| Feature | PS2 anchor | PC anchor |
|---|---|---|
| Minimap `gaHudAiMap` | `0x44bf40` ← `146118`,`146868` | absent; PC has `gaHudAiGPSNeedle` `0x6e4fa4` ← `0x4a547c` (PS2 also has it, `0x44be48`) |
| SpeedDial | `0x44c2f0` ← `14b040` | `0x6e5234` ← `0x4a8124` (PRIOR hud-port1) |
| Brake lights `gaSFXBrakeLights`/`blight` | `0x472498` ← `1a0758`; `blight` `0x4724b0` ← `1a07e0` | `0x6e7350` ← `0x4ca044`; update `0x4ca1d0` (PRIOR xtrail-brake-followup) |
| Second `blight` user | `0x479ff8` ← `26c1b0` (3 refs) | UNKNOWN |
| Tyre tracks | `gaSFXTyreTracks` `0x4724e0` ← `1a0cd0`; textures `vehicles/skid1/2` `0x482c58` | `0x6e73b4` ← `0x4ca62b` |
| Drive particles | `particle/dirt_drive`,`tarmac_skid`,`mud_drive` ← `19cdf8` | `0x6e7018` ← `0x4c16ca`, `0x6e6fe4` ← `0x4c1706` |
| Car shadow | `Misc\Shadow\shadow` `0x485948` ← `332628`; `showroomshadow` `0x487708` ← `3aeca0` | `misc\shadow\shadow` `0x6ea3cc` ← `0x587f5a`; no showroom shadow string |
| Water surface | `watersurface2` (PRIOR water1) | `misc/water/watersurface3` `0x6e9f4c` ← `0x577aaa` |

## 2. Inventory and portability table

Portability classes: **overlay-only** (proxy + exact identity, no new game data path),
**needs assets** (private PS2-derived files, local only), **needs EXE hook** (requires
a native value/owner the proxy cannot see, i.e. code hook or memory read).
Effort: S ≤ 1 phase, M 2–3 phases, L > 3 phases. Status cites pc-port docs.

### 2.1 Vehicles (priority)

| Feature | PS2 evidence | PC counterpart / absence | Ported? | Portability | Effort |
|---|---|---|---|---|---|
| carshiny body env (mode3, mixed static+flipped framebuffer) | `390d98→391690/3a6c58→3ade58`; target producer `330780→31a518`; UV math in VU helper `408` (PRIOR refl1) | No `carshiny`/`rendertarget64` strings; PC native CAMERASPACENORMAL + alpha-weighted add (PRIOR refl1 §H) | Yes, Mode4 + 212-entry registry, runtime-confirmed Tata/Mode4 ([full-coverage](../pc-port/docs/full-coverage/final-report.md), [visual-parity-expansion](../pc-port/docs/visual-parity-expansion/final-report.md)) | overlay-only + ENV asset | done; residual coefficient/basis approx. |
| Mixed-material bodies (6 families) | generic mode3 rule `391690:391774–3918b4` (PRIOR coverage-followup/body-lights) | mixed PC draws | Partial: 1327 faces partitioned ([vehicle-model-port1](../pc-port/docs/vehicle-model-port1/final-report.md)) | overlay-only | S |
| Windscreen glass (mode20, static highlight FIX96, ZMSK1) | `3ae040` (PRIOR refl1) | no `windscreen-reflect` string | Xtrail headlight glass only ([xtrail-lights-model](../pc-port/docs/xtrail-lights-model/final-report.md)); fleet glass UNKNOWN coverage | overlay-only + asset | M |
| Whole PS2 race CAR mesh (25 families) | CAR.PSM tree `3900f0/391d38` (PRIOR ps2-format-lights) | PC car.dx | IMPLEMENTED_RUNTIME_PENDING except Kia/Xtrail confirmed ([port3 coverage](../pc-port/docs/vehicle-fleet-port3/coverage.md)); single-car races only ([fix2](../pc-port/docs/vehicle-fleet-port3/fix2/report.md) §5) | overlay-only + assets | M (opponents) |
| Lamp OFF / ON_CORE (mode1) / ADDITIVE_GLOW (mode14) | name overrides `391690`: `breaklightson-`→mode1 `391cc0`, `…glow-`→mode14 `391c54`; mode14 GS `31300c` ALPHA FIX128 Cd+Cs, ZMSK1 (PRIOR xtrail-brake-followup) | `gaSFXBrakeLights` `0x4ca1d0`, threshold `0x68f974`=0.1 matches PS2 selector | ON/glow 25 families, OFF 21 (+NewRav 0x142/24 in fix2); Bruno/Jump/Mattserati/UFO OFF Stock | overlay-only + assets | S (blockers) |
| Damage deformation | **PS2 mechanism UNKNOWN** — no PS2 damage owner reversed in any report; only HUD-side car output fields `+0x104..+0x10c` (§1.1) | PC private damaged copy at render instance `+0x90`, consumer `0x54c9d0` (PRIOR vehicle-damage-fix1/damage-owner) | PC-native damage kept; private damage maps for Xtrail/Kia/UFO only; 22 families Stock fallback ([port3 car](../pc-port/docs/vehicle-fleet-port3/car/findings.md)) | overlay-only (PC deltas) | M |
| Damage-tree / named-child switching | tag7/tag8 selector wrappers `391d38`, model `+0x40` (PRIOR ps2-format-lights); live selection UNKNOWN | PC conditional draws | Conditional lamps/windows preserved native ([race-model-port1](../pc-port/docs/vehicle-race-model-port1/final-report.md)) | needs EXE hook for live mask | M |
| Wheel transforms | WHEEL.PSM; PS2 wheel matrix producer **not reversed** | native wheel WORLD (steer/spin/suspension) | 24 families via native WORLD ([port3 wheels](../pc-port/docs/vehicle-fleet-port3/wheels/findings.md)) | overlay-only | done (runtime pending) |
| Body vertex lighting (`322220` ny grayscale .225/.4) | PRIOR refl1 §F | PC native lighting | Not ported (would be global relight → excluded by policy) | — | — |
| Frontend COMPLETE models | 29/29 decoded; tag102 = wheel cylinder `3947b0` (PRIOR) | complete.dx; owner `gaFrontendCarMoverAI` chain open | Xtrail runtime-confirmed; others BLOCKED on owner join ([coverage-followup](../pc-port/docs/coverage-followup/final-report.md)) | overlay-only | M |
| Showroom shadow | `misc/shadow/showroomshadow` ← `3aeca0` (NEW-BYTES) | absent on PC | No | needs assets + frontend owner | M; contract UNKNOWN |
| Race car drop shadow | `Misc\Shadow\shadow` ← `332628` | `0x587f5a` | Not compared | UNKNOWN | UNKNOWN |
| Tyre tracks / drive particles | `1a0cd0`, `19cdf8` | `0x4ca62b`, `0x4c16ca` | Not compared | both exist; delta UNKNOWN | — |

### 2.2 HUD

| Feature | PS2 evidence | PC counterpart / absence | Ported? | Portability | Effort |
|---|---|---|---|---|---|
| SpeedDial plate | `14b290→14b388→14b6c8`; 4×64² GXI quadrants (PRIOR ui2, hud-port0) | `gaHudAiSpeedDial` vtable `0x690F38`, consumer `0x56D110`, key/subimage `0x56D5AA/0x56D5D5` | No — blocked on same-session key0→texture join ([hud-port1.1](../pc-port/docs/hud-port1.1/final-report.md)) | overlay-only + asset | S |
| Damage icon orange band | §1.1 `0x1412f8`, update `0x1414e8` | `0x4a4420` 4-band ramp, no orange | No ([hud-port2-roadmap](../pc-port/docs/hud-port2-roadmap.md)) | **needs EXE hook** for exact bands (damage scalar). Overlay-only alternative only approximates: recolour PC yellow icons cannot tell 0.25–0.4 from 0.4–0.5 | S (hook) |
| Rising/fading damage notification | §1.2 `gaHudAiCarDamage1`, `142018/1422f0/142ab0/142b90`; images from `hud\hud-damage` (`0x46ffe8`, 7 refs in `183e08`) | absent | No | overlay-only possible (trigger on PC icon colour change of an identified damage packet, own sprite timeline) but thresholds differ → exact triggers need EXE hook; needs HUD-DAMAGE PSB assets | M |
| RaceLine minimap | `gaHudAiMap` `146118/1461f8/146960/147038`, clip `1469f0`, scale 0.4, centre (74,392) (PRIOR ui2) | absent; PC GPS widget instead | No | needs EXE hook (player pos/heading, opponents); route from RaceTest XML is data | L |
| Progress bar / rank / timer fonts | PRIOR hud-port0 feature matrix | same owner families, different fonts/positions | No | overlay-only + assets after widget mapping | M |
| Pause tiles `textboxalpha` | PRIOR hud-port0 | `textbox` | No (excluded) | overlay-only + asset | S |

### 2.3 Course dressing (Turkey2 = control)

| Feature | PS2 evidence | PC counterpart / absence | Ported? | Portability | Effort |
|---|---|---|---|---|---|
| Grass/shrub detail sprites | parser `2d5100`, producer `3597e0→31da60`, mode11 (PRIOR grass1) | no `$detail`/`grass1`/`bush1` usage | Yes, 36/36 courses Mode2 (Turkey2 2814/2894 grass, 1961/2193 shrub faces) ([full-coverage](../pc-port/docs/full-coverage/final-report.md)) | overlay-only + assets | done (deploy 72 files) |
| treeblend (mode2, src-alpha, ZMSK1) vs tree (mode6, ATE>64) | `3ae618` / `3ae710` (PRIOR treeblend1) | no `treeblend` string; PC uses tree | France1 bush01 pilot only ([PILOT1.3 handoff](../pc-port/HANDOFF.md)); Turkey2 has **no** treeblend (PRIOR cdelta1 detail survey) | overlay-only | S per course |
| Puddle mode9 / water mode10 / waterfall mode19 | `3aea50`, `3ae9a0` (PRIOR water1) | `watersurface3` `0x577aaa` vs PS2 `watersurface2` | Turkey3 puddle geometry, opaque preview only ([course-objects1](../pc-port/docs/course-objects1/final-report.md)) | overlay-only + assets | M (material: UV anim + secondary) |
| Extra geometry (trees/huts/boats) | PRIOR dressing1: no extra population proved; boat/hut reuse PC geometry | PC baked | No | needs assets; low value | — |
| Rocks/stones | `stones` category bound but **not emitted** by two-pool generator (PRIOR grass1) | — | N/A | — | — |
| Spline ambient (boats/barges/airships) | `gaEntitySpline` ctor `1a7b08`, update `1a80e8`, world write `1aa308` (PRIOR ambient1) | no `gaEntitySpline` string; some dinghies baked | No | overlay-only + assets (draw own mesh with source spline) | M |
| Birds | `gaAnimals_BirdManager` `1ae8b8/1af330` (PRIOR ambient2) | absent | No | overlay-only + assets (sprite, RNG, camera) | M |

### 2.4 Course physics objects (inventory only)

| Feature | PS2 evidence | PC counterpart | Status |
|---|---|---|---|
| Haybale/tumbleweed rigid bodies (58+25 authored) | `gaAiRigidBody` vtable `473820`, ctor `19fcd0`, update `1a0258`, manager `1715c8` (PRIOR rigid1) | `gaAiHayBale` ctor `0x4C9C30`, fixed `haybaletest` model; no tumbleweed class; loader rejects PSM (`55157C`) | NO-GO for private admission ([rigid-port1.3](../pc-port/docs/rigid-port1.3/final-report.md)); paused by user |
| Knockable checkpoint barrels | user observation only; owner UNKNOWN (PRIOR cdelta1) | markers non-colliding | UNKNOWN |
| Smoke emitters (81 Eggs) | binding UNKNOWN (PRIOR cdelta1) | UNKNOWN | UNKNOWN |

## 3. Ranking (what to port next, given cars stay first)

1. **Car blockers in flight** — finish PORT3 runtime qualification, then Bruno/Jump/
   Mattserati OFF, opponent cars. Overlay-only; highest visible value; already scoped.
2. **Damage HUD (§1.1 + §1.2)** — smallest new feature with complete PS2 maths and an
   exact PC structural twin (`0x4a4420`/`0x4a45be`). Exact port needs the damage scalar:
   either a one-function EXE hook replacing the PC ramp (S) or a read-only memory feed
   (outside current proxy policy). Notification sprite is overlay-only once triggers exist.
3. **Course materials** — treeblend admission beyond France1 and puddle mode9 material
   for the existing Turkey3 layer: overlay-only, assets already local.
4. **SpeedDial plate** — gated on one live join (hud-port1.1); small once unblocked.
5. Spline ambient / birds (M each), RaceLine minimap (L, needs hook), showroom shadow (UNKNOWN).

## 4. Recommended next three phases

1. **CAR-PORT3-QUALIFY** — run `vehicle-fleet-port3/qualify_runtime.py` on fix2 F10s for
   the 23 pending families; close Bruno/Jump/Mattserati OFF layouts; extend the fleet
   gate design to opponents. No new RE needed.
2. **HUD-DAMAGE1 (research + design)** — (a) byte-verify `0x1414e8`, `0x1422f0`, `0x142ab0`,
   `0x142b90` with Rabbitizer and the PC callers `0x4a45be..0x4a4878` with objdump;
   (b) identify the PC damage-icon packet (same method as HUD-PORT1: `gaHudAiCarDamage`
   vtable from ctor near `0x4a400b`/`0x4a4147`); (c) decide hook vs. approximation with
   the user, since an exact orange band needs the damage value.
3. **WATER-PORT1** — upgrade the Turkey3 puddle preview to mode9 (per-counter UV,
   WATERSURFACE2 secondary FIX56 additive, ZMSK1) using water1's render contract;
   then treeblend admission for the 13 other treeblend courses (Turkey2 stays control).

## 5. Open unknowns (explicit)

* PS2 vehicle damage deformation / damage-model switching code: not located.
* PS2 wheel transform producer: not reversed (port uses PC native WORLD).
* PS2 second `blight` consumer `26c1b0`: role UNKNOWN.
* Shadow, tyre-track and particle differences: presence only; rendering delta UNKNOWN.
* PS2 notification image indices (channel id → image) assume `hud-damage` bank; the
  bank binding at `183e08` is not decoded.
* All PS2 runtime/GS inherited state remains NOT_PERFORMED as in prior reports.

## 6. Files and reproduction

* `ps2-string-xrefs.txt` — PS2 string → reference → function list (Ghidra EER, read-only).
* `tools/BinaryDiffStringProbe.java`, `tools/BinaryDiffRangeProbe.java`, `tools/needles.txt`.
* `tools/r5900_constants.py` (Rabbitizer), `tools/string_presence.py` (both binaries).

```powershell
& 'D:\Game\Master Rallye\_reverse-tools\ghidra-bridge-main\ghidra_12.1.4_PUBLIC\support\analyzeHeadless.bat' 'D:\Game\Master Rallye\master-rallye-re-general\ps2-research\data\revalidation2\ghidra_ee' EERevalidation2 -process 'SLES_509.06' -readOnly -noanalysis -scriptPath <binary-diff1\tools> -postScript BinaryDiffRangeProbe.java <out.c> 140f30-142f40
```

```bash
ps2-research/data/revalidation1/tooling-venv/Scripts/python.exe -I ps2-research/binary-diff1/tools/r5900_constants.py 1412f8-1414e8
objdump -d -M intel --start-address=0x4a4420 --stop-address=0x4a4540 "D:/Game/Master Rallye/corpora/retail/MRallye.exe"
```

Raw decompiler dumps stay in the session scratchpad (not committed).
