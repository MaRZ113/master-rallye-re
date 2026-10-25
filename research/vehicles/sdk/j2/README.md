# R5V-J.2 runtime evidence and Vehicle Select re-entry fix

**FINAL STATUS: FULL PASS / CLOSED.** The owner tested the exact corrected
reverse-mapper candidate and confirmed that Vehicle Select re-entry now
restores ID27. This later owner report does not add or imply a Broker capture;
see [final closeout](closeout-2026-10-09.md).

J.2's supplied 2026-10-09 runtime batch remains valid: it confirms the
two-addon SplitScreen race, Rallye Cup roster reuse, Master Rallye fresh-process
roster persistence, and the hardened live Dump walker. The owner separately
qualified the corrected re-entry candidate; no new capture was supplied.

## Re-entry root cause

The stack-ABI candidate that first stopped the Vehicle Select crash was
human-tested: the screen opens and ID26 restores, but ID27 still returns as
Navara. Static decoding of the exact effective J.2 native mapper found why.
The ID27 reverse-map arm sets class T2 and stores ordinal 7 into the T1
per-class slot (`this+0x14`), while T2 uses `this+0x18`. The constructor's
existing publisher then sees T2/local0 and the forward map selects stock ID7.

The new `root-cause-candidate` changes only that mapper displacement from
`0x14` to `0x18`; the 86-byte ABI-correct publisher is unchanged. The verified
J.1 parent remains byte-for-byte intact on disk at 246 operations. The
derived J.2 composite has 248 operations and the same 243-resource inventory.
Static tests prove the new reverse/forward native mapping and reject the old
encoding. The corrected candidate was later confirmed by the owner in human
runtime. The earlier static-only test records below remain historical
generation-time evidence; they are not rewritten as runtime captures.

## Candidate

Use only:

```text
.research-output/vehicles/sdk/j2-reentry/root-cause-candidate/
  mr-runtime-launcher.exe
  launcher-build.json
  bundle/
```

| Artifact | SHA256 |
|---|---|
| Pristine retail `MRallye.exe` | `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` |
| Launcher | `1fb190ae85d2b7b119576a650e4723abb1130ef4bbdee6d353357087e3de66c7` |
| J.0 addon plan | `357d3cf10f32b63af27d28c23a858197d7eedbd0d7ef79e4deb2a63a6b170989` |
| Native patch manifest | `162de9762c070fd970731da030f03150b303ecf2f8886bd4f25ca357b9129f11` |
| Native operation table | `44c139de5b211947857bcb4e70ac84a6b9f1adc23cc9b0fe2a520978a5282f5a` |
| Reconstructed reference image | `2f3b1d95d05c997bb13d6a8e235327098e344b75b46d0432c4a3a7ecf289ab64` |
| 86-byte constructor publisher | `f39f33838e0e7d3d276fbec03af0439c6c36a4807224ebe8cfc7ce14e70324ee` |

The original EXE is never written. The candidate remains
`runtime_qualified=false`. Follow the [root-cause retest](root-cause/human-retest.md)
for a short same-player ID27/ID26/stock ID7 check. The earlier crash candidate
and the stack-only candidate are retained as historical research output.

## Evidence and validation

The raw evidence records and bundle provenance remain in
[`runtime-evidence.md`](runtime-evidence.md) and
[`bundle-audit.md`](bundle-audit.md). The static diagnosis is
[`root-cause-2026-10-09.md`](root-cause-2026-10-09.md); the exact commands and
current results are in [`root-cause/validation.md`](root-cause/validation.md).
The final owner report and J.3 preparation boundary are recorded in
[`closeout-2026-10-09.md`](closeout-2026-10-09.md) and
[`../j3/plan.md`](../j3/plan.md). Earlier test and candidate files retain their
historical generation-time contents.
