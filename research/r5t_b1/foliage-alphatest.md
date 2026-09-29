# Foliage alpha-test source evidence

## Static comparison

The old 8.4.1 France1 source corpus lacks the literal `$alphatest` and
`$shader(tree)` strings found in late source material. In the available cooked
DX comparisons, old-source foliage candidates recooked by the Demo 9.10
runtime commonly show raw flags `01000101`; native late tree candidates
predominantly show `01010101`. The cooker log also contains render-sort and
plane-choice warnings.

This is correlation across different source/build contexts. It does not prove
which material field controls alpha testing, that these bits are the exact
cause of foliage occlusion, or that tag100/BSP data is implicated.

## Controlled experiment status

No foliage source construct was edited or cooked in R5T-B.1. The available
France1 GXM/TXT structure is large, and no isolated source material-to-DX
binding has been decoded. Adding a guessed directive would not be a controlled
test. There is no foliage runtime candidate prepared.

Future work should identify one small tree source/material pair, establish the
exact existing syntax and texture binding, make one cooker-understood change,
and compare repeated DX material flags/draw grouping and logs before requesting
any runtime observation.
