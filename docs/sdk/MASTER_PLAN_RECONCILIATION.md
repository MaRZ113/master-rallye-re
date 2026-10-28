# Master Plan v6.7 — full-history reconciliation

28 October 2026. Baseline: clean `research/vehicles`,
`f2714b1d50c5af18bdc4081010317fe3e4632922`. This is a document-restoration
check, not new model, preview, Windows or gameplay validation.

## Source documents and retained bytes

| Input / result | Bytes | SHA256 |
|---|---:|---|
| Original attached `master_rallye_vehicle_sdk_master_plan_v6_7.md` | 290052 | `98029f1cfa00525ba985d6809c13407da26406bf42e938f3e0eab368ce749a5c` |
| Baseline `MASTER_PLAN.md`, canonical Git blob at `f2714b1` | 252911 | `aec1129b19fdacf56cc5786a879b20dad52f3aaf329bd6662c8e4d895523c5d8` |
| Baseline Windows working file, before reconciliation | 254561 | `cb72e3981616da9e0caa35af9be18eb16d81ca3cf074e7fdb4f8f8debc71303b` |
| Reconciled `MASTER_PLAN.md`, before later pilot status additions | 293151 | `ee8ca108a952269ef028daf9e90a3d05989d3943cf829afcc5f09d5ba4150001` |

The attachment was read from the owner's Downloads path, not reconstructed from
chat or a source-review ZIP. Its complete original LF bytes are retained at
[`retained/master_rallye_vehicle_sdk_master_plan_v6_7.md`](retained/master_rallye_vehicle_sdk_master_plan_v6_7.md).
That file matches the original attachment byte-for-byte. The complete same
290052-byte attachment is also the exact prefix of the reconciled
[`MASTER_PLAN.md`](MASTER_PLAN.md), once, with no inserted edits or newline
conversion inside it.

The former working file used1650 CRLF line endings. Replacing only CRLF with LF
proved it equal to the baseline Git blob; no uncommitted plan edits were lost.
Repository checkpoints were retained from the canonical Git blob, with its exact
LF bytes. This distinguishes committed content from Windows checkout encoding.
Two narrowly scoped `.gitattributes` entries enforce LF for `MASTER_PLAN.md`
and the retained attachment despite this repository's `core.autocrlf=true`;
future checkouts therefore preserve the attachment's exact byte identity.

## Correspondence and merge decision

Comparison of full content found that the existing plan's shared history was
already present once inside the attachment. The original repository document
decomposes exactly into these three byte strings:

| Baseline segment | Bytes / SHA256 | Retention |
|---|---|---|
| Source Garage audit checkpoint, before `# Master Rallye Vehicle SDK` | 1248 / `9c580e19285d3a828eec4ece8af4e1911c11ee76ef16f886eb93faa2d6d95228` | Exact repository-only appendix block, once |
| Shared history, beginning at that heading and ending immediately before the GT Garage implementation heading | 250645 / `e28d1f4b6dfbe768dd70ad154d6688ce47b4f1da3a174b38a0076e1198f86500` | Exact contiguous bytes already in attached v6.7, once |
| GT Garage implementation checkpoint, beginning `## Implementation status — GT Garage Lab, 28 October 2026` | 1018 / `c2681062ab88ad37056f1886f03035c8922f6d3e7d347ce186f1bb28ebffe2d3` | Exact repository-only appendix block, once |

Therefore the complete previous repository document was **not** appended again.
The reconciled file consists of the complete authoritative attachment plus a
short explanatory appendix and only the two repository-only checkpoint blocks.
All three original segments are retained exactly once; all original baseline
lines are present. This preserves actual repository evidence while restoring
the previously omitted roadmap addenda.

| Restored complete section | Attachment line | Reconciled plan line |
|---|---:|---:|
| v6.3 Cross-Game Rally & Off-Road Heritage | 1710 | 1710 |
| v6.4 Cross-Game Source Recon / Donor Tool Audit | 1769 | 1769 |
| v6.5 Source Garage: Four Additional Game Families | 1842 | 1842 |

Each section retains the attachment's complete following text through the next
section/end, not merely its heading or a short replacement status note. Paris-
Dakar Pajero, Michelin RAV4/Mégane, later donor research and their separate
personal/historical priority remain in this complete retained roadmap.

The appendix explicitly labels the old `Stop for audit review` and GT Garage
checkpoints as historical. The current owner request approves one bounded Evo2
neutral-scene/preview pilot; embedded older tasks do not independently authorize
Paris-Dakar RE, other importers, MR-native authoring, roster allocation or
publication. Source Garage research priorities and protected accepted projects
remain intact.

## Verification and reproduction

The restoration check verified exact attachment retention/prefix, all three
baseline segment identities and single occurrences, zero absent baseline lines,
and the restored section positions above. Machine-readable results are private:
`.research-output/vehicles/source-garage-evo2/master-plan-reconciliation.json`.
`git diff --check` passes. The immutable attachment bytes are preserved rather
than silently reformatted.

The central checks can be repeated without the original Downloads location:

```python
from pathlib import Path
import hashlib, subprocess

root = Path.cwd()  # repository root
old = subprocess.check_output(['git', 'show', 'f2714b1:docs/sdk/MASTER_PLAN.md'])
attached = (root / 'docs/sdk/retained/master_rallye_vehicle_sdk_master_plan_v6_7.md').read_bytes()
current = (root / 'docs/sdk/MASTER_PLAN.md').read_bytes()
assert hashlib.sha256(attached).hexdigest() == '98029f1cfa00525ba985d6809c13407da26406bf42e938f3e0eab368ce749a5c'
assert current.startswith(attached) and current.count(attached) == 1
start = old.index(b'# Master Rallye Vehicle SDK')
end = old.index('## Implementation status — GT Garage Lab, 28 October 2026'.encode())
for segment in (old[:start], old[start:end], old[end:]):
    assert current.count(segment) == 1
assert all(line in current for line in old.splitlines(keepends=True))
```

No product tests were needed for this document-only correction. No other source
code, donor installation, original MR resource or accepted vehicle was changed
by reconciliation. Later pilot implementation and its tests are documented
separately; the results above must not be presented as a new full-suite run.


## v6.8 retention checkpoint — first native 4Runner pilot

The complete owner v6.8 attachment is303112 bytes, SHA256
`3de8dd7460d54f95f31e57d84504a8787fa13b4669f060d187266ae4b9805058`.
It contains the entire295599-byte current repository plan once at offset0,
then adds the v6.8 planning section. Its exact bytes are retained in
`retained/master_rallye_vehicle_sdk_master_plan_v6_8.md` and as the complete
prefix of MASTER_PLAN.md. The current native-pilot implementation checkpoint
is appended after that prefix. Both retained versions have explicit LF rules
in .gitattributes, preventing Windows checkout normalization from changing
attachment hashes. Historical v6.3-v6.5 and repository checkpoints remain full.


## Complete v7.0 reconciliation, 28 October2026

The complete322686-byte supplied v7.0 is retained byte-for-byte in retained/master_rallye_vehicle_sdk_master_plan_v7_0.md and forms the canonical plan prefix. It includes the complete303112-byte v6.8 plus missing v6.9 and v7.0 owner reviews. The4895-byte unique old repository implementation suffix is appended verbatim as historical checkpoints; no history is summarized or discarded. Machine proof is in vehicles/4runner-stable/master-plan-reconciliation.json under ignored private evidence.
