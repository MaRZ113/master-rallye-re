# Validation and remaining boundaries

Validated on 2026-10-26 in isolated branch `research/gt-sound-bank-lab`.
Original game assets were opened read-only. Private derivatives and native
projects stay under ignored `scratch/gt_sound_lab/`. No game run, gameplay
audio capture or human timbre assessment is claimed.

## Automated and corpus evidence

| Check | Result |
|---|---|
| Source-only synthetic tests | 30 pass: Lab6, JAM5, GT3 twelve, existing GT4 extraction7 |
| GT3 source map | US244 cars,235 ENGINE rows,118 referenced sound numbers; all bank references resolve |
| GT3 complete bank audit | 1,215 banks,8,554 records,8,501 bank-local spans; every frame/loop/terminal/padding checked |
| GT3 alternate databases | EU244 and JP242 rows parse; no short mesh-code inference |
| GT4 source map | 723 cars,384 sound numbers,3,572 numeric banks;6,033 tuning/engine option keys verified |
| GT4 complete numeric decode | All3,572 banks pass full decoder;21,439 band records,21,433 bank-local spans |
| GT4 shared source | roadnoiz.es adds3 ENGN entries;24 INST banks contain107 split entries |
| GT4 INST codec boundary | 93 admitted entries,14 retained unsupported; all24 bank structures readable |
| GT4 bank sharing | 598 duplicate whole-bank hash groups among numeric banks |
| Native byte/architecture checks | GT3:2,576 words; GT4:6,560 words, mapped to original bytes and independently R5900 decoded |
| GUI smoke | Game/vehicle selection, bank inspection/RPM/loops and explicit GT4 band audition verified in in-app browser |
| HTTP/WAV smoke | Both catalogs, GT3 PCM export, WAV hash/rate/channels, foreign Origin/Host rejection pass |
| Source integrity | Full source volume identities recorded; all3,572 GT4 numeric bank hashes freshly revalidated after successful decodes |
| Source hygiene | `git diff --check`, Python compilation and embedded JavaScript syntax checks pass |

GT3 corpus validation is a complete encoded-frame audit, followed by selected
actual PCM exports. GT4 numeric-bank validation actually invokes its decoder
on every referenced entry. Counts refer to entry records or bank-local spans,
not unique real-world recordings. Separate source files can share content.

The Lancer oracle resolves `mits0015/lancer_evo4_wrc_97` to Sound ID22601,
retains its eleven shared ENGINE rows and verifies eight base-engine bands.
The original muffler/turbine default keys and supplied native rule select a
turbo3 candidate. No invented unique-Lancer attribution is made.

Selected GT3 and GT4 nominal/native-pitch exports were reopened as WAVs;
hashes, mono PCM16 shape, frame counts and rates are retained privately. GT4
engine band04 exposes17696 samples and loop `[28,17696)` at rounded21457Hz
under the admitted anchor rule. This is an individual recording, not the mix.

## Private evidence index

- `scratch/gt_sound_lab/source-identities.json`: original CORE/boot/VOL identities.
- `gt4-inventory-final.json`: full numeric/shared/INST inventory, catalog,
  event resolution and cached-decode source revalidation provenance.
- `gt3/catalog-final.json`: complete GT3 audit and default-source associations.
- `gt3/native-event-map-final.json`: exact-build GT3 event bank/voice/leaf pitch.
- `gt3_native/native-cross-check.json`: original segment/Ghidra/Rabbitizer proof.
- `native/native-evidence-final.json`: GT4 original bytes and architecture proof.
- `http-validation.json`: local HTTP/PCM smoke results.
- `browser-final/`: explicit browser-created WAVs and sidecars.

The archive deliberately excludes all those private results, database contents,
native exports, ELF files and audio. `package_gt_sound_lab.py` copies an explicit
source/docs/tests allowlist and generates minimal package init shims, avoiding
the main Workshop package's unrelated imports. Its source manifest records
every delivered file hash. The same synthetic suites run in the isolated
source tree; no original assets or optional native-analysis dependencies are
needed by them.

## Unresolved native/runtime boundaries

1. Exact historical GT4 Beta-asset/Online-CORE pairing. Static direct-program
   resolution is comparative evidence; shift_change's program15 is absent.
2. Complete original driving mix: gain envelopes, producer semantics of all
   throttle/load fields, previous-frame smoothing, Doppler, pan, SPU2 hardware
   interpolation, ADSR/LFO and final relative levels.
3. GT4 BOV state producer and release thresholds. The event/sample route and
   consuming gain scalar are established; its full trigger producer is not.
4. GT4 SE-sequence event dispatch and the14 unsupported INST entries. No
   repaired loop, fallback recording or unsupported acoustic role is guessed.
5. GT3 full per-event driving conditions, complete program/envelope semantics
   and short model-code association such as sb0097. Named-event source and
   leaf pitch recovery do not close these separate boundaries.
6. Subjective timbre, authentic in-game balance and audible PS2 parity remain
   untested. The continuous GT4 turbine2 drivetrain route is sample-driven
   native evidence, not a recording of a race or a universal claim about every
   vehicle/transmission type.

These limits are recorded in the explorer and handoff; they do not prevent
private inspection or deliberate sample adaptation. The original complete GT
audio system is not declared solved.
