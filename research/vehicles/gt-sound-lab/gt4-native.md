# GT4 supplied-CORE sound orchestration

## Identity and evidence boundary

The unchanged supplied encrypted source is now at
`E:/Games/GT_Model-Tools/VOL/GT4-Beta_Extracted/CORE.GT4`, SHA256
`0cf52c3ad8e9c1ddba55e7538a35dfed1c02cd0e38e5c348bdf80975046617ff`.
It matches the previously authenticated reconstructed CORE ELF, SHA256
`962523fb4156aefa4e7d255c4937825614e0b99a9a48e94f1c9fcbe7c586c5c0`.
The fresh analysis uses a private copy of that ELF and existing analysis database
inside this worktree's ignored `scratch/gt_sound_lab/native/` directory.

This is supplied Online-US CORE evidence interpreted alongside the extracted
Beta sound corpus. Their exact historical runtime pairing is **not confirmed**.
No game was run and no PCM was classified by listening. Decompiler output is an
analysis aid, never original source. All native instruction dumps, proprietary
bank data, reconstructed executable and Ghidra database stay private.

REA's available Ghidra provider was checked by the coordinating pass; its Windows
native route does not support this PS2 R5900 ELF. Direct Ghidra 12.1.4 with Emotion
Engine Reloaded, language `r5900:LE:32:default`, successfully processed the copied
project read-only. Rabbitizer 1.16.2 with `InstrCategory.R5900` independently
decoded 6,560 distinct selected instruction words, all mapped back to identical
original ELF bytes. This count is decode/byte coverage, not a claim that every
instruction's semantics was manually audited.

Private evidence: `native-evidence-final.json` (SHA256
`af8af83b49009962136fb121537f395db0972e10f81cb04226b1500beffb8a92`),
`selected-events.json` and the current `*.txt` Ghidra exports in that directory.
Source-only handoff includes scripts, digest gates, tests and these findings.

## Bank selection is exhaust category plus turbo eligibility

| Native VA | ELF file offset | Confirmed use |
|---|---|---|
| `0027E2A8` | `0017F2C0` | Gets base sound number and tuning selector, calls bank loader |
| `00304E68` | `00205E80` | Reads engine record `soundNum` at byte 24 |
| `00304E98` | `00205EB0` | Selector from equipment `+D0` record byte 6; adds 4 if turbo predicate true |
| `00304FA0` | `00205FB8` | Turbo predicate from equipment `+B0` record byte 9, nonzero |
| `00273170` | `00174188` | Loads engine and selected tuning bank separately |

The selector is `stage + (turbo_enabled ? 4 : 0)`. A missing `+D0` record defaults
the stage to zero; a missing `+B0` record makes the turbo predicate false.
The literal pointer table at `00662D68` is, in index order:
`normal0, normal1, normal2, normal3, turbo0, turbo1, turbo2, turbo3`.
The prefixes table selects `motosound` or `carsound` independently.

The serialized equipment order in local PDTools
`PDTools.Structures/PS2/CarEquipments.cs` independently corroborates `+38` Engine,
`+B0` TurbineKit and `+D0` Muffler. Its table metadata labels Muffler byte 6
`category`, and TurbineKit byte 9 `wastegate`. These are comparative field names;
the original instruction loads and offsets are the primary evidence. TurbineKit
`category` does **not** directly select a `turboN` suffix. A category-4 kit does
not imply a nonexistent `turbo4` bank.

The parent pass's original Lancer database decode finds Muffler row 2289, table
20, category byte 3, plus TurbineKit row 2401 with wastegate byte 12. Under this
supplied native selector, default Lancer is a `turbo3/22601` candidate alongside
`engine/22601`. That is static selection evidence, subject to the build-pairing
boundary above. Actual table IDs and DEFAULT_PARTS offsets must come from this
database's IDI metadata, not hardcoded IDs from an older field map.

## Separate engine, tuning and common layers

`00273170` formats both `%s/engine/%05d` and `%s/%s/%05d`. They are loaded into
distinct objects at sound-object `+38` and `+2D8`. `00273290` copies the common
`roadnoiz.es` resource into the object at `+15C`; `00273308` creates playback
controllers for all three. `00273480` updates them independently.

`0027E420` builds these relevant control triplets:

