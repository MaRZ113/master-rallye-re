# Hierarchy and runtime traversal

The executable connects the selected source groups to runtime traversal:

```text
PSM tag1 -> tag6 -> tag5 -> material-owning tag2
  [original bytes and391d38]
       -> tag6 child-bound insertion / indexed child cache
          [3929ec..392a7c;3c1eb0]
       -> model+3c region data and view X/0/Z selection
          [3c1148 ->3c7458 ->26bc78]
       -> selected child index, once per generation
          [3c1e48; stamp+28, generation+34]
       -> bound radius/center visibility gate
          [3b9258 ->200550]
       -> generic sibling-linked child traversal, same draw context
          [3b93f0 -> child virtual+5c]
       -> tag2 mesh virtual+5c=3bca80
          [reused WATER1 verified vtable488328]
       -> material/cache queue and CPU renderer
          [WATER1 material-to-draw; no new shader reverse]
       -> UNKNOWN LINK: selected live children, packets and visible frame
```

3c1eb0 caches children in+18/+1c/+20, sizes a stamp vector+28/+2c/+30,
sets ready+24 and resets generation+34. 3c1e48 compares stamp[index] with
generation before virtual draw; it writes the stamp and increments the global
42dca8 diagnostic counter. A current generation is not a live object count.
Initial zero stamps/generation and rollover behavior are not turned into an
offline first-frame simulation.

3c1148 uses draw-context+8 to obtain a model, then model+3c for selection data.
No model/structure yields no child dispatch in the traced path. Camera X/Z are
read from view+C0/C8; Y is explicitly zero for the region query. A -1 region
result returns early. Directional selection additionally uses negative view
B0/B8, constructs a horizontal plane, and calls3c15d8 if squared X/Z direction
exceeds0.001. A record list at structure-base+24/+28 supplies additional indices.

3c7458 advances region descriptors by0x18 and returns the first accepted index;
26bc78 reads X/Z and region data with0x1c elements. Its complete membership and
3c15d8 directional predicates remain UNKNOWN: EE instructions truncate the
bounded decompiler. Magic-divide expressions in generic MIPS output are not
accepted as exact table-count formulae. No octree/PVS/LOD class name is invented.

3b9258 retrieves the view through graphics virtual+54, passes radius+28 and
center+1c to200550, and traverses children only on acceptance. Eligibility is
confirmed by executable; a given camera's actual selected set needs capture.
