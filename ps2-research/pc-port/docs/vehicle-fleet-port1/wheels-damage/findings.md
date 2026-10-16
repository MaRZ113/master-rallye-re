# Fleet wheel and damage decision

Source-only, 2026-10-16. No renderer edits, new runtime grants, builds or native mutation.

## Wheels

All 24 paired PS2 WHEEL resources parse through the existing strict terminal-102 reader, with original SHA-256 checked against the accepted fleet source manifest and protected PC wheel.dx hashes checked independently. UFO has no paired wheel resource; leave its native geometry alone.

The audit compares exact float32 position-face multisets, including multiplicity, across all PS2 roots and all native wheel records. It does not fit transforms, adjust wheel radii, infer equivalent UVs or assume a PC draw maps one-to-one to a PS2 root.

Four families have exact exhaustive geometry multisets: **megane, Navara, NewRav, Xtrail**. Of these, megane/NewRav have five native records; Navara/Xtrail have four. The other twenty wheel pairs each contain 252 triangles on both platforms but have no bit-exact matching position triangles. This is a genuine exact-geometry mismatch, not evidence of incompatible physics or an assertion that the meshes look different. A source-backed scale/coordinate relationship could be researched separately; this pass does not invent one.

KiaSportage and Tata also have four native records, but their geometry does not satisfy the exact partition test. Thus four records alone is not a compatibility gate. Most wheel resources (twenty) have five records. Current Xtrail runtime uses a four-source full-wheel mask and four independent wheel owners. The source-record count and independent wheel-owner count are different concepts; neither may be generalized from the other.

Safe fleet integration choice: preserve native wheels for newly admitted chassis. Keep the accepted Xtrail private wheel path unchanged. A subsequent private wheel conversion must retain each current native wheel owner WORLD (steering, suspension and spin), prove complete source membership, and suppress only a complete matching wheel set. Never render these wheel meshes with chassis WORLD. For the four exact families, source equality alone still does not prove current runtime owner, UV/material identity, upload generations or admission.

## Damage

Existing fleet source profiles grant healthy geometry only. The complete current native chassis owner/list must be traversed and all suppressed unconditional source records validated before the first private chassis submission. If any record has changed geometry or a malformed/current-generation mismatch, the **entire vehicle chassis must remain native for that frame**. A late draw-local fallback after earlier private suppression risks a partial/duplicated body. No generic deformed-private rendering is authorized by a UV hash or source tag alone.

Native private-tree selection at instance+0x90 is not itself proof that positions changed; unchanged clones may still satisfy full healthy source signatures. Conversely a formerly admitted owner does not authorize reusing old positions after damage. Use current position geometry and resource generations, and invalidate the full-family admission coherently. Leave conditional native lamps/windows independent and preserve original native draw HRESULTs.

Xtrail remains the separately proven exception: accepted per-source healthy references, static source correspondence, candidate delta agreement and current owner generation gates support its explicit deformation path. Do not replace it with generic Stock fallback or apply its deformation map to another family.

To extend deformation to another family, the missing contract is that family's ordered healthy vertex certificate plus explicit PS2-corner→native-vertex correspondence, ambiguity checks, independently observed damaged branches and coherent full-frame preflight. Native wheel physics and game damage stay native throughout.

## Reproduction

Run `python audit.py` in this directory with the existing protected corpora installed. Output `contracts.json` includes exact per-family source/native counts and per-record root intersection counts. Run `python test_contracts.py` for five metadata integrity checks. These checks establish source inventory only; they do not claim runtime steering or damage acceptance.
