# Synthetic fixtures

Only hand-authored/generated data belongs here. Original Master Rallye bytes
must never be copied into test fixtures.

`test_library.py` builds minimal DX/DXT streams in temporary directories and
contains 22 behavioral tests covering:

- tag-2 draws, tag-7 groups, and tag-8 children;
- local-to-global addressing and winding;
- zero/multiple UV sets and ordered texture slots;
- absent/ambiguous sidecars and missing textures;
- malformed strings, unknown tags, truncation, and unreasonable counts;
- absent, truncated, matching, and mismatching global index tables;
- opaque and recognized 56-byte trailing sections;
- unused/shared vertex-range diagnostics without grammar rejection;
- synthetic glTF structure;
- independent BGRA channels, stored row order, PNG row conversion, and UV V
  transforms;
- archive-root filtering in the R0 inventory scanner.

Run with:

```powershell
py -3 -m unittest discover -s tests\synthetic -v
```
