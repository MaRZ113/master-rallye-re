# Water and puddle survey

Status: course material use confirmed on both platforms; new PS2 water geometry or dynamic reflections remain UNKNOWN.

Water-related material directives are present in 34 of 36 decoded PS2 landscape PSMs and 33 of 36 canonical PC course sidecars. This compatible metric is **resource families with at least one qualifying directive**, not material count or visible water-body count. Both lack qualifying metadata in Italy1 and Turkey1; PC Turkey3 is the additional negative case. `$shader(puddle)` appears in 33 PS2 landscape models versus 17 PC sidecars; `$shader(water)` appears in 19 versus 24. Mixed strings and reused material names do not establish additional puddle instances.

The following references are inside decoded compiled course payloads, beyond archive filenames:

| PS2 landscape | First decoded payload offset | Exact material-like string |
| --- | ---: | --- |
| France1 | 3,541,866 | `water $surfacetype(water) $shader(puddle)` |
| France1 | 3,701,932 | `water $surfacetype(water) $shader(water)` |
| France1 | 3,553,566 | `$shader(waterfall) $scroll(v,+1)` |
| Italy_S1 | 3,638,832 | `water $surfacetype(water) $shader(puddle)` |
| Spain_S2 | 4,096,247 | `Water $surfacetype(water) $shader(puddle)` |
| Spain_S2 | 4,190,686 | `$shader(waterfall) $scroll(v,+1)` |
| Turkey3 | 3,429,472 | `water $surfacetype(water) $shader(puddle)` |

Italy_S1's PC counterpart already names `water $surfacetype(water) $shader(water)`; the material interface changes to puddle in PS2 rather than proving a brand-new water surface. Spain_S2 PC names `$shader(waterall) $scroll(v,+1)` while PS2 names `$shader(waterfall) $scroll(v,+1)`. France1's PC water and waterfall directives likewise already exist. Both spellings waterall/waterfall occur in the wider corpus; treating waterall as a new unrelated subsystem would overstate the evidence.

## Compiled PC geometry proof

Read-only Course SDK `parse_course_dx` and sidecar candidate matching validate France1, Italy_S1 and Turkey1 complete disjoint index/vertex coverage. France1 has 14 draw records matched uniquely to the water material and two matched uniquely to the waterfall material; Italy_S1 has ten water candidate draws. Turkey1 has none. Draw records are renderer submissions and can partition one physical water body; they are not independent water-body instances.

One France1 water draw (index 236) uses water-tga, 182 triangles and finite bounds X [-2334.8921,-2204.8921], Y approximately 30.35725, Z [-198.1078,-58.1078]. Waterfall draw 287 uses waterfall-tga, 350 triangles and bounds X [-2480.1755,-2344.9907], Y [19.8286,95.7705], Z [-436.3899,-287.2865]. Italy_S1's ten candidate draws also have validated finite geometry. This establishes existing PC course geometry with water-related material selection, not the final rendered effect or reflection semantics.

Turkey3 is a new bounded discrepancy: all 939 decoded PC draw records have zero water/puddle texture-slot or sidecar candidate-material hits; its validated geometry has 54,589 vertices and 42,237 triangles, SHA-256 `724a69da708a124f7dbfd666b7ad8d391bcaf22ff94bd2c91143e305749cf7f8`. PS2 has the course-local puddle string above. Presence is NOT_FOUND_IN_SCANNED_PC_CORPUS for named material/draw dependencies. Whether PS2 adds geometry, changes an unlabeled PC surface, or changes only classification remains UNKNOWN until a PSM geometry/material binding is decoded. This does not prove PC lacks an unlabelled water surface or runtime water system.

## Representation boundaries

Asset/texture presence: both corpora contain course water texture families; PackFS additionally identifies CommonTextures/WATERSURFACE2. Material selection: confirmed by the course strings/sidecars above. PC course geometry: validated draw records above. PS2 course geometry binding: UNKNOWN because no PSM draw parser exists in this survey. Explicit XML water placement/runtime subsystem: see ambient-survey.md and delta-matrix.json; no general water generator was derived here. Dynamic animation/reflections/collision/vehicle-water response: UNKNOWN. A standalone `$surfacetype(water)` string can be collision material metadata and is not itself evidence of a visible water draw.

The six screenshots include a large blue water surface in 20260415224620.jpg. The course identity and matching surface have not been fixed by camera or capture provenance; this is SCREENSHOT_CORRELATION only. It does not confirm reflection, animation, physics or PS2-to-PC exclusivity.

## Per-landscape directive presence

