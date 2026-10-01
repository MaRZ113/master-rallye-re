# Conservative structure summary

This is an evidence table for partial Ghidra data types. Fields remain neutral unless a read/write or diagnostic operation supports a stronger label. The same layout is not assumed in earlier builds unless separately verified.

## Retail broker entry candidate

**Type to add to the isolated retail Ghidra project:** `BrokerEntry_Partial_0x1C`

| Offset | Size | Proposed field | Evidence | Confidence |
|---:|---:|---|---|---|
| `0x00` | 4 | `key_index_candidate` | Type accessors copy the requested index/key into entry word 0; exact mapping to string intern ID remains unverified. | MEDIUM |
| `0x04` | 4 | `value_storage_pointer_candidate` | Broker dump dereferences this word as Bool/Float/Int; non-scalar cases call typed helpers on the same storage. | HIGH for pointer-like use; exact ownership unknown |
| `0x08` | 4 | `type_tag` | Diagnostic and getters compare this word against Bool=0, Float=1, Int=2, Matrix=3, String=4, other observed categories. | HIGH |
| `0x0C` | 4 | `save_flags` | Diagnostic checks bits 0, 1, 2 and labels the columns Save S/O/PS. Mapping from individual bit to label is inferred from flag masks and log argument order; verify before renaming. | MEDIUM |
| `0x10` | 4 | `revision` | Diagnostic prints this word as `Rev %d`. | HIGH |
| `0x14` | 4 | `scope_tag` | Diagnostic maps 0 to GLOBAL, 1 to SCENE and other values to a formatted category. | HIGH for observed mapping |
| `0x18` | 4 | `unknown_18` | No reliable semantic interpretation assigned in this pass. | UNKNOWN |

The diagnostic iterates a collection with 0x1c stride and prints size/capacity. Typed getters and setters also calculate entry addresses with `index * 0x1c`. This supports the record size independently. The structure is **retail-only** for now because the complete field-offset evidence was collected from retail; do not automatically apply it to earlier programs.

The collection object returned by `004D8EC0` is represented by global candidate `DAT_006F9410`; its begin/end/capacity and list fields align with the collection walk in `00601D00`. It is a candidate shared broker instance, not a claim that scene/user scopes use the same global object.

## Other recurring objects

- Resource stream objects and the archive/index manager are partially identified by constructors and `CreateFileA`/archive behavior, but no structure is proposed yet: ownership, handle fields, and lifetime are not fully established.
- Vehicle registry record shape and class capacities are already documented by R5V research; R-EXE1 does not replace or broaden that existing structure claim.
- Course marker/split structures remain as previously documented. No new route state structure is proposed from string names alone.

## Ghidra project mutation

`AddRExe1RetailTypes.java` adds the broker candidate as an unreferenced datatype in the isolated ignored `research-output/r-exe1/ghidra-projects/MRallye_retail` project. It does not change executable bytes or define fields over guessed binary addresses. Raw Ghidra databases are not committed.
