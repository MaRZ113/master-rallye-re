# Material and texture-reference evidence: rev131 versus rev135

This report separates observed texture-name references from unresolved draw
prefix state. The available Trooper sample does not expose a proven standalone
material table.

## What is byte-identical

For each of the 22 `car`, 20 `complete`, and 5 `wheel` mapped draw records:

- the length-prefixed texture-reference suffix is byte-identical between
  rev131 and rev135;
- the ordered three-slot name tuple is preserved, including `Null` placeholders;
- draw-to-texture-name association is preserved under the verified record map.

This confirms reference-string preservation in these pairs. It does not prove
that all renderer/material parameters have unchanged meaning.

## What changes

Each rev135 record has a 24-byte parsed prefix in place of the 11-byte opaque
rev131 prefix. The 13-byte record growth is uniform. Rev135 exposes raw flags
and parser-named `unknown_*` values there; the old bytes cannot yet be
reliably decoded into equivalent fields. This region may include material or
draw state, but that interpretation is **UNKNOWN** until executable or broader
controlled-output evidence supports it.

The exact old/new prefix bytes, per-field values exposed by the current reader,
and all suffix comparisons are in `dx-binary-diff.json`. No names are assigned
to the unknown legacy values, and no claim is made that the full rev135
material meaning can be reconstructed from the rev131 record.

## Paired DXT control

Only `black-tga.dxt` was supplied as a paired texture output. Both files are
1,044 bytes and byte-identical (SHA256
`c8af53e3c1ea06c42178b3e1988dff0b3c64f150b722cba6bdd0450dc1357f82`). The
header, dimensions (16×16), stored CRC32 (`0x6B3FE5F6`), and 1,024-byte pixel
payload are equal. `Black-tga.gxi` is also byte-identical across the supplied
source folders. With no DXT delta in this one pair, deeper texture
investigation is not warranted in this phase.

## Conclusion

Texture-reference names are preserved exactly. Full material serialization
equivalence is **UNRESOLVED** because the old opaque prefix has not been mapped
to the rev135 prefix, and the sample does not establish the meaning of its raw
flags/unknown fields. Existing renderer runtime evidence should not be used to
assign meaning to these cooker fields without a direct structural link.
