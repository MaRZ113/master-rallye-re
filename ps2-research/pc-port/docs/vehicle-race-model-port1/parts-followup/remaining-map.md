# X-Trail remaining CAR parts: bounded decision

Evidence source: `../assets/pc-source-map.json`, hash-locked original PC CAR and independently decoded original PS2 CAR. This is source geometry correspondence; current resource generations and owner still must be admitted by the runtime classifier. PC numbers below are compiled source records, not persistent native draw ordinals.

| PC record | Faces | Original PS2 correspondence | Decision |
|---|---:|---|---|
| 2 | 34 | root.2:28 flat black; root.15:6 authored rubber-secondary | Mixed static trim; do not blanket classify reflective |
| 3 | 8 | root.2:8, UV differs by up to .7864 | Source PS2 UV required |
| 10 | 18 | root.19:18 glass; normals match within 1.2e-7, UV differs by up to 1.0034 | One-to-one static glass geometry; separate mode20 submission at its native draw is justified after runtime gates |
| 16 | 29 | No PS2 triangle correspondence; dnissanslave7 texture | Native driver retained |
| 17 | 42 | First38 unmatched; faces38..39 root.15; faces40..41 root.18 | Never suppress all42; preserve unmatched native driver/black geometry |
| 18 | 29 | No correspondence; dnissandad | Native driver retained |
| 19 | 148 | No correspondence to PS2 root.8, despite equal148 face count | Native helmet retained; equal primitive count does not prove identity |
| 20 | 200 | No correspondence; whitesuit32 | Native driver retained |
| 21 | 28 | root.5 all28, exact UV, normals within1.2e-7 | Safe additional unconditional source-model subset |
| 22 | 14 | root.11 all14, exact UV, normals within6e-8 | Safe additional unconditional source-model subset |
| 23 | 6 | root.20.0.0 off and root.20.1.0 on share positions | Keep native branch; geometry alone cannot choose off/on |
| 24 | 6 | Same overlapping positions; actual UV/normals correspond to on | Keep native branch |
| 25 | 22 | root.20.1.1 glow, exact UV/normals | Keep native brake/glow lifetime and switch |

Root.2's full50 faces are accounted for by PC1:14 (already suppressed by the first pilot), PC2:28 and PC3:8. Adding full root.2 is safe only after removing the latter36 stock faces; PC2's last6 rubber faces must remain or be replaced separately. Root.15's full8 are PC2:6 plus PC17:2. Root.18 is two default-material faces inside PC17, not a complete42-face replacement. These are genuine body trim and must be distinguished from the first38 unmatched PC17 faces. Root.8's helmet148 faces are not a source-coincident replacement for PC19; do not infer a driver swap from counts.

The smallest additive chassis expansion is roots5+11 (42 original faces) with exact PC21+22 suppression, retaining current Mode4 source materials and leaving all conditional brake/screens and native drivers unchanged. It does not require new authored assets: both roots already exist in the converted unconditional CAR resource. Add root19 glass only through an isolated mode20 material transaction at the admitted native glass draw; drawing it in the early opaque chassis bucket risks ordering differences.

PC26/27,28/29,30/31 correspond to conditional side/front screens. Each pair shares positions but differs in intact/cracked primary texture or branch composition. They are deliberately outside the unconditional source-set warmup. No live selected-branch contract was established in this focused pass; rendering both would duplicate surfaces.

No integration, original game asset or frozen renderer edits, native memory reads, builds, physics changes or new runtime claims were made by this read-only subtask.
