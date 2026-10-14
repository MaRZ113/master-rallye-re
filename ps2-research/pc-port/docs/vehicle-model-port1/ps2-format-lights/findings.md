# COMPLETE post-tree format and bounded lamp ownership

Source audit on `master`, starting HEAD
`a6daf3b17d32043c948e3ed9a843b1a5b3258f16`. The original renderer, Course SDK,
canonical PS2 inputs and protected PC assets remain unmodified. Only this
directory contains source/test/compact metadata changes; full EER output remains
ignored under `ps2-research/data/vehicle-model-port1/`.

## Terminal102 is a wheel-cylinder record, not a visual node or LOD

**CONFIRMED_BY_BOTH.** Fresh read-only Ghidra12.1.4 Emotion Engine Reloaded
`r5900:LE:32:default` export and Rabbitizer1.16.2
`InstrCategory.R5900` independently checked **2032** original instruction words.
The exact canonical ELF hash is
`b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2`.
The compact original probes, PT_LOAD offsets and function bounds are in
`r5900-format-evidence.json`; no generic MIPS surrogate is used.

The actual top-level consumer chain is:

```text
PSM539 vertex records + visual recursive tree
 -> 0x3900f0 -> 0x391d38 returns at exact tree end
 -> 0x38fac0 top-level tag loop reads102
 -> compare102 at0x38fe68/6c -> call0x3947b0 at0x38ff1c
 -> stream virtual+0x84 reads exactly two float32 values
    at0x3947f4 and0x394824
 -> allocation0x74 + constructor0x2444e0
 ->0x3a5c60 stores first value at cylinder+0x14
 ->0x3a5c90 stores second value at cylinder+0x18
 -> name predicate: literal wheel at0x4879c0
 -> matching wheel name: model+0x38 = cylinder
 -> other name: destructor0x244760 + original refusal message
 ->0x38ff88 returns to next top-level tag read
 -> original0xffffffff sentinel / EOF
```

The literal at `0x487a18` says the rejected object is a cylinder. Thus `.4/.2`
are cylinder parameters; they are **not** visual LOD thresholds. Their physical
dimension names/units are not needed or inferred for this visual port. This
does not authorize loading or registering physics objects. In a normal
`complete` filename, the wheel predicate fails and the temporary cylinder is
destroyed while the already loaded visual model remains.

The **25** affected COMPLETE resources end in the original exact sequence:

```text
66 00 00 00 cd cc cc 3e cd cc 4c 3e ff ff ff ff
u32=102       first=.4     second=.2     u32=-1
```

Tata's verified boundary remains offset352800 in352816 bytes. KAMAZ, WOOLDAND
and XTRAIL use tag101, dispatched to the existing convex-auxiliary consumer
`0x3946e0`; their trailer stays opaque in this visual adapter. UFO uses the
already supported sentinel at exact EOF. No collision data is converted.

## Strict reusable adapter and full source inventory

`complete_reader.py` reuses the existing `decode_vehicle` / `decode_scene`
without editing either shared parser. For102, it requires that the proven
recursive tree already ended, exactly16 bytes remain, both floats are finite,
and the last u32 is the original sentinel at exact EOF. Only a private host
parsing view substitutes the delimiter word with101. It then repeats the strict
tree parse, checks that its endpoint is unchanged and restores `Scene.payload`
to the original immutable bytes. Every node, strip, offset, UV, normal, color,
ADC/control bit and material source stays identical. No original file or
payload hash changes. Unsupported visual tags still fail closed.

The regenerated `complete-inventory.json` contains **29/29 supported visual
source trees**, all hashes/provenance, root/conditional mesh counts, material
strings, original texture slots, strip controls, bounds, named/indexed wrappers
and candidate PC compiled draw records. It stores no vertex or face arrays.
The read-only PC corpus has26 `complete.dx` resources. Name-paired comparisons
are candidate source controls; the source digest alone is not a live menu owner.

Known independent controls reproduce:

| Source control | Result in identity local coordinates,0.001 |
|---|---:|
|WOOLDAND COMPLETE visual source|4261 nondegenerate/nonsuppressed faces,17 root meshes|
|PC Forester complete -> WOOLDAND COMPLETE|978/2271 PC source faces matched;517/1152 distinct PC positions|
|PC Forklift complete -> PS2 FORKLIFT COMPLETE|1377/1460 source faces;710/751 positions|
|PC Ufo complete -> PS2 UFO COMPLETE|160/670 source faces;82/344 positions|
|Tata COMPLETE visual source|4620 source faces;tag102 source boundary352800|

The remaining identity-coordinate comparisons find no identical triangles.
That is **not** proof of unrelated models or platform-exclusive geometry.
Body/wheel density, triangulation, vertical offsets and source geometry differ;
some bounds are close while positions differ beyond0.001. No fitted global
transform or larger epsilon is introduced just to raise correspondence.
Cross-platform per-part transform/alignment remains a separate admission gate.

PS2 **FORESTER remains distinct from WOOLDAND**. No PC counterpart is assigned
to PS2 FORESTER, MOONBUGGY or TANK in this audit. The current PC Forester is paired
with WOOLDAND only. These unpaired PS2 models remain possible additional-car
research candidates, not aliases or automatic replacements.

## Hierarchy and wheel/menu constraints

