# Path and key system

`CONFIRMED_BY_EXE`: `004D44F0` creates the string-pool manager at `006F93D4`.
`004D4460` interns text: hash lookup `004D4B30`, collision-chain exact byte
comparison, allocation of a record with text at +8, then `004D4D00` registers a
sequential numeric ID. `004D4CD0` resolves ID→record; `004D0570` resolves text.

IDs are **not hashes**. Hashes locate candidate strings; equality resolves
collisions. The pool comparison is case-sensitive, with no slash normalization
in the interner. `Vehicles/X` and `vehicles/X` can receive different IDs.
File constructors normalize their own slash spelling; that is a separate layer.

The Broker's key lookup then indexes the dense vector using that ID. Slash
segments are not tree nodes. Editor `00660480` reconstructs a selected full
path from UI tree items; `0065F9A0/0065FA20` populate the visual hierarchy.
Typed getters check the tag and return type defaults on mismatch; they do not
convert every value to a string or dynamically traverse child nodes.

Several **filename-group/UI scans** compare resolved text with `_stricmp`
`005D1660`, including SaveFile deduplication and Game save filtering. Those
comparisons do not establish case-insensitive Broker path identity.

No transactional namespace, wildcard lookup grammar or generic recursive
XmlData child enumeration was recovered. Prefixes in Observatory presets are
offline filters, not engine lookup syntax.
