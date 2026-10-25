# SCALE1-CRASH — single native audio lookup

2026-10-23 · `research/vehicles` · 29 and 30 records remain experimental.
The user confirmed that **both** previous configurations crash loading races,
including stock-only selections. This is separate from Lancer model rendering.

## Exact failure

Four existing logs under `D:/Game/Master Rallye/MRRRenderer/logs/` agree:
`crash-23784.txt`, `crash-19868.txt`, `crash-26032.txt`, `crash-26548.txt`.

| Field | Observed value |
| --- | --- |
| Exception / instruction | `C0000005` / `004AC594` |
| Read address | `0000005E` |
| ECX / ESI | `2` / `2` |
| Relevant stack | `004AC66E`, SDK cave `0068EA89`, `00408FB9` |

Original retail SHA256 is
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
REA/Ghidra and direct PE byte checks identify `004AC660` as the participant
CarID getter, called by the audio constructor at `00408FB4`. It may clobber
volatile ECX/EDX. `004AC594` reads `[ESI+5Ch]` after receiving `this` through
ECX, matching the logged `2+5Ch = 5Eh` failure.

The previous SCALE wrapper called that getter, then tail-jumped the parent
SDK helper for **stock/default** IDs. The parent called the getter again using
destroyed ECX. Added IDs returned earlier, so a test limited to new IDs missed
the bug. This is a global race-audio initialization failure; it is not evidence
that a particular mesh, new CarID or registry allocation size is unsupported.

## Correction

`tools/sdk_capacity_native.py::emit_audio_lookup` chains the qualified parent
helper **once**, then translates only added IDs. Stock and existing addon
results return directly. Participant argument, return value and `ret 4` ABI are
preserved. No crash suppression, validation bypass, new capacity mechanism or
resource/physics change is introduced.

`validate_sdk_capacity_emulation.py` now tests **every physical ID**, participant
slots 0/2/5, using the emitted parent helper and a native-getter mock which
deliberately clobbers ECX=2 and EDX. It rejects an invalid `this` and verifies a
single getter call, donor audio profile and stack cleanup.

Counterfactual replay of the saved old emitter fails for **both** layouts with
`audio getter destroyed this pointer: 0x2`. New code passes 87 cases for 29
records and 90 for 30. Native Broker/getter/string/allocator boundaries are
mocked in this helper test: this is CPU ABI evidence, not live race loading.

## Independent candidates

| Candidate | Location under `.research-output/vehicles/scale1-crash/` | Storage |
| --- | --- | --- |
| 29 | `candidate-29/Launch-SCALE29.cmd` | Existing qualified cave layout |
| 30 | `candidate-30/Launch-SCALE30.cmd` | Existing separate 64 KiB private allocation layout |

Each includes its own matched launcher and runtime. Both preserve the frozen
Subaru V-MESH4.13 and Mercedes plus explicit **stock Navara SDK PROBE canaries**.
They do not include Lancer or the new Lancer damage bridge. Roster plans remain
exactly unchanged from their respective previous SCALE builds. All 290 / 390
immutable resource files match those previous builds; only native audio glue
and its sealed metadata have changed. User options/save state are excluded
from immutable resource comparisons as defined by the existing policy.

Private evidence: `audio-abi-29.json`, `audio-abi-30.json`, candidate-specific
`validation.json`, `regression.json`. Both strict bundle reconstructions and
launcher preflights pass. The 30 allocation self-test passes and rejects an
occupied address. The actual installed approved graphics proxy also passes
launch-environment verification. No game was launched during these checks.
The shared full suite passes 629 tests with one fixture-dependent skip.

## Human test order / remaining unknowns

Close every running game before changing candidates. Use each bundle's own
disposable state; do not copy campaign saves between experimental layouts.

1. Start **29**, select a stock car and load a new Quick Race. This directly
   exercises the formerly broken stock fallback. Repeat another mode/car.
2. Check Subaru and SDK PROBE selections, player/AI participants, Results and
   return/re-entry. Repeat with reflections enabled/disabled.
3. Close the game and repeat independently on **30**, including both probes.
4. If a load still fails, retain the new crash/session logs and exact candidate
   name. Further initialization paths may become visible after this first fault.

Do not infer a supported capacity from this repair: race lifecycle, campaign
progression, persisted competitions, network compatibility and higher counts
remain unqualified. No higher-capacity patch was added. The narrow correction
removes a reproducible failure of both existing layouts; gameplay success must
still be demonstrated by these independent tests.

The original EXE and existing graphics DLL remain byte-identical. No commit,
push, asset distribution, publication or Randomizer integration was performed.
