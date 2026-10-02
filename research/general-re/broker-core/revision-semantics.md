# Per-entry revision

`CONFIRMED_BY_EXE`: +0x10 is uint32, initialized/reset to zero. It is neither a
process-wide monotonically increasing change serial nor proof of pending disk IO.

| Path | Rule recovered |
|---|---|
| Bool `004DDC60`, Float `004DDCD0`, Int `004DDD50` | same-type equal-value write preserves revision; unequal write increments |
| XmlFilename `004DDDC0`, String `004DE0D0` | interned ID equality avoids increment; changed ID increments |
| MarkerListName `004DDE40` | same interned ID preserves revision |
| Matrix `004DDEC0`, vectors `004DE260/004DE300/004DE3B0` | compare numeric components; increment/copy only if different |
| StringList `004DE1C0` | free old list, take replacement ownership, always increment (initial 0→1) |
| type replacement | release payload, reset revision/scope/SaveFile, initialize type; existing save bits are retained |
| XmlData `004DE480` | deletes prior owned object; replacement increments, including initial 0→1 |
| copy `004DEAA0` | copies revision verbatim with other metadata |
| explicit setter `004D5DF0` | assigns revision directly |
| broker edit acceptance `0065F170` | typed write, then explicitly assigns remembered revision+1 |
| scope/flags/SaveFile setters | no intrinsic revision increment |

Scalar increment sites use ordinary 32-bit arithmetic; no saturation/overflow
guard was observed. Float equality follows the compiled numeric comparison,
not the equality of Dump's printed decimal strings. Matrix/vector component
checks and StringList's unconditional replacement were separately decompiled and
checked against assembly; they are not generalized from the scalar result.
Every caller's forced-revision convention and all nonfinite-number corner cases
are outside the recovered common rule.

Type-changing setters call `004DE7B0`, which destroys payload only, then assign
the new tag, revision, scope and SaveFile. They do **not** clear entry +0x0C.
Construction and explicit reset `004DDC20` do clear the low three bits. This
distinction supplies a concrete path where a value can have __NO_SAVE metadata
while retaining an Options/PlayerState flag from its earlier type. The generic
mode filter still selects by that bit; sentinel spelling alone is not protection.

Reload constructs temporary typed entries and copies their loader-generated
revisions; the XML does not preserve the previous live counter. Thus a revision
decrease across reload is not evidence of an older save being selected.

The Observatory defaults to keeping revision-only changes. `--ignore-revision-only`
removes a diff event only if revision is its **sole** changed field; no path-based
noise blacklist is installed and value/metadata changes are retained.
