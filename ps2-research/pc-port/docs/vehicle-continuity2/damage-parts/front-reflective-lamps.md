# Front reflective lamp damage rejection: confirmed

The transparent cover (root19/mode20) and underlying reflective lamp surfaces (root5/root11 mode3) are separate. Keeping the cover transparent does not prove that the mode3 surfaces behind it still use PS2 replacement.

PID13624 healthy3221 and first-damaged6379 retain exact original full geometry hashes for PC21/root5 and PC22/root11. Further-damaged10314 changes both:

- PC21,30vertices/28faces: `cb24d664...` becomes `1e154984bd0e3dd3326e507789ff7266ba14957d5bc28fe562aded270bf44faa`; ordered UV+winding remains `a777b05873183d164d519a6bd0b147176586e019f23111efca10a1faecbd1dc3`.
- PC22,18vertices/14faces: `7e42aed1...` becomes `32ac59a8e95b58ccce260dda476c12338bf66aadad2395d99ef1c8ac587ba4f1`; ordered UV+winding remains `e2f30092b892cdc42461afbc8691012f39821fd22fbb9b03bea6a52fe90fc71d`.

Both current owners pass context7. PC21 moves3native vertices and PC22 moves1; maximum component displacement .019762814044952393. The healthy-full-hash part resolver consequently rejects both changed records before private mode3 drawing. This reproduces the same class of strict identity failure as the separately fixed cover, not a reflection-format or lighting defect.

The other18vertex/14face draw, geometry `e3f1adc5...`, is conditional glass with different UV/winding and context5; it is not PC22 and must not be admitted by counts.

Pinned index-only mapping drafts cover every referenced PS2 vertex: root5 has48vertices, at most3native candidates each; root11 has22vertices, one candidate each. Every candidate exists within offline1e-5 and all duplicate candidate native deltas agree exactly in all three observed states. Runtime must still enforce exact healthy/UV/winding/current owner/currentupload certificates and agreement. Source tolerance is not a runtime identity tolerance. Unknown future candidate disagreement must fall back Stock.

Generator, source hashes, index-only draft headers and compact measurements accompany this note. Three focused evidence tests PASS. The flushed session records successful cover root19 draw/restore at285 and13327, but it does not contain per-transition cover damage events; user confirmation remains the positive visual evidence for transparent damaged covers.
