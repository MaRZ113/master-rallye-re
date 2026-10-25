# Surfaces and texture bindings

The hierarchy identifies model, physical draw, material and texture slot. Select
a draw to highlight its actual source surface. Shared wheel geometry affects all
assembled instances. Shared vertices prevent independent diffuse RGB edits.

Selected-surface RGB modulates native vertex colors. It is not semantic paint:
baked lettering can change too. Alpha is preserved. Existing environment passes
can be disabled where qualified; arbitrary shader features are not invented.

Assign Existing Texture changes one selected draw's diffuse slot 0. Select a
slot leaf to choose its exact native slot. The dialog lists every existing local
texture, dimensions, usage and an incompatibility reason. Selecting a texture
shows it in Texture Studio. Assignment does not recolor or replace that texture.

Qualified bindings require equal ASCII name length, native format, dimensions
and alpha plane. Environment/effect slots, new resources, Null activation,
length-changing records and aliased descriptors are rejected. This preserves
record offsets and native damage/reflection alpha semantics. Multiple draws can
reference one image without changing each other's descriptors.

An assignment applies only to the selected model variant. Inspect the other
variant explicitly; no guessed correspondence is applied.
