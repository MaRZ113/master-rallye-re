# R5V-H validation — Stage 1 preparation

## Baseline

Starting commit: `596e705` (`research: close R5V-G.2 and generalize stock audio profiles`).
Branch: `research/vehicles`.

* Synthetic suite with `PYTHONPATH=src`: 291 passed, 0 failed, 0 skipped.
* `python -m compileall src tools tests`: PASS.
* `git diff --check`: PASS.

The first local invocation omitted `PYTHONPATH=src`; 260 tests passed and two
modules failed import because `master_rallye` was not on the import path. The
documented baseline invocation with the source path then passed all 291 tests.

## Static and binary validation

* Pristine retail SHA256: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
* Deterministic G.1 intermediate: `722d1a59a9c11cb0c181751c17674e6a04587e2c7b3b8c225c2e93754a438da7`.
* Deterministic G.2 profile-0 intermediate: `636422d0a21b5f75abd3d6233ab0fcbae26cb0dce79c1a8d40d60ad2e8ca488f`.
* H forced candidate: `688653245b916ae7aae2a8e22fd47e76963f3afb1c23936b47b57bb40c76f0c5`, 3,121,214 bytes.
* H hook: VA `0x00458428`, file offset `0x58428`, replaces five bytes
  `8B44241450` with a relative jump to `0x0068E690`.
* H stub: VA `0x0068E690`, file offset `0x28E690`, size 95 bytes, exclusive
  end `0x0068E6EF`. It is one byte after the 22-byte G.2 wrapper ending at
  `0x0068E68F`; it remains inside `.text` raw bytes and ends before `.rdata`
  at RVA `0x28F000`.
* `.text` VirtualSize at file offset `0x218`: retail `0x28D294`; G.1
  `0x28D679`; G.2 `0x28D68F`; H `0x28D6EF`.
* The return guard is the one-human Quick Race call return at `0x0047B973`.
  Other required guard values are Car1/ESI=1, end slot/EBP=4, class=0,
  player CarID=0, and second excluded ID=-1.
* Only the final selected CarID local is changed. DriverID is already chosen
  and remains untouched; native code publishes CarID and derives CarClass.
* G.2 audio selector hook and profile0 wrapper remain present in the H
  candidate. Participant CarID is still the input to that wrapper.
* Candidate builder verification: PASS; exact existing output and manifest
  reproduce from pristine retail.
* Latest Ghidra 12.1.4 headless import/analysis: PASS. The candidate hook at
  `0x00458428` decodes as `JMP 0x0068E690`; the stub has six expected guards,
  writes `0x1A` only to `[ESP+0x14]` on the match path, replays the original
  `MOV/PUSH`, and jumps back to `0x0045842D`. The first post-script formatting
  attempt failed before producing output; the corrected script completed
  successfully. The generated Ghidra project remains temporary and is not
  evidence committed as a database.

The code cave/payload and exact original/replacement bytes are recorded in the
ignored generated manifest at
`.research-output/vehicles/ai/forced-id26-proof/MRallye.manifest.json`; the
patched executable is not committed.

## Tests added for the H preparation

The forced-stub test interpreter executes the emitted x86 instruction subset
and checks positive and negative guards, branches, preserved DriverID, replayed
MOV/PUSH, and the resume target. This is static instruction-level emulation;
it is not execution inside Master Rallye and does not replace Ghidra/runtime
validation. Two new Broker-checker tests ensure missing PlayerType or player
CarID evidence remains `UNKNOWN` rather than becoming a false failure/pass.

The Broker checker tests use arbitrary PlayerType values and compare the target
AI with Car2/Car3 while distinguishing Car0. Missing PlayerType, player CarID,
or requested candidate-hash evidence remains `UNKNOWN`/incomplete. The checker
does not hardcode an unverified numeric AI enum and never reports a human
runtime pass.

## Final local verification

* Synthetic suite: **307 passed, 0 failed, 0 skipped**.
* Focused forced-candidate tests: **7 passed**.
* Focused Broker-checker tests: **9 passed**.
* `python -m compileall src tools tests`: PASS.
* Forced candidate builder `--verify-existing`: PASS; output hash and size
  match the values above.
* Latest Ghidra 12.1.4 candidate disassembly: PASS.
* `git diff --cached --check`: PASS.

## Human runtime status

**NOT TESTED.** No H runtime capture is present. Mercedes AI visual identity,
controller behavior, physics, collision, damage, race progression, results,
and audio remain open until the exact candidate is tested by a human.