| Landscape resource family | PS2 water material directives | PC water material directives |
| --- | --- | --- |
| FRANCE1 | scroll(v,+1), shader(puddle), shader(water), shader(waterfall), surfacetype(water) | scroll(v,+1), shader(water), shader(waterfall), surfacetype(water) |
| FRANCE2 | shader(puddle), surfacetype(water) | shader(water), surfacetype(water) |
| FRANCE_M | scroll(v,+1), shader(puddle), shader(waterfall), surfacetype(water) | scroll(v,+1), shader(water), shader(waterfall), surfacetype(water) |
| FRANCE_S1 | scroll(v,+1), shader(puddle), shader(waterfall), surfacetype(water) | scroll(v,+1), shader(water), shader(waterfall), surfacetype(water) |
| FRANCE_S2 | shader(puddle), shader(water), surfacetype(water) | shader(water), surfacetype(water) |
| FRANCE_W | shader(puddle), shader(water), surfacetype(water) | shader(water), surfacetype(water) |
| FRANCE_W_FLIP | shader(puddle), shader(water), surfacetype(water) | shader(water), surfacetype(water) |
| ITALY1 | not found | not found |
| ITALY2 | shader(puddle), surfacetype(water) | shader(puddle), shader(water), surfacetype(water) |
| ITALY3 | shader(puddle), shader(water), surfacetype(water) | shader(puddle), shader(water), surfacetype(water) |
| ITALY_M1 | shader(puddle), surfacetype(water) | shader(puddle), surfacetype(water) |
| ITALY_M1_FLIP | shader(puddle), surfacetype(water) | shader(puddle), surfacetype(water) |
| ITALY_M2 | shader(puddle), surfacetype(water) | shader(puddle), shader(water), surfacetype(water) |
| ITALY_S1 | shader(puddle), surfacetype(water) | shader(water), surfacetype(water) |
| ITALY_S2 | shader(puddle), surfacetype(water) | shader(puddle), surfacetype(water) |
| ITALY_S3 | shader(puddle), shader(water), surfacetype(water) | shader(puddle), shader(water), surfacetype(water) |
| ITALY_S3_FLIP | shader(puddle), shader(water), surfacetype(water) | shader(puddle), shader(water), surfacetype(water) |
| ITALY_S4 | shader(puddle), surfacetype(water) | shader(puddle), shader(water), surfacetype(water) |
| ITALY_W1 | shader(puddle), surfacetype(water) | shader(water), surfacetype(water) |
| ITALY_W2 | shader(puddle), shader(water), surfacetype(water) | shader(puddle), shader(water), surfacetype(water) |
| SPAIN1 | scroll(v,+1), shader(puddle), shader(water), shader(waterfall), surfacetype(water) | scroll(v,+1), shader(puddle), shader(water), shader(waterall), surfacetype(water) |
| SPAIN2 | shader(water), surfacetype(water) | shader(water), surfacetype(water) |
| SPAIN_M | scroll(v,+1), shader(puddle), shader(water), shader(waterall), surfacetype(water) | scroll(v,+1), shader(puddle), shader(water), shader(waterall), surfacetype(water) |
| SPAIN_S1 | shader(puddle), surfacetype(water) | shader(puddle), shader(water), surfacetype(water) |
| SPAIN_S1_FLIP | shader(puddle), surfacetype(water) | shader(puddle), shader(water), surfacetype(water) |
| SPAIN_S2 | scroll(v,+1), shader(puddle), shader(water), shader(waterfall), surfacetype(water) | scroll(v,+1), shader(puddle), shader(water), shader(waterall), surfacetype(water) |
| SPAIN_W | shader(puddle), shader(water), surfacetype(water) | shader(puddle), shader(water), surfacetype(water) |
| SPAIN_W_FLIP | shader(puddle), shader(water), surfacetype(water) | shader(puddle), shader(water), surfacetype(water) |
| TURKEY1 | not found | not found |
| TURKEY2 | shader(puddle), shader(water), surfacetype(water) | surfacetype(water) |
| TURKEY3 | shader(puddle), surfacetype(water) | not found |
| TURKEY_M | shader(puddle), shader(water), surfacetype(water) | surfacetype(water) |
| TURKEY_S1 | shader(puddle), shader(water), surfacetype(water) | surfacetype(water) |
| TURKEY_S2 | shader(puddle), shader(water), surfacetype(water) | surfacetype(water) |
| TURKEY_S2_FLIP | shader(puddle), surfacetype(water) | surfacetype(water) |
| TURKEY_W | shader(puddle), shader(water), surfacetype(water) | surfacetype(water) |

Deferred deep phase: PS2-WATER1 should decode PSM material-to-draw binding and distinguish water/puddle/waterfall consumers against existing PC geometry, before adding assets or proposing renderer work. The wider CDELTA1 priority is decided in next.md.
