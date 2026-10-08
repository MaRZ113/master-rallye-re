# Inspectable source maps

The read-only SVG workflow creates ignored data/dressing1/maps/TURKEY3.svg and
ITALY_S1.svg. Turkey3 includes a course overview and three candidate insets:
nearby PS2 terrain, cyan puddle reference, colored candidate triangles, whole-edge
component labels, source ancestor tag/offset chains and orange PC-family outlines.
ItalyS1 retains pinus source coordinates, nearby geometry and PC-family locations.

Axes are game X right/Z up. Projection collapses Y; JSON retains complete bounds.
Overlap in the map does not establish 3D correspondence. A number labels an edge
component, never an object. Fitted subpart transforms are not applied as authored
scene placement. Maps are decoded source diagnostics, not emulator frames.

The Turkey map was inspected through a locally rasterized PNG; the generated
PNG/SVG contain original geometry and remain ignored/excluded from the handoff.
The handoff supplies the generator and compact bounds, allowing private-corpus
owners to recreate maps. No Blender installation or add-on modification is needed.
No France dynamic-versus-static overlay is generated because a safe route-time
transform/instance relation remains unproved.

```powershell
python ps2-research/tools/dressing_visualize.py --inventory ps2-research/data/dressing1/inventory-full.json --ps2-root "D:/Game/Master Rallye PS2" --pc-root "D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked" --sdk "D:/Game/Master Rallye/master-rallye-re-course" --output-directory ps2-research/data/dressing1/maps
```
