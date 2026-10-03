# Exact controlled candidate

Type: **EXE PATCH**, after the data/Broker-init seam audit. This is a 55-byte
guarded selector in existing executable padding, not a general injection framework.
Only pristine retail is a supported source. The convenience widescreen-freeze
image is neither modified nor accepted by this builder.

| Property | Value |
|---|---|
| Source size/hash | 3,121,214 bytes; `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` |
| Candidate size/hash | 3,121,214 bytes; `985cef18ada36dd4f17979e671c6ef1dd9647fa82903cee886156ecac4ed73f3` |
| Chosen-ID seam | VA `0x458428`, file `0x58428`, five-byte MOV/PUSH replaced by JMP |
| Selector | VA `0x68E300`, file `0x28E300`, 55 originally zero bytes |
| Header | File `0x218`, .text VirtualSize `0x28D294 -> 0x28D337` |
| Preserved allocation | Same section/raw/image size and aligned executable page count; no participant allocation changes |
| Guards | ESI=1; retained chooser arguments firstAI=1, count=3, requestedClass=2 |
| Change | [entry ESP+0x14] chosen ID becomes0; stock class setter derives0 |
| Resume | Replay original MOV/PUSH; JMP `0x45842D` |

The pristine declared .text ends at `0x68E294`; selector padding lies in the
same existing last raw/aligned page. Input hash, PE mapping and original bytes
are checked independently. A scan of all source bytes found no four-byte literal
addresses into the selector's55-byte range; this is supporting evidence, not an
exhaustive indirect-target proof. No section flags or relocation entries change.
The inverse verifier restores the three ranges and requires exact pristine SHA.

## Semantic preservation

The hook runs after RNG, used/remaining vehicle pools and driver selection.
It changes the local used by **both** CarID and registry-derived CarClass setters.
It does not touch driver local+0x18, other arguments, pool state or control IDs.
PUSHFD/POPFD protects flags; displaced MOV/PUSH retains EAX/ESP effects.

Guards deliberately do not read the overwritten exclusion argument slots
([participant structure](participant-structure.md)). The candidate activates
for one-human four-car T3 Quick Race, regardless of the stock T3 player's ID.
The **controlled human proof requires ID14**, and the oracle rejects any other
player. This is not an ID14-only machine-code guard or arbitrary-class support.

The course, mode, rules, difficulty, ghost setting, player path and NumCars
remain the stock frontend selections. No Car4, allocation/loop-bound change,
asset overlay, registry expansion, bounds-check removal or canary is involved.

## Reproduction and restore

Run from the main checkout; generated paths must stay under its ignored output:

```powershell
python tools/r_ai1_mixed_class.py build ../corpora/retail/MRallye.exe .research-output/r-ai1/human-candidate/MRallye.exe
python tools/r_ai1_mixed_class.py verify .research-output/r-ai1/human-candidate/MRallye.exe
```

The builder refuses an existing output/manifest; use another ignored subfolder
to reproduce without overwriting. It emits the candidate hash and adjacent
`MRallye.manifest.json`, reproduced in [patch-plan.json](patch-plan.json) as a
small patch description. The original EXE remains untouched. Restore an isolated
test installation by replacing its candidate with a verified pristine copy
(source hash above); never overwrite the protected corpus source.

## Exact Observatory research profile

The supplied portable distribution is0.1.0-beta and pristine-only. The local
`tools/r_ai1_observe.py` adapter hashes its four Python implementations against
fixed audited digests before import, verifies the candidate plus inverse
manifest, then selects **only the fixed candidate hash** in its capture/command
gates. Retail image size/base and debug-sink/command RVAs are unchanged by the
three patch ranges. Original basename/size/process/file gates remain.

External Observatory files remain unchanged; no external bytecode is written.
Research configuration/captures/launchers are confined to this main checkout's
ignored output. It reuses existing read-only process capture and verified native
window commands; no WriteProcessMemory or new Broker mutation is added.
No force/allow-any or unknown-build option exists. Changed vendor files fail
closed until separately audited. The fixed vendor digests are in the adapter.
