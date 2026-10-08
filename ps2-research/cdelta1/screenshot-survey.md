# Screenshot survey

User PS2.zip was located at `D:/Game/Master Rallye/!backup/PS2/PS2.zip` (4,982,514 bytes). It contains six JPEG files, byte-identical to the six files in `D:/Game/Master Rallye PS2/PS2-userscreens`. Exact archive/member hashes, dimensions and comparison results are in materials-evidence.json. No additional screenshot corpus was found inside that archive.

All six images were inspected. Correlations:

| Capture filename suffix | Visible lead | Evidence boundary |
| --- | --- | --- |
| 20251213155350 | Roadside repeated vegetation tufts, replay vehicle closeup | Appearance only; generator and course UNKNOWN |
| 20251213161001 | Scattered tall trees and small ground vegetation; race HUD | No PC paired camera; tree population delta UNKNOWN |
| 20251214125616 | Vegetation tufts and dust trail between steep slopes | Dust and tufts visible; resource/owner mapping UNKNOWN |
| 20251214125620 | Dust trail, replay closeup and tufts | Appearance only; no new major ambient object identified |
| 20260415224620 | Broad blue water surface beside track, forest line, small vegetation | Water/tuft correlation only; course/surface correspondence, animation and reflections UNKNOWN |
| 20260417002511 | Ground vegetation and race vehicles in replay | No new large ambient object identified |

These captures suggest high visual relevance for detail vegetation and water. They do not establish extra visible trees or props over PC, identify the course securely, prove knockable checkpoints, or show the newly discovered ambient fleet. No coordinates were traced. Screenshots were used only to prioritize byte-level targets and preserve SCREENSHOT_CORRELATION.

The new Nessie XML reference is a useful negative-control lead: its actual PS2 `MISC/NESSIE/NESSIE.PSM` is only 44 raw bytes, SHA-256 `339d5610a6a170f45fafc316d2ca7ae23bd9060ed8180f892efa8ea003d621ac`, with no printable geometry/material names and NaN-like header words. A Visible=True scene reference does not make this a confirmed monster model or visible runtime easter egg. No supplied screenshot displays it.