The original source vertex is52 bytes: normal xyz+0, strip-control+12,
color word+16, two source UV pairs+20 and XYZW+36. Existing conversion and ADC
suppression rules remain the authority. Normals and XYZ are model-local; source
to PC/PS2 world transformation is not supplied by tag7 or tag8.

Fresh `0x391d38` instructions verify tag7 registration into model+0x40, storing
the generated named-child option index and authored selector; tag8 retains a
selector wrapper. Neither structure contains a transform matrix in this
grammar. Child order must not be used as active state. Summed authored geometry
is **not** a simultaneous frontend or race polygon budget.

WOOLDAND COMPLETE's17 root meshes contain the supported prototype geometry, but
its authored `crashiny` typo and untagged material must retain generic defaults;
they cannot be silently converted to carshiny. Whole-menu suppression still
requires current PC complete-buffer generations, exact source ranges, complete
draw-set ownership, transforms and menu-lifetime evidence. The adapter removes
the source-format blocker; it does not prove live safe suppression, damage,
wheel transforms or menu rotation.

## Lamps: source state selection now has an original owner

**CONFIRMED_BY_BOTH** for source selectors and static executable writes;
independent live PS2/PC lamp state/GS capture remains **NOT_PERFORMED**.

The original class string `gaSFXBrakeLights` at0x472498 references constructor
0x1a0758 (xref0x1a0764). Its initialization function **0x1a07e0** resolves the
current model's named `blight` option via **0x1d76d0**, retaining the model at
owner+0x18 and option index atowner+0x14. Missing index remains-1. It constructs
the original Broker key from `Controller/` plus the source Egg name.

The update **0x1a08c0** reads that Broker controller through
`0x1e4280 -> 0x1e3820`, then reads the float at `(result+8 pointer)+0x24`.
The actual original instructions compare against float32 word **0x3dcccccd**:

```text
controller field > float32(.1) -> selected blight value2
otherwise                     -> selected blight value1
0x1d77a0 performs bounds-checked current option-array write
```

The writer requires index>=0,index<model option count, value>=0 and
value<=that option's maximum before writing. The named selector is proved;
the exact live Controller owner/field value, update scheduling and runtime
visibility remain unobserved. This is not a PC controller hook implementation.

The original source `blight` wrapper has tag8 alternatives labeled1 and2.
On and glow mesh records are under selector2 even when the *child ordinal*
varies by family; e.g.Tata usessecondchild while WOOLDAND usesfirstchild.
Some off-state shapes sit in root meshes or use different original resource
names, so the four explicit mode3 brake-related records are not a universal
off-light count. `lights-contract.json` preserves the exact hierarchy and
the earlier29-family source hashes without duplicating full geometry.

The material classifier **0x391690** applies post-shader primary-name overrides:

| Original substring, preserved spelling | Final mode | Writes |
|---|---:|---|
|`breaklightsonglow-`|14|+2c=1,+3c=0,+44=.3|
|`breaklightson-`|1|+2c=0,+3c=0,+44=.3|

These are the original `break` spellings. The literal authored shader tokens
`carbrakelight`,`carbrakelights`,`brakelight` have no recognized registered
literal in the canonical ELF and are not silently aliased to carshiny. The
texture-name override works even when the material lacks a shader directive.
The existing source scan contains28 mode1,28 mode14 and4 explicit mode3
brake-related mesh records: these are neither60 lamps nor60 live draws.

## Exact remaining lamp interfaces; no speculative implementation

1. Current live PS2 `Controller/<EggName>` value/owner/lifetime and its relation
   to the braking input, along with actual selected `blight` option.
2. Live selected off/on/glow mesh, frame, texture handles and actual mode14
   packet producer through VU/GIF to GS.
3. Mode14 complete TEX0/TEX1/ALPHA/TEST/ZBUF/PRIM and inherited state/pass order;
   a numeric mode14 is not proof of additive blending or depth-write behavior.
4. Original PC current brake state, corresponding native lamp draw/resource
   owner and exact state restoration boundary.
5. Original lamp texture alpha/UV sampling and controlled reference capture.

Whole-body framebuffer reflection must not blanket glass, rubber, flat paint,
unknown/default materials or these live lamp alternatives. No glow, physics,
private body or PC lamp replacement is implemented by this bounded research.

## Reproduction

Executed commands (from re-general):

```powershell
python ps2-research/pc-port/docs/vehicle-model-port1/ps2-format-lights/audit_complete.py
python ps2-research/pc-port/docs/vehicle-model-port1/ps2-format-lights/lights_contract.py
& ps2-research/data/revalidation1/tooling-venv/Scripts/python.exe ps2-research/pc-port/docs/vehicle-model-port1/ps2-format-lights/verify_bytes.py
python -m unittest discover -s ps2-research/pc-port/docs/vehicle-model-port1/ps2-format-lights -p 'test_*.py' -v
python -m compileall -q ps2-research/pc-port/docs/vehicle-model-port1/ps2-format-lights
git diff --check
```

Focused tests **18/18 PASS**. The source inventory uses existing PackFS reader
and read-only Course SDK. Synthetic/frozen metadata tests require the included
compact JSON plus the existing shared PS2 Python readers; no private game data.
Inventory regeneration requires canonical PS2 corpus and protected PC vehicles;
R5900 verification additionally requires Rabbitizer and the ignored EER export.
The exact read-only headless invocation is in `command-log.md`.
