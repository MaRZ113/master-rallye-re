# Independent material axis

Geometry matching ignores material. Each relation separately preserves PS2
authored material/map slots and PC actual ordered texture slots/TXT candidates.
Missing slots remain Null; a non-null later slot is not promoted to base color.
Different bindings, different extracted shader tokens and unresolved sidecar
mapping remain distinct. Literal matching names/slots indicate source equivalence
only, not independently proved cross-platform shader behavior.

Italy water gives shared geometry with PS2 puddle versus PC water, proved by WATER1
handler modes9/10. France shared water and ground/foliage also show category or
slot differences. PS2 detail directives are additional metadata, not object counts.
Ground noise often occupies different source slots; this is DIFFERENT_TEXTURE_BINDING,
not an automatic claim that the final pixels differ. Alpha/blend differences are
not inferred from texture names or source alpha. Existing WATER/REFL executable
contracts remain separately referenced; no new renderer behavior is implemented.
