# R-BROKER1: Broker core

## Result and boundaries

The retail Broker is a typed, process-wide parameter database backed by a dense
path-ID-indexed vector. The slash hierarchy is a naming/UI convention. Persistence
metadata and scope are separate from the payload. This is `CONFIRMED_BY_EXE`,
using constructors, lookup/setter assembly, typed XML conversion, serializer
filters, and the original Dump consumer. Earlier work already established the
0x1C retail stride and many paths; those are foundations, not new discoveries.

**Phase status: PARTIAL.** Core representation, XML conversion, save filters,
writer and observational frontend are reconstructed. The normal SCENE cleanup
producer and USER scope producers remain unresolved; the new automatic frontend
still needs human runtime validation. The first disposable Options observation
is prepared, but developer Game-save activation is not authorized by this tool.

## Material new conclusions

- Key IDs index slots directly; manager size includes empty `0x0C` holes. A
  lookup can enlarge this storage. It is not a recursive tree search.
- `0x0C` is the empty/unbound entry state, established by construction, reset,
  removal and serializer/Dump exclusion, not a hidden XML payload type.
- The manager's separate linked list is the **SaveFile registry**. Its opener
  insertions are not typed parameter additions. See [manager.md](manager.md).
- SaveFile controls provenance/grouping, scope is another field, and save bits
  select persistence modes. `__NO_SAVE` alone is not a universal serialization
  veto. See [persistence](../persistence/findings.md).
- Revision is local to each entry. Same-value scalar writes need not increment
  it; object replacement and editor acceptance have different rules.
- XmlData has construction/clone/ToXml/FromXml virtual operations. Some runtime
  classes intentionally return no XML tree. A root `CarN` is not a recursively
  enumerable Broker subtree.
- All three pristine demos examined have 0x94 serializer entry stride, versus
  retail 0x1C. Their mode predicates match semantically. See
  [build-evolution.md](../persistence/build-evolution.md).
- Retail generic editor menu Commit/Cancel IDs7/8 dispatch to an immediate
  return; the live Broker value dialog's OK is a different operation. This
  corrects a previous conflation of UI labels with active mutation paths.

## Evidence and reproducibility

Analysis: Ghidra **12.1.4**, the installed ghidra-bridge Python environment and
selective PyGhidra export of isolated scratch projects. Retail used a copied,
previously analyzed program; pristine demos were independently imported with
`analyze=False` and only selected entry points disassembled. No authoritative
EXE/database was modified. Guessed middle-of-function exports and bad-instruction
decompiles were discarded. Decompiler argument counts are provisional where
calling conventions are not typed; branch, field and call facts were checked
against instruction listings. No inferred types were applied to shared projects.

Helper: `tools/scanner/broker_core_evidence.py`. Local, ignored evidence is under
`research-output/general-re/broker-core/`, `xml-core/`, and `persistence/`.
Each batch has a hash-bearing manifest and selective C/assembly files. Export
collections are discovery aids; this documentation contains the accepted model.
Function labels in [function-map.md](function-map.md) are proposed research names.

Existing owner-provided captures `frontend`, `frontend2`, `race-baseline` were
read and their raw/JSON pair hashes validated. They report respectively
6,919 / 6,919 / 7,806 emitted entries, with GLOBAL/SCENE counts 6,864/55,
6,864/55, 6,928/878 and no USER rows. This is prior `CONFIRMED_BY_RUNTIME`
evidence, not a new assistant-run experiment. Capture contents remain ignored.

No process writes, Broker edits, save commands, EXE patches, or gameplay
automation were executed. New frontend behavior is `SOURCE_EVIDENCE` plus
synthetic validation, **AWAITING_HUMAN_RUNTIME_VALIDATION**.

## Navigation

- [Manager](manager.md), [entry layout](entry-layout.md), [paths](path-system.md)
- [Types](types.md), [scope/lifecycle](scope-lifecycle.md), [revision](revision-semantics.md)
- [Editor mutation](editor-mutation-path.md), [unknowns](known-unknowns.md)
- [XML pipeline](../xml-core/findings.md), [persistence](../persistence/findings.md)
- [Human workflow](../../../docs/broker-observatory.md)
