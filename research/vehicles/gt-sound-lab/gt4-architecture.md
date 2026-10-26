# GT4 source architecture

## Evidence scope

Inputs are the unchanged `E:/Games/GT_Model-Tools/VOL/GT4-Beta_Extracted/`
tree. The volume SHA256 is
`a190e2e993c95981a36574447757a858d261d5d81662e576a0e95bf683258e3d`.
CORE.GT4 SHA256 remains
`0cf52c3ad8e9c1ddba55e7538a35dfed1c02cd0e38e5c348bdf80975046617ff`;
the reconstructed supplied CORE is
`962523fb4156aefa4e7d255c4937825614e0b99a9a48e94f1c9fcbe7c586c5c0`.
Its Online-US identity and unproven exact pairing with the extracted assets
remain explicit. Static native interpretation is not observed gameplay.

## Vehicle and tuning association

All 723 GENERIC_CAR labels resolve through original keys to ENGINE rows and
384 sound numbers. There are 3,572 numeric banks in the nine carsound
directories. The resolver uses the raw GTDB Huffman/template reader, not a
label-based ENGINE guess or a derived SQLite association.

| Original field | Qualified layout |
|---|---|
| GENERIC_CAR default parts | 24-byte row, key at0, table36 |
| DEFAULT_PARTS engine | 208-byte row, key at88, table12 |
| ENGINE sound number | 113-byte row, little-endian u16 at24 |
| DEFAULT_PARTS NATUNE | key at96, table13, or explicit -1/-1 |
| DEFAULT_PARTS turbine | key at104, table14; wastegate at turbine+9 |
| DEFAULT_PARTS muffler | key at152, table20; category at muffler+6 |

The original IDI headers establish table IDs. The local PDTools DefaultParts
column list omits intervening fields for this layout: blindly treating
DEFAULT_PARTS+136 as muffler is wrong. That key position belongs to table18
when present; actual MUFFLER.idi identifies table20. Source bytes take priority
over the comparative metadata names.

`CARS/{generic_row:016X}` stores an 8-byte count/reserved header followed by
16-byte row/table/category/padding records. The explorer verifies all 6,033
audio-relevant engine/NATUNE/turbine/muffler keys against original rows and
category bytes. It retains 37 explicit absent-key records. No upgrade is
associated by substring matching.

Original CAR_VARIATION_american keys lead to table42 VARIATIONamerican;
its string references resolve through american_StrDB.sdb to ModelCode.
Repeated physical variation row IDs are preserved, never collapsed into one
dictionary row. This gives the independently recovered `mits0015` model code
for the Lancer oracle, and preserves multiple color variation records.

For Lancer: GENERIC_CAR223 -> DEFAULT_PARTS3128 -> ENGINE1605 ->22601.
Engine22601 remains shared by eleven ENGINE rows. Muffler2289 category3 and
TurbineKit2401 wastegate12 predict `turbo3` from the supplied CORE's equipment
rule. This is a static interpretation of default parts, not a measurement of
current in-game equipment. Available same-ID banks are engine, normal3 and
turbo0..3; absent normal0..2 are reported. normal3 and turbo3 are byte-identical.

## ENGN samples, RPM and sharing

All 3,572 numeric ENGN banks pass the structural and full PCM decoder checks.
They contain 21,439 band records and 21,433 distinct referenced spans within
their banks. A sample may deliberately have multiple RPM/pitch records: five
banks previously rejected as duplicate offsets are now admitted without
changing source bytes. Aliases remain separate band records. Across numeric
banks there are 598 groups of identical whole-bank hashes.

The header has two count/pointer pairs; both are retained. All numeric banks
in this particular corpus use table0 only. A record is16 bytes: signed16
reference/full-volume-min/full-volume-max/gain, uint32 base-SPU-pitch and
uint32 body-relative byte address. The supplied CORE computes pitch from
base pitch * requested control / reference, selects up to two adjacent RPM
entries and applies lookup-table crossfades and gain. See native report for
the actual layer controls; neither normal nor turbo is a proven throttle-off
label or turbo-kit stage number.

Every entry records bank SHA256, source record/file offsets, encoded hash,
sample count and end-exclusive loop bounds. Inspection exposes comparative
native RPM semantics separately from the original words. Anchor duration/rate
is reported only after admitting the exact supplied CORE. WAV rate is rounded
from 48000 * base_pitch /4096; Doppler/global pitch and hardware interpolation
remain outside the audition.

`sound_gt/sound/roadnoiz.es` is an additional shared ENGN bank, controlled by
a separate speed-derived runtime path. Its generic control fields are not
labelled vehicle engine RPM. The inventory also hashes sdvol.dat and vcse.raw
without inventing their layouts.

## Shared INST/JAM and event sounds

Twenty-four sound_gt/sound INST banks have107 split entries. The corrected
decoder admits93; fourteen retain explicit unsupported loop/SSA statuses,
including ten countdown entries. In the main race banks the result is28/31
and14/15 admitted entries. These are per-entry boundaries, not rejected banks.

The important correction to the old audition tool is native SSA scaling:
JAM+0x7c nonzero selects shift3, zero shift4. Both supplied race banks use
shift3, so their sample-unit addresses multiply by8. The new
`gt_sound_jam.py` supersedes the historical fixed-*16 interpretation.
Program presence, split records, raw note/envelope flags and unsupported
records remain visible. A musical-looking byte is not assumed to establish
the final playback pitch.

The 81 GTSE names are retained with tokens and source record offsets. The
supplied native direct path resolves b_off/turbine/turbine2 to bank/program/
first-split identities; the corresponding shift_change program is absent
from this asset bank. See [events-drivetrain.md](events-drivetrain.md).

## Limits

No complete SPU2/IOP mixer, ADSR/LFO, spatial audio, hardware interpolation,
drive capture or PS2 acoustic parity is claimed. A single recording, a nominal
WAV and a static token resolution are three different qualifications.
