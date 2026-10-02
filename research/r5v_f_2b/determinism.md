# R5V-F.2b cook determinism

**Cook A: partial.** The retail Cook A produced and validated `complete.dx`
(SHA-256 is in `complete-cook.md`). `car.dx` and `wheel.dx` have not been
cooked, and Cook B has not been run. There is no complete A/B set to compare.

The planned comparison uses exactly the same retail candidate, retail
`Data.sma`, three source GXM hashes, authoring GXI copies, and 25 historical
root DXT files. Cook B must start from absent generated DX files in its own
isolated directory; it must not delete or reset anything in the canonical demo
or retail trees.

For `complete.dx`, `car.dx`, and `wheel.dx`, record SHA-256 and semantic DX
summaries for A and B. Byte-identical output is the target. If hashes differ,
produce a binary and semantic diff and explain each changed field before
calling the retail cook reproducible. The isolated `cook-a/` folder now
contains the human-captured complete cook log and output; `cook-b/` remains
unused until all three Cook A roles pass.
