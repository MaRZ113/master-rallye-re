# SaveFile: logical load provenance and Game grouping

Retail entry +18 is a pooled string ID. `005FE120` assigns the logical source
filename after typed conversion; merge copies it with the value. It is not a
physical path, scope, write permission or guarantee a loose file exists.

`004D54A0` registers filenames in the manager's deduplicated circular list.
`004D5350` refreshes it from live entries. `004D58F0` assigns an entry SaveFile
**unconditionally**; `004D5400` changes an old group to a new one. Neither is
an implicit revision update. Broker opening registers two sentinel filenames.

`005B16C0` walks registered filenames and excludes `__NO_SAVE`/`__NO_CHANGE`,
then calls the Game serializer for each remaining group. A name registered with
no eligible live values can still participate in the registry, so registry
presence is not proof of a populated source file.

`005FE460` mode 1 compares entry SaveFile to the requested group (case-insensitive)
and also requires Game bit. Modes 2/3 ignore SaveFile and select Options/PlayerState
bits. The Observatory's report preserves exact filename case; it deliberately
does not merge historical observations merely because the engine group compare
ignores case.

The supplied runtime captures show unlock paths assigned PlayerState, while
Progress contains only its remaining cheat-state rows in that group. This is
consistent with override loading assigning source metadata anew. A value's
SaveFile is mutable provenance/category, not immutable original-asset identity.

An additional static counterexample to a universal __NO_SAVE veto: a type-changing
setter resets SaveFile to __NO_SAVE while **retaining existing save bits**. See
[revision/metadata behavior](../broker-core/revision-semantics.md). No such
live mutation was performed as a runtime experiment.
