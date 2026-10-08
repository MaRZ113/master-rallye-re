# Material and shader contract

The readable PSM material is parsed by the executable. It is not merely an
unused source annotation or a guessed binary flag. Node reader `391d38`
reads material input into mesh+80 through `390ba8`; `391690` initializes
generic map defaults and applies the shader property.

`390d98` searches case-sensitively for `$shader`, then the first following
opening and closing parentheses. It returns their interior. The shared
interner folds ASCII capitals and slash direction **after** extraction.
`3a6c58` looks up that interned name; `3ac680` compares interned identities.
It calls shader object virtual+14. Unknown names log an unidentified-shader
message and retain the previously computed generic map defaults. The diagnostic
preserves the authored spelling and does not guess that fallback's numeric mode
when the general map setup is not being evaluated.

| Exact recognized name | Registration / name VA | Handler | mesh+28 | Auxiliary | Texture names | mesh+44 |
|---|---|---|---:|---|---|---:|
| waterfall | 3a7708 /487628 | 3ae800 | 19 |327ee8 /485378 | Both overridden to common waterfall / waterfall2 | .005 |
| waterall | 3a7778 /487678 | 3ae8d0 | 19 |327ee8 /485378 | Same result, separate registration | .005 |
| water | 3a77e8 /487688 | 3ae9a0 | 10 |327ea0 /4853a0 | Course primary retained; watersurface2 secondary | 1 |
| puddle | 3a7858 /4876b0 | 3aea50 | 9 |327e60 /4853c8 | Course primary retained; watersurface2 secondary | .25 |

Each handler sets mesh+2c, +3c and+40 to1, writes auxiliary pointer+24 and
the material mip/scale factor+44. The shader registry is initialized once by
`390f98`; string ordering is not used to infer mode numbers.

`$surfacetype(water)` is a separate interface. The tag-103 spatial material
parser `2d5100` writes a surface-type identity vector at proxy+8c and detail
identities at+98. Its short material table is not the visual shader table.
Water-related executable string consumers also occur at `3344cc/336930`,
but their broader vehicle/physics behavior was not reverse-engineered here.
There is a narrow real connection: puddle vertex-color preparation `320938`
queries spatial triangles and skips water-named candidate materials when
selecting a non-water ground height. This does not make surface type a GS
blend selector.

`$scroll(v,+1)` is preserved as authored metadata. The traced shader extractor,
handlers and waterfall update do not evaluate its axis or numeric argument.
Waterfall animation is a hardcoded dual-UV update. No `$scroll` literal was
found in the scanned canonical ELF strings, which supports a bounded lead,
not a universal proof that every general property path ignores it.

See [UV and animation](uv-and-animation.md) for the proved formula and unknown
counter units. `waterall` acceptance and absence of a proved numeric scroll
consumer are separate conclusions.
