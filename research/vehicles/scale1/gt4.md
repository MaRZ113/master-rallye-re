# GT4 Lancer continuation and assembly gates

Original inputs remain private under
`D:/Game/GT_Model-Tools/VOL/GT4-Beta_Extracted/extracted/` and retain prior hashes.
The local derived specdb.sqlite corroborates identity: CAR_NAME_american223
`lancer_evo4_wrc_97` → CAR_VARIATION223 Table42:208 → VARIATION208
`mits0015_0`, ModelCode `mits0015`; Generic year1997. Raw DBT was not independently
reparsed. SpecDB dimensions/column names were not used as wheel anchors.

| Source | Shapes decoded | Stored triangles |
| --- | ---: | ---: |
| Menu body | 30/30 | 5350 |
| Race body, all LODs | 93/93 | 8249 |
| Menu wheel | 2/2 | 1074 |
| Race wheel | 10/10 | 220 |

These totals include uninvoked/shadow/effect forms and multiple LODs. They are
not one combined visible car. Four prior body failures and one wheel failure
were packed UV uploads, not proof of missing positions. New decoding handles
signed/unsigned V2-8/V2-16, ROW addition, STMOD1/2 and split primary UV uploads.
Secondary tween UV arrays stay separate; masked/non-contiguous cycles, holes,
overlaps and nonfinite data reject. Header vertex/triangle counts must agree.
Float normals stay unchanged; packed normal words retain unresolved semantics.
VIF arithmetic was cross-checked with primary
[PCSX2 Vif_Unpack code](https://raw.githubusercontent.com/PCSX2/pcsx2/master/pcsx2/Vif_Unpack.cpp).
Integer UV division by4096 remains the existing GT convention, not a proof of
the VU normal-lighting microprogram.

`gt4_commands.py` reads original byte control flow: operands, branches, LODs,
texture-set bindings, matrix scopes and per-draw state. Body model0 has220 menu /
639 race reachable commands. Unknown callbacks stop unless an explicit diagnostic
branch profile is supplied. The editable profile here selects brake-off/day and
skips procedural wheels solely for body diagnostics. MatN names are never a
material classifier. Source PGLU colours/tail words are retained; alpha test,
blend, inverse write mask and depth transitions are conservative. Destination
alpha, unknown texgen/colour and special effects stay unsupported records.

## Native PS2 evidence and build boundary

Local CORE SHA256:
`0cf52c3ad8e9c1ddba55e7538a35dfed1c02cd0e38e5c348bdf80975046617ff`.
PDTools reconstruction recipe passes encrypted CRC, inflated size and SHA512
digest comparison inside the RSA result at exponent81001/big-endian (tool labels
GT4 Online US). Minimal reconstructed ELF preserves segment addresses/bytes;
SHA256 `962523fb4156aefa4e7d255c4937825614e0b99a9a48e94f1c9fcbe7c586c5c0`.

Ghidra12.1.4 Emotion Engine Reloaded `r5900:LE:32:default` was verified available;
Rabbitizer InstrCategory.R5900 independently checks original words/table entries.
REA Windows provider does not support this R5900 target. Initial autoanalysis
timed out; subsequent explicit function exports are targeted, not a complete
executable audit. Project/dumps remain in ignored `scratch/scale1/`.

**This Online CORE is not proven the exact executable paired with the Beta
assets.** Its behavior is cross-build corroboration, not Beta runtime proof.
No PCSX2 visual/runtime investigation occurred.

- `002F3AC0`, table `006F6430`:67 CarModel callbacks;0 reads taillight state,
  7 time-zone. Callbacks11–14 at `002F3BC0` use four runtime wheel rows at+AC,
  stride3C; `002F3F98` consumes XYZ/rotation/dimension terms.
- `002F0B50` / `002F5030`: store/relocate CAR4. `002F1168` returns CarInfo
  through CAR4+10; `002F11D8` reads instance data at+7C in embedded MDLS via+20
  or a runtime override.
- `002EEE58` → `002EF628` → `002FC0D8` configures CarInfo/parameter-provider
  data. Full final transform provenance remains unresolved. Values passed via
  `002F0DC0` / `002F1108` populate dimension-related fields, **not proven XYZ**.
- Original menu CAR4 range `[57C80,637F0)` equals the entire separate
  `wheel/menu/mits0015` byte-for-byte. This proves component association, not
  its world transforms. Four identical origins (~.04495,0,0) are not car anchors.

## Artifacts and unfinished work

Private `scale1/lancer-menu-final`, `lancer-race-final`, `lancer-wheel-menu-final`,
`lancer-wheel-race-final` contain geometry IR and original-command graphs. Menu includes
three packet-local shared-writer DX/DXT probes, with fillers/donor collision;
they are not complete car.dx/complete.dx. Four diagnostic view PNGs exist.
They still use the explicitly labelled legacy YAML RGB route; direct-byte
traces are separately retained and more conservative. Missing wheels/decals in
those previews are not claimed as a finished vehicle or PS2 visual parity.

A real installable Lancer still requires final wheel transforms/dimensions,
packed normals where applicable, external texture bindings, destination-alpha
decal composition and MR material/atlas qualification. Shared wheel/UI helpers
are available but not applied to guessed placement. No Subaru-specific builder
or repairs were copied, and no substitute model is presented as GT4 Lancer.
