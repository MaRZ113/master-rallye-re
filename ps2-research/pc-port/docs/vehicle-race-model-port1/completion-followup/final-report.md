# X-Trail CAR completion follow-up

Status: IMPLEMENTED_PENDING_USER_RUNTIME for new statictrim/WHEEL. Existing chassis1712faces plus60lamp/glass USER_RUNTIME_CONFIRMED in session27136, successful draw/restore in two race periods and freshF10set. User confirms headlightglass transparency. No claim of complete vehicle/PS2 visual parity.

StartingHEAD9893186. Original renderer frozen; approved overlay only. Canonical .build/baseline and .build/ps2-enabled/.staging reused serially. No new build trees, asset edits, deployment, physics/HUD/course work or push.

## Static CAR

All unconditional original CAR except helmet now covered:1832faces. Original CAR resource unchanged, hash a15ee827bc93e7a7fe242d8ba2440afe1991cd06e8aeee15ce78b836e372ccac. Source PC mixedtrim masks derived independently at .001 tolerance with unique source pairing; runtime checks exactfloat32 geometry hashes and complete multiplicities. root2 full50faces split across PC1/2/3; root15full8 splitPC2/17; root18two faces insidePC17. PC17's38unmatched nativefaces are submitted unchanged in currentIB order, fourprovenfaces replaced by PS2root15/defaultroot18. Original default.gxi black8x8 retained. New geometry uses cached original attributes and acceptedprimaryV sampling. No proprietary bytes committed.

Existing owner/race/upload/matrix checks retained. Material preflight before source suppression; state transaction restores exact native state, stream/texture/shader refs and effective shadow only. Native38 + private4 failure afterpartialGPUsubmission cannot be undone atomically and is reported/disabled. Static trim covers missing14 inside previously suppressed mixedsidedraw, so parts1 chassisbatch now1726 versus1712. Remainingperboundary parts106faces complete1832.

## WHEEL

Original PS2WHEEL SHA d53360eab52761fdadf1a4d5a2c87196be7674fbbb603c41cd4726a4b303773c; originalPCwheel SHA f05ac990b6ea2312f2a2d552ec886aded4c68a8d8fac027f99e1fc7b0826779c (see exactsource evidence for canonical hash). Four source geometry records72/36/54/90 have exhaustive disjoint bit-exact correspondence to three originalPS2meshes. DRAW resource keeps300 original vertices/252faces/5textures,68258bytes, SHA1c548d537acd75480515ff6d43140215638d2cd87c8b254d509dd5e6d004a31f. No new scale/fittedoffset/physics. Preserve original normal/UV/color/texture and rubber secondary; only chrome uses current mixedreflection source.

Strict opt-in defaultStock; one nativeparticipant only, accepted currentframeXtrailchassis, currentqueue/model4leafmembership, actualbindings/generations/revisions and fourhashwarmup percurrentwheelowner. Native per-wheel WORLD preserved at each originaldraw, unitaxes and boundedcurrentchassis proximity checked; unknown/morethan4currentowners failclosed. No historical pointers/drawordinals/texture-onlymatching. Managedresources/pendingtransaction added to realReset repair/invalidation while windowmodeecho retains existing path. Cache only uploadidentity updates; no perframefullscene scan. Stage/material approximations and CULL_NONE remain documented.

## Remaining exact contracts

No safe driver animation/deformation join for PS2helmet: native drivers retained. Conditional sources independently recovered: brakeoff/on sharepositions but differ UV/normals; front intact/cracked are byte-equivalent geometry/UV/normals and differ texture only. Must establish current texture/resource semantic identity before choosing replacement branch. Sideintact is flat1+glass5 and needs partition; no genericalpha/material replacement. Native branch/glow behavior preserved. This pass does not claim all dynamicparts transferred.

## Validation

Both Win32Release builds and exports/generator checks passed; baseline24/24CTest, PS2-enabled34/34CTest, Python133/133. Additionalsource tests trim6/6,conditional4/4,wheel3/3 passed. Nativefocused checks include role-pinned asset parser/defaults/invalidmodes, currentqueueowner, singleparticipantwheelguard, resourcecreation/reset, trimgeometrycounts, state/HRESULT/partialfailure restoration. Independent safety review completed before PC17 finalextension; main reviewed PC17preflight/native38/private4 path. Runtime wheelpose/steering, nativeadjacentdraws, damage and Reset/MSAA remain unconfirmed. Build report and SHAmanifest included. First wheeldecoder testcaught incorrect texturecount4; originalheader proves5 and parser/tests corrected without modifyingasset.

Nextsingle step: user A/B from runtime-ab.md. After successfulwheelpose evidence, map conditional frontscreen boundtexture identity in one paused/intact/crackedpair; do not reopen physics or unrelated course work.
