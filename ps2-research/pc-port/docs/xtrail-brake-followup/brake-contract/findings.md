# Original brake selection and glow contract

Canonical PC SHA256: bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4.
Canonical PS2 SHA256: b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2.

## PC engine owns brake selection

REA/Ghidra12.1.4 identifies gaSFXBrakeLights constructor0x4ca040/vtable0x691488.
Init0x4ca110 retains Egg+0x50 -> +0x18 model at AI+0x18 and resolves named
`blight` at AI+0x14. It creates Controller/<EggName>/ControllerCarBrokerAccess.
The exact vtable+0x10 target0x4ca1d0 was absent from REA's initial function
inventory (explicit invalid_request). A bounded noanalysis x86 import then
disassembled only that target. All41 instruction byte windows match original PE
section mappings; bounds0x4ca1d0..0x4ca23e.

The original update reads Broker result+8 pointer -> float32+0x24. Original
threshold0x68f974=0x3dcccccd. Ordered value>float32(.1) writes blight2; otherwise
(including unordered) blight1. REA writer0x4d3c50 checks nonnegative index/value,
index<model+0x20 count and value<=model+0x14 max[index], then writes
model+0x4 values[index]. This matches the PS2 selector contract.

**CONFIRMED_BY_EXE, not live owner observation.** Reuse original engine emission
of verified on/glow geometry. The port needs no new Broker reads, brake key
heuristics, AI calls or selector writes. Current source geometry/UV/texture and
buffer generation must still identify the actual native lamp draw.

## PS2 mode14 is additive

Fresh EER r5900:LE:32:default and Rabbitizer R5900 checked4623 original words.
Dispatch0x312610 table0x4850c0: mode14 word0x4850f8 ->0x31300c; mode0/1 both
dispatch0x3126e4. Compact original probes are in mode14-gs-evidence.json.

Mode14 forces triangle-strip4/IIP1/TME1/ABE1/FGE0; higher PRIM bits inherited.
TEX0 TCC1/TFX1 DECAL. ALPHA low0x29/FIX128 gives `(Cd-0)*128/128+Cs=Cd+Cs`.
It is not source-alpha interpolation. The original authored glow mesh and texture
supply its shape; this case does not activate a body secondary environment pass.
TEST=(old&0xfffffffffff9c000)|0x41000: ATE0/ZTST2 GEQUAL, ZTE/DATE inherited.
ZBUF ZMSK1 masks depth writes. Do not force PS2 GEQUAL into PC without depth proof.
TEX1=(old&0xfffff000ffe7fe1e)|0x120: LCM0/MMAG1/MMIN4/L0/K0, MXL/MTBA inherited.
Exact live GS sampling and inherited fields remain NOT_PERFORMED.

Mode1 uses default setup: ABE0/FGE1, TCC0/TFX0, depth writes allowed; ALPHA44
is inactive. This is PS2 setup, not a measured PC native state table.

## Vehicle identities and remaining gate

User identified rear screenshots as **Terrano**, not X-Trail.
XTRAIL: named root.20@175524, on root.20.1.0@175710/6faces/mode1,
glow root.20.1.1@175870/22faces/mode14.
TERRANO: named root.24@191201, on root.24.0.0@191235/6faces/mode1,
glow root.24.0.1@191404/20faces/mode14.
Both on/glow use selector2; child ordinal differs. Historical source hashes and
material slots remain in vehicle-model-port1/ps2-format-lights/lights-contract.json.
These are authored source face counts, not lamp or live draw counts.

Smallest runtime check: same-session rear view, released F10 / held brake F10 /
released F10. Join current on/glow source geometry+UV+texture+buffer generation,
confirm original engine selection and current owner/world pose. Then an exact
emitted-draw replacement may use ONE/ONE glow and ZwriteOFF with the native PC
depth convention, restoring exact states. Never replay guessed glow geometry.

No native calls, memory mutation, controller hook, physics or builds in this workstream.
