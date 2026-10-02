# R5V-F.2b cook determinism

**Cook A: not run. Cook B: not run.** There are no retail-generated DX hashes
to compare.

The planned comparison uses exactly the same retail candidate, retail
`Data.sma`, three source GXM hashes, authoring GXI copies, and 25 historical
root DXT files. Cook B must start from absent generated DX files in its own
isolated directory; it must not delete or reset anything in the canonical demo
or retail trees.

For `complete.dx`, `car.dx`, and `wheel.dx`, record SHA-256 and semantic DX
summaries for A and B. Byte-identical output is the target. If hashes differ,
produce a binary and semantic diff and explain each changed field before
calling the retail cook reproducible. The isolated `cook-a/` and `cook-b/`
folders are prepared, but currently empty apart from the external validator
report located at the phase root.
