# Display identity and test unlock

## Display name

At `0x4819B0`, the frontend computes absolute vehicle ID into EDI, fetches the
registry, and calls the unlock lookup. The selected absolute ID remains EDI for
record stats, preview, and resource lookup. The two localization calls for
groups `0x33` and `0x34` use EDI as their selector (`PUSH EDI` at `0x481A10`
and `0x481A4D`).

The candidate hook at `0x4819BD` saves `EBX=EDI`, changes EBX to 0 only when
EDI=26, calls the unchanged registry getter, then resumes at `0x4819C4`. Only
those two localization selector pushes are changed to `PUSH EBX`. Later code
reuses EBX for the model-name switch. ID26 therefore keeps record ID26 for
preview/stats while showing ID0's existing display/localization identity:
`TOMMEK DIRTBEAST`.

## Unlock

Retail `0x45A150` checks the ID against 25 before indexing its 26-entry jump
table. The candidate does not extend that table. At the narrow Vehicle Select
call site `0x4819CE`, it calls a wrapper which:

1. calls the original unlock function with the same record pointer;
2. restores ECX after the original call;
3. returns true only when the selected record's ID field is 26;
4. otherwise preserves the original AL result.

The established ID25 test profile is retained using the same four-byte
case-25 test override from the prior runtime candidate. This is a test access
policy only; it does not add campaign unlock/save semantics.