| Control packet offsets | Layer | Observed controls |
|---|---|---|
| `+4C/+50/+54` | base engine | view-dependent gain times dynamic byte `+724`; Doppler; dynamic ushort `+61E` RPM |
| `+58/+5C/+60` | common `roadnoiz.es` | gain and reference value from `00212698`; Doppler |
| `+74/+78/+7C` | selected `normalN/turboN` bank | separate gain times byte `+725`; Doppler; same RPM |

`00212698` computes a speed-squared gain with bounded lookup/interpolation and
produces its own reference value. It is separate from the engine-RPM stream.
The two car-specific banks therefore participate as concurrent native layers;
folder names alone do not establish acceleration/deceleration roles.

This pass does not qualify the producer semantics of every gain byte or fully
reconstruct the original throttle/load envelope. It does establish that a
single renamed WAV cannot reproduce this mixer, and that changing a turbo kit
category alone is not the full sound-bank-selection rule. Existing V-AUDIO1
exact-build RPM-band pitch and crossfade evidence remains applicable to this
same supplied CORE; it is not rerun gameplay validation.

## Corrected JAM sample-address semantics

The earlier `gt4_instrument_audition.py` and the comparative PDTools `*0x10`
assumption are superseded for these GT4 banks by `tools/gt_sound_jam.py`.
Two original functions determine the actual scale:

| Native VA | ELF file offset | Confirmed operation |
|---|---|---|
| `005338C8` | `004348E0` | Bank address shift is 3 if JAM-header word `+7C` is nonzero, else 4 |
| `00533730` | `00434748` | Combines split byte 5 and LE ushort at 6, shifts by bank shift, adds linked body address |
| `00533998` | `004349B0` | Links the bank's SPU body base |

For split bytes `s`, `units=(s[5]<<16)|LE16(s+6)` and
`body_byte_offset=units << shift`. Both `gt4race.ins` and `gt4race2.ins` have
`JAM+7C=FFFFFFFF`, so their address unit is **8 bytes**, not 16. The latter's
`turbine` entry is at body offset 180480, which is valid; the previous offset
360960 fell outside its 195888-byte body because the scale was wrong.

| Bank | SHA256 | Split records | PCM accepted | Loop-policy unsupported |
|---|---|---:|---:|---:|
| gt4race.ins | `54a165aa0d417dd0cfe35f67b6c43c9156660b4d6641ee0886b722a02ec76baf` | 31 | 28 | 3 |
| gt4race2.ins | `b27a2bafe3e428e5ca764e3c99958065d84b22c6c962be09ed85f66631f9b564` | 15 | 14 | 1 |

Remaining unsupported entries are race programs 28/29/30 and race2 program 3.
Their addresses are now in bounds, but their encoded streams contain a loop
start followed by ordinary end flag 1. The existing strict ENGN decoder rejects
this combination. Records and original flags are preserved; this pass does not
declare the source corrupt or invent a repeat endpoint. `SSA outside body`
was not evidence for noise/sentinel synthesis in these selected records.

Nominal WAV rate is still caller-selected. The actual voice consumes base-note,
fine-tuning, ADSR, flags and LFO data (`00533C78`), and game controls alter pitch.
The new inspector does not silently claim that a 24-kHz audition reproduces
original pitch or envelopes.

## Reproduction

From this worktree, run `python -m unittest discover -s tests/synthetic -p
test_gt_sound_jam.py -v`. Five fixture-independent tests pass for native scale
switching, direct routing/gaps, nominal WAV provenance and overwrite refusal,
malformed headers/pointers, and ELF mapping/hash rejection.

`tools/ghidra/GtSoundLab.java` accepts output path followed by address arguments,
`s:literal` searches, `r:address` incoming-reference queries, or
`f:start:end` function ranges. Use the copied private project with headless
`-process core.elf -readOnly -noanalysis`. The script prints language, executable
hash, function boundaries, pseudocode and instruction bytes to the private file.

`gt_sound_native_evidence.py --core PRIVATE_CORE --exports PRIVATE_EXPORTS...
--output NEW_PRIVATE_JSON` verifies the exact CORE hash, four instruction-range
digests, original ELF mappings and export identity, then independently decodes
with Rabbitizer. The available Rabbitizer package is in the original worktree's
`.research-output/vehicles/scale1/python-tools`, compatible with installed
Python 3.11. The source helper retains only lengths/digests for its admission
gates; executable bytes occur only in private diagnostic outputs.
