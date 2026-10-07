# R-GFX5-5: UI ownership decision

**READY_FOR_CLOSEOUT_WITH_EXPERIMENTAL_PRESERVEMARGINS.** No robust native widget owner was established at the final consumer. Group inheritance is not implemented. PreserveMargins remains **EXPERIMENTAL / LEGACY COMPATIBILITY**; **Centered4x3 is the stable recommended production mode**. This is the clean fallback explicitly authorized by the narrow-pass prompt, not a claim that remaining HUD/menu splitting is fixed.

The R-GFX5-4 user report confirms working packet-anchor retention and Windowed maximize/restore, while composite HUD/decorative stability still fails. Four supplied sessions match pristine retail SHA256 bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4 and DLL 044a492a4919a009e416863d9e4753f139af007a70af1407c159dabae6fe5a65. Runtime-trace evidence: retained-without-current-rule reaches 11,901 in session12128 and 48,238 in session29228; all sampled restore-failure counters are zero. These are cumulative maxima within each session, not summed successes or visual proof. [Hashes and curated observations](ui-group-ownership.json).

## Native candidates and limits

| Candidate | Static evidence, VA / RVA | Ownership decision |
| --- | --- | --- |
| Render entity | DrawTextPacket 0x0056D110 / 0x0016D110 reads entity+0x4C | Identifies one packet, no proven parent/root link for sibling packets |
| Packet content vector | Same consumer reads packet+8/+0xC and advances content rows by0x38 | Intra-packet geometry/text content; not proof of ownership across entities |
| Cached matrix | Consumer copies packet transform; identity constructor0x0058C660 / 0x0018C660; setter0x004E24C0 / 0x000E24C0 replaces/releases packet+0x84 | Cached matrix object, not an established widget parent |
| Camera list | Submit0x00509680 / 0x00109680; SortPerCamera0x00509970 / 0x00109970 | Camera-indexed list and priority/distance sorting are broader than a widget and submission-order dependent |
| Global dispatcher | 0x004D3920 / 0x000D3920 initializes singleton0x006F93D0 / 0x002F93D0 with dispatch vtables | Renderer service, not proof of a HUD subgroup |

These field meanings are CONFIRMED_BY_EXE through the read-only Ghidra12.1.4 bridge exporter. Pristine EXE and Ghidra program hashes were verified; project opened read-only, temporary transactions rolled back, no database save. Raw exports remain ignored under .analysis/r-gfx5/narrow-ui-*. No original reverse notes or retired trees were modified. Sparse project reference queries return no consumer/list references; that is a limitation of this analysis, not evidence that a UI hierarchy does not exist elsewhere.

Session29228's bounded prefix contains198 consume records: 52 entities, 52 packets, 52 content-storage pointers, maximum one distinct entity per candidate. Directions: right80, left32, none86. The same renderer can submit logically related pieces as distinct packets, but this prefix cannot name their logical widgets. Shared matrix/font/texture/color, geometric proximity and ordering are insufficient admission evidence. No unverified pointer fields are read, no nearest-neighbor groups are introduced, and the historical51 XY rules/left text bands are unchanged.

## Short grace and safety

`MARGIN_ANCHOR_GRACE_FRAMES=2` tolerates up to two completed frames without consumption of an otherwise identical entity/packet/point/content-storage/mode identity. Expiry occurs at completion of the third absent frame. A returning packet uses **current engine X/Y** with its retained direction; learned coordinates are never frozen. Alternating submission is covered by tests. Actual packet/storage replacement deliberately requires relearning rather than receiving alternating-storage exceptions.

Packet, point, mode or storage replacement, invalid structure/nonzeroZ, Reset, observed frontend/race epoch and device release invalidate immediately, overriding grace. Identity remains a validated tuple plus epoch, not a real native allocator generation. MainMenu-to-QuickRace is not claimed to be a separately observed screen epoch. Fully identical tuple reuse before expiry is unobservable; this remaining safety boundary reinforces experimental status. Frame edits still restore at Present/Reset; the verified consumer bridge and guarded restore are unchanged.

`anchor_grace_retained` counts actual returns after a missing frame, once on the first return consumption. `grace_expired` counts entries expired beyond the bound. `group_grace_retained=0` is explicitly not applicable because no group registry exists. Existing retained-without-current-rule telemetry remains.

## Bounded diagnostics, not grouping

F10 preserves the three-frame window,64 observed identities and256-record device budget. Packet records now include candidate IDs from already verified entity/packet/content-storage fields, grace retention, current rule, current engine XY, effective X, individual anchor and epoch. Proven group ID/direction are null with `group_owner_status=not_proven`.

Each diagnostic frame can emit `ui_group_candidates`: observed member packet IDs/count, candidate kind and ID, and contradictory current historical-rule evidence. Results are explicitly **prefix-only**, not full-frame membership or semantic direction. A synthetic shared-content candidate with LEFT, RIGHT and CENTER reports conflict, leaves group direction null and keeps the CENTER member unchanged. There is no majority rule, cross-member position derivation or group admission/retention/invalidation to certify.

## Closeout boundary

Numeric INI selectors and strict booleans are canonical; established text enum names and true/false remain accepted. Out-of-range selectors fail locally to Stock; malformed booleans disable that feature. Invalid Trace values now disable the affected logging option and record the raw value/reason in session metadata. This intentionally replaces permissive nonzero/unknown-as-true Trace parsing. Missing Trace options still default to1.

Centered4x3 control and combined Borderless/native AF16/MSAA4/MenuFreezeFix=1 regression are the recommended final human checks. PreserveMargins HUD/menu and F10 are useful research checks, but remaining composite defects do not block the authorized experimental closeout. Backdrop remains BACKDROP_ASSET_EXTENSION_REQUIRED. R-CAM1, photo mode and HD UI are not begun.
