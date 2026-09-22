# Legacy shape-transfer experiment (v2)

## What it does

Legacy v2 takes an arbitrary/donor OBJ and projects its shape onto the original
Master Rallye vertex layout. It offers nearest-vertex and nearest-surface-style
mapping while retaining the template's vertex count and binary topology.

## Preservation and loss

It can preserve the original DX index topology, draw/material structures,
texture strings, and unknown template bytes because it ultimately patches a
fixed-size template. It does **not** preserve donor topology, donor edge flow,
UV seams, material boundaries, or exact donor surface detail. Nearest mappings
can fold vertices, merge distant features, create self-intersections, and
produce poor normals.

## Status

**USEFUL_HYPOTHESIS / EXPERIMENTAL_AUTHORING_TOOL.** This is not a DX format
rule and not a core writer. A future home could be
`tools/experimental/shape_transfer.py`, with explicit error metrics and
visual validation, but migration is not necessary for R3.1 and was not done in
R2.5.
