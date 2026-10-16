# Healthy fleet CPU admission review

User observation: Kia PS2 model appears with a large FPS reduction; after collision, performance recovers. The current non-X-Trail damage policy deliberately chooses native Stock on a private damage tree. This is compatible with an expensive healthy certificate path, but it is not a timing measurement or proof that one operation alone causes the entire slowdown.

## Concrete source costs

`fleet_body_certificate` first compares the complete cohort descriptor/resource tokens. `current_tokens` uses the revision of the entire shared buffer, not a byte-range revision. Any native upload to that buffer can therefore invalidate an unchanged healthy body certificate. A cache miss copies every source range and calls `source_hash` on every source.

`frontend_model_native.hpp::source_hash` creates all per-triangle position hashes through `vehicle_face_hashes` and `foliage_face_hash`, sorts the strings, and hashes the joined result. The digest helpers open/create/finish/destroy BCrypt hash objects. This repeats thousands of small hashes for one body, in addition to the exact ordered-position and UV/winding stream checks already performed by `RaceDamageState::snapshot`. The private-tree check skips this whole source-certificate work after collision.

Independently, each candidate draw calls `courseintegration::certificate`, which calls both `live_race_hud_context` and `live_race_certificate`. These synchronously resolve and read the nine Broker context keys plus player identity under the observer lock. The original native body can issue dozens of candidate draws per frame; the precommit check calls the same certificate again. This reintroduces the same class of repeated render-thread work fixed previously for HUD suppression, although the exact contribution requires measurement.

## Small safe optimization

For an already pinned family, retain exact dimensions, descriptor layout, ordered XYZ SHA-256 and ordered UV plus normalized native winding SHA-256. Together these fix the complete ordered positions, UVs and triangle-index stream. An additional unordered per-triangle geometry hash adds no identity strength once those exact source digests match. It may be removed from known-family cohort revalidation without accepting altered geometry, UVs, indices or damage. Keep initial unique-family discovery separately exact; it can use either the existing geometry signature once or a separately checked unique ordered certificate pair.

Do not mark an unchanged range valid solely because its owner is unchanged or substitute prior revisions. Snapshot and verify current bytes when the shared revision changes. The optimization should remove redundant triangle hashing, not weaken fresh source proof.

Sample expensive race/Broker context once per device/frame and reuse only within that frame. Continue current-thread/scene/recording, queue-owner, packet, selected tree, exact WORLD, generation/revision, pass-key and precommit ownership checks on each affected draw. Invalidate the sample for Reset/device changes and race lifetime transitions. Avoid changing the immutable baseline; the cache belongs to the existing PS2 integration scope.

## Bounded measurement

An opt-in aggregate counter, emitted at most once per second and capped per session, can record: candidate calls; full race samples; source-certificate rebuilds/cache hits; source snapshots; triangle-hash calls; elapsed CPU microseconds for certificate, Broker sampling, private material submission and framebuffer capture. Use QueryPerformanceCounter, never per-triangle log lines. Compare healthy versus damaged Stock fallback in one session. This separates CPU admission overhead from genuine private-draw or reflection-capture cost.

No renderer edits, tests or runtime profiling were performed by this independent review.
