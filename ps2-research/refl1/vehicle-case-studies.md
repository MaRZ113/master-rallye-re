# Controlled vehicle cases

The two families use different canonical CAR.PSM payloads and geometry. They are
not two skins of the same mesh. PackFS range/hash provenance and compact selected
groups are in [vehicle-evidence.json](vehicle-evidence.json).

| Model | Decoded bytes | Source vertices | Visual meshes | Shader counts |
|---|---:|---:|---:|---|
|TATA|180332|3262|31|20carshiny,6carglass,3carflat,2carbrakelights|
|KIASPORTAGE|194660|3559|31|13carshiny,7carglass,6carflat,2carbrakelights,3untagged|

Both visual trees have31tag2,5tag7 and10tag8 records under a root tag1, and end
with101. Tree end=176064/191364 respectively. Counts include named-child
alternatives and are never reported as a simultaneous runtime draw population.

| Case | Mesh / material offset | Source textures | Strips / diagnostic faces | Contract |
|---|---|---|---|---|
|A painted Tata body|root.3 /170849|tatabon-tga +whitepaint-tga|8 /57|carshiny3, target override|
|B second-family Kia body|root.4 /186148|kiaside2-tga +whitepaint-tga|27 /522|same mode3/source policy|
|B additional Kia panel|root.5 /186634|kiabon2-tga +whitepaint-tga|14 /206|same mechanism|
|C Tata glass|root.21 /174377|windscreen32-tga +glass-tga|2 /8|carglass20, static highlight|
|C Tata glass variant|root.22 /174539|windscreenc32-tga +glass-tga|1 /4|same mode20|
|D Kia metallic/bright trim lead|root.20 /189466|mlamp32-tga +chrome-tga|7 /28|carshiny; chrome map replaced|
|E Tata opaque control|root.0 /169723|underdash2-tga|37 /579|carflat1; no env selector|
|Texture exception control|Kia root.9 /187437|canvas-tga +rubber-tga|8 /159|carshiny3 but rubber retained|

The mesh/material association is CONFIRMED_BY_BOTH. Calling a paint-family mesh
a body panel is supported by its resource family and geometry; exact visible
part/frame correspondence is not runtime-confirmed. The compact bounds are
model-local, not measured screenshot regions. Body meshes include several
paint/plastic-looking source families: carshiny selection is broader than only
whitepaint. Neither source glossiness nor chrome naming defines a distinct shader.

Tata and Kia use the same register/compiler contract despite different geometry
and source images. Untagged Kia meshes and carbrakelights remain explicitly
untraced. The all-CAR name survey preserves caralpha/carsglass/carglow and typo
crashiny as additional leads; no full vehicle catalog reverse is claimed.

Live player/opponent distinction, LOD and conditional name selection are not
established. The recovered target is global to the selected presentation pass,
not allocated per selected model. A future capture must select a specific mesh
and its runtime instance before validating its visible contribution.
