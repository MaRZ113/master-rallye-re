# Seven-AI T1/T2 crash and duplicate physical CarIDs

## Current verdict

**Crash root cause: UNKNOWN.** The owner reports that seven-AI races have
crashed with a T1/T2 player under restricted T1/T2 policies, while a tested
T3-player setup did not. The published beta documents the limitation, but the
reviewed canonical R-MOD3 inputs contain no exception record tying those exact
scenarios to an EIP, invalid address, or native lifecycle stage. Do not call
pool exhaustion the cause.

**Native pool behavior: CONFIRMED_BY_EXE / STATICALLY_VERIFIED.** The current
Ghidra 12.1.4 exports for exact retail SHA show `FUN_00458090` at `0x00458090`
is called twice from Quick Race setup `FUN_0047B780`. The chooser takes five
32-bit stack arguments and ends in `RET 0x14`. The caller supplies the first
AI slot, count, requested class, and up to two excluded human CarIDs. Its
class cases construct physical-ID candidates; T1 is IDs 0..6, T2 7..13, and
core T3 14..20 with progression-gated IDs 21..24.

For each AI slot, the chooser checks temporary-pool length through
`FUN_004116A0` (`ECX` vector, `EAX` length). If the temporary pool is empty,
it shuffles the saved eligible pool with `FUN_00450580`, copies it back into
the temporary pool, selects and erases one physical ID, then writes that
slot's CarID, record-derived CarClass, and separately chosen DriverID. The
per-slot writers are `0x004ACAF0`, `0x004ACC10`, and `0x004ACCD0`. The chooser
does not clone a participant object or AI controller. `FUN_00458980` owns a
separate driver pool; it uses `ECX` for the pool, a stack output pointer, and
returns its status in `AL` (`RET 4`).

The current F3 design hooks class-policy seams inside `FUN_00458090` but leaves
the physical pool, refill/shuffle, DriverID draw, and per-slot publication
native. The current mode plan and code use the same exact retail image. This
proves that native code has an explicit repeat-after-refill path. It does not
prove that repeated physical IDs are safe through every vehicle/physics,
collision, AI, grid, Results, replay, or teardown path.

## Why the symptom points at, but does not prove, repetition

With a strict T1 policy and a T1 human, the chooser excludes the human's
physical ID. The base candidate pool therefore contains six T1 IDs for seven
AI draws. On draw seven, the temporary pool must be refilled and a previously
used AI CarID can recur. The same arithmetic applies to T2. With a player
outside the restricted class, all seven core IDs remain eligible; seven draws
can complete without refilling. A tested T3-player control is consistent with
that distinction if it used a T1/T2-only AI pool.

This is a falsifiable explanation of the condition boundary, not a crash
diagnosis. The 8-car R-AI2.1 runtime used a mixed, non-repeating roster. The
engine's per-`CarN` identity and dynamic actor/controller ownership are
separate from CarID, but no checked runtime capture proves the duplicate path.

Other live hypotheses include a downstream resource/physics owner that assumes
distinct physical IDs, a duplicate-sensitive UI/result lookup, a race-start
or grid issue that correlates with this roster, or a separate callback/data
condition. Earlier R-MOD callback ABI crashes were independently localized
and fixed; those records do not establish this seven-AI failure's EIP.

## Smallest useful follow-up evidence

Do not run a full factorial matrix. Once an implementation phase is approved,
compare only these controlled Quick Race cases on the same track and candidate:

1. Six AI, strict T1, T1 player.
2. Seven AI, strict T1, T1 player.
3. Seven AI, strict T1, player outside T1.

If necessary, repeat the distinguishing pair for T2. A seven-AI Full-policy
run is a useful no-small-pool control, but it is not needed before the first
three results are interpreted. Preserve the exact INI, candidate hash,
exception code, EIP, exception parameters, registers, stack trace, and any
Broker roster captured before actor construction. Do not add a game hook just
to log speculative state.

Interpretation:

- Crash before the chooser's 7th slot or before CarID publication: inspect the
  callback and candidate-pool inputs first.
- Repeated CarID present, then failure during materialization: inspect whether
  the failing owner keys shared state by physical CarID instead of `CarN`.
- Seven unique IDs on the failing case: reject the pool-exhaustion theory and
  trace the actual failing object/lifecycle.
- Same repeated-ID roster reaches race initialization: capture the first
  failing instruction; do not infer safety from a Broker-only roster.

## Fix options

| Option | Assessment |
|---|---|
| A. Correct native chooser | Keep the stock chooser and fix only an exactly demonstrated bad empty-pool/refill branch. The current bytes already show refill, so no correction is justified yet. Lowest risk if a faulty edge is proven. |
| B. Duplicate-capable allocator | A custom allocator can choose unused class-eligible IDs first and then repeat, while leaving native DriverID selection and per-slot CarN publication intact. It is broader than the current evidence warrants; all class and RNG semantics would need preservation. |
| C. Larger registered pool | Verified addon IDs can increase eligible identities later, but an add-on is neither necessary nor an acceptable prerequisite for stock-only duplicate support. |

**Smallest defensible action:** capture the first failing native instruction for
the narrow controlled comparison. Do not add ID aliases, cross-class fallback,
new Start vetoes, or a replacement pool before that evidence exists.

**Status:** native repeat path `CONFIRMED_BY_EXE`; release symptom
`HUMAN_RUNTIME_OBSERVATION`; causal link `UNKNOWN`. Confidence is high in the
static control flow and low in any specific crash cause.
