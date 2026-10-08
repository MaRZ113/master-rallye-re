# Source and coordinates

PS2_VISUAL_SOURCE_MESH is the authored PSM tag2 strip layer; PS2_SPATIAL_TRIANGLE
is separate tag103 data and is never counted as visual geometry here.
PS2_SCENE_INSTANCE means a RaceTest Egg; PS2_RUNTIME_TRANSFORM is separate.
PC_COMPILED_RENDER_DRAW comes from validated revision135 DX. PC_TXT_MESH_RECORD
retains source names/spans/parents, without a guessed DX face correspondence.
PC_SCENE_INSTANCE and PC_COLLISION_STRUCTURE remain separate layers.

Matching uses GAME_SOURCE coordinates. All three authored landscape matrices
are identity on both platforms; non-identity transforms fail closed. Independent
ordered RaceLine anchors show420/420 Turkey3 and448/448 France1 identical points;
Italy has290/292 identical compared positions, two differences, maximum26.822077,
mean0.176589 source units. This supports the common frame without fitting those
unmatched geometry surfaces. Ordinary vertex agreement independently supports it.
The internal Italy_S1 landscape pairs with the differently spelled ITALYS1.XML;
filename guessing was rejected. No scale/offset/axis/rotation registration is fit.

The optional display conversion is(X,Y,Z)->(X,-Z,Y),scale1. No Blender scene or
add-on was changed. Diagnostic bounds/maps stay source-space; Y is collapsed
only in the top-down visualization. Live landscape/instance matrices are unknown.
