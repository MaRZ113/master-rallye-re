# R3 DX writer corpus validation

All operations used the original bytes as an in-memory template. No generated
DX resource was retained in the repository.

| Metric | Result |
|---|---:|
| Vehicle DX resources | 78 |
| Zero-edit byte-identical | 78 |
| Safe single-position validated | 78 |
| Single-position skipped | 0 |
| Failures | 0 |

A single-position pass means the candidate stayed inside the original AABB,
changed only its source 12-byte position record, reparsed successfully, and
preserved all known non-position structures and original diagnostics.
