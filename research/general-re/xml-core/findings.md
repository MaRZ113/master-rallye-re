# XML core

`CONFIRMED_BY_EXE` plus independent retail XML metadata (`CONFIRMED_BY_CORPUS`).
Broker Values are typed conversion records with full Name paths. XML tree nodes,
Broker entries and polymorphic XmlData objects are three different structures.

The architecture is: logical DataGame filename → resource read job → XML tree
→ Game/Broker dispatch → typed temporary manager → reset-or-merge into live
manager. Loader metadata assigns the logical SaveFile and GLOBAL scope. Values
of type XmlFilename then request dependent config files; XmlData delegates to a
registered class factory. That explains how config becomes runtime state without
inventing recursive Broker paths inside every object.

Canonical details: [load-pipeline.md](load-pipeline.md),
[xmldata-factories.md](xmldata-factories.md), [xmlfilename.md](xmlfilename.md).
Save/load-back: [persistence](../persistence/findings.md).

Read-only metadata inventory inspected Game, dev, Editors, Progress, Settings,
vehicles and DefaultOptions XML from `corpora/retail/Data.sma_unpacked/DataGame`.
Game has 22 XmlFilename Value entries. Progress has 184 Values. vehicles has 490.
Derived metadata and source hashes are in [corpus-metadata.json](corpus-metadata.json);
values and embedded proprietary XML were not copied into Git. The inventory
uses ElementTree for inspection and is not an emulator of native acceptance.

Not established: arbitrary XML compatibility, all object class serializers,
byte-identical native round trips, or a complete engine XML schema. The native
ordered-attribute checks must be respected by any future writer.
