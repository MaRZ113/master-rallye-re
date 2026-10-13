# Native PC convex lifecycle: bounded follow-up, 2026-10-13

Status: **NATIVE_CACHE_INVALIDATION_PREDECESSOR_RESOLVED; PRIVATE_SPAWN_NOT_ENABLED**.

The original executable is PE32/i386 at image base `0x00400000`, 3,121,214 bytes, SHA-256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. REA's Ghidra 12.1.4 provider and independent installed GNU objdump 2.46 checked the selected original instructions. Nothing launched the game, called a native game function, modified process memory or changed renderer/asset files. This document adds evidence to the earlier `static-followup.md`; it does not rewrite the frozen findings.

## Important qualification of the earlier cache hazard

`static-followup.md` correctly observed that cleanup helpers only resolve an entity when their cached pointer is zero. The previously missing predecessor has now been found:

```text
0x0043F2C0 original physics-manager update
 -> 0x0043F310 maintenance [call 0x0043F2E0]
 -> 0x0043F350 native cache invalidation [call 0x0043F313]
      -> prop bodies in manager+0x28/+0x2C: body+0x1D4 = 0
      -> collision-manager 0x0043AB60 [call 0x0043F3B9]
           -> installed backend vtable+0x30 = 0x0056FCE0
                -> convex instances: instance+0x18 = 0
 -> 0x0043F3D0 existing vehicle maintenance
 -> 0x0043F450 native removal [call 0x0043F321]
      -> 0x0043AB70 collision-manager cleanup
           -> installed backend vtable+0x08 = 0x0056EDE0
                -> entity-name resolution and absent-entity removal
 -> 0x0043F890 / 0x0043FBE0 / 0x0043FE80 update stages
```

The nonvehicle-body clearing store is **0x0043F3AE**, and the convex-instance clearing store is **0x0056FD07**. Original backend vtable bytes at **0x00692348** are `e0 fc 56 00`, selecting `0x0056FCE0`. That routine also clears the second shape-family entity cache at +0x0C and backend+0x30 helper cache at +0x40. REA/Ghidra's default database does not define functions at `0x0043F2C0` or `0x0056FCE0`; their selected entry/return boundaries are grounded in original vtable/call bytes and independently decoded instructions, not fabricated Ghidra functions.

Thus an existing native update clears these caches before cleanup. This resolves the specific static claim that cleanup never has an invalidation predecessor. It **does not** establish arbitrary selective removal, a render-thread mutation boundary, race-exit/restart ordering or rollback of a partially created private object. `0x004F5840` queues Egg retirement; it does not synchronously unregister a collider. Runtime ordering remains **NOT_PERFORMED** in this follow-up.

## Read-only runtime roots and strict layouts

The collision-service holder pointer is stored at **VA 0x006F957C / RVA 0x002F957C**. Original getter `0x004E8CD0` reads it at its entry and lazily allocates when null. A read-only observer must read the pointer; it must **not call this getter**, because the getter mutates native state. `0x004F4EF0` is a base constructor installing vtable `0x0069188C`, not a singleton getter.

The holder's +0x08 is the installed collision backend. Require its original vtable **0x00692318** before decoding its 0x34-byte layout. Its convex-instance vector is:

| Offset | Field |
|---|---|
| +0x14 | Begin pointer |
| +0x18 | End pointer |
| +0x1C | Capacity end pointer |

Native instance allocation is **0x1C bytes**, cloned at `0x00621220`. Its seven DWORD fields are:

| Offset | Proven field |
|---|---|
| +0x00 | Representation at slot 0 |
| +0x04 | Representation at slot 4 |
| +0x08 | Base shape object |
| +0x0C | Native physical body |
| +0x10 | Collision category |
| +0x14 | Egg interned-name ID |
| +0x18 | Mutable resolved-Egg cache |

Do not invent an instance vtable at +0x00: that field is a representation pointer. To preserve slot identity, this follow-up avoids imposing A/B names. Reader `0x0057CE60` stores the first `0x0057D140` result in +0x04, and its second result in +0x00; the base `0x0057D640` result goes in +0x08. Clone `0x00621220` keeps those original slots. Body setter `0x00621310` additionally writes each representation+0x38 and base+0x08; category setter `0x00621330` writes representations+0x3C and base+0x0C.

Only decode the selected nonvehicle body as that type after checking vtable **0x00691A04**. It has allocation 0x1DC, entity-name ID +0x1D0 and resolved-Egg cache +0x1D4. Current-state getter `0x004FF3E0` explicitly copies body+0xA0/+0xA4/+0xA8 to its output XYZ, and +0xAC..+0xB8 to its four-component orientation. Preserve raw words and finite interpreted values. This is not a license to treat every vehicle body as that class.

Egg+0x50 points to its separate en3d object. en3d+0x0C is the interned model-resource ID, and en3d+0x1C..+0x5B is a 16-float transform. `0x004F5A80` initializes the identity matrix there; AI transform consumer `0x004F5440` copies a Broker-provided 16-word matrix there. Matrix interpretation and body state must stay separately labeled in an external sample: observing two changing arrays is not independent physics-contact proof.

## Private native resource bridge: precise remaining contract

The installed backend attachment is **0x0056EEF0**, `ECX=backend`, stack arguments Egg/body/category, callee `RET 0x0C`. Its resource path is:

```text
global pointer 0x006F9CF0 -> native renderer/model owner
 -> owner+0x04 model cache
 -> Egg+0x50 en3d; en3d+0x0C model-resource ID
 -> 0x0054B320 lookup
 -> returned wrapper+0x04 model
 -> model+0x0C convex prototype
 -> 0x00621220 clone
 -> 0x00621310 body binding / 0x00621330 category binding
 -> instance+0x14 Egg name
 -> 0x0056FE10 original vector insertion
```

`0x0054B320` is **not a read-only lookup suitable for an external/native observer**: a miss registers a cache mapping through `0x0053BCA0/0x0054B620`, and `0x0053BE70` may load resources, change LRU links, count load attempts or evict another resource. An external sampler must inspect already existing pointers or record a debugger observation of the original call; it must never invoke the lookup to make evidence appear.

Reader `0x0057CE60` receives **ECX=parser context** and **stack+0x04=native stream pointer**, returns EAX=0x1C-byte prototype and cleans four stack bytes. Its base/representation readers use the native stream vtable+0x3C for float-word reads and +0x44 for integer-word reads. `0x0057D860` consumes counted vertex/face records through those stream methods and allocates refcounted graph objects. A byte array plus a guessed `fread` adapter is not an established ABI.

The original loader `0x00551430` constructs a native stream using **0x0064CE80**, vtable **0x0069CE44**, and stores the convex prototype at **0x0055170C** into model+0x0C. The constructor uses global filesystem-service objects and initializes descriptor/error state; it is not a proved memory-stream constructor. Ghidra's loader pseudocode eliminates numerous original switch branches as unreachable, including the collision branch; that pseudocode alone cannot refute the independently decoded `0x005516D2 -> 0x0057CE60` call or the prototype store.

The exact implementation blockers are now **owned bounded native stream ABI; private model/resource-name/cache registration and retained prototype lifetime; allocation-failure rollback; a validated original physics-thread admission/retirement boundary; controlled original teardown/restart observations**. The cache invalidation predecessor is no longer listed as absent. Do not substitute an existing hay hull, fake a wrapper or edit manager/backend vector pointers.

## Smallest safe next control

Use a bounded external `ReadProcessMemory` sampler to observe original collision-holder/backend/instance/body/entity links during a cold Turkey3 load, restart and exit. Require exact EXE/hash/image base, readable pointer ranges, finite typed state, bounded vectors and revalidated roots on every sample. Detect pointer churn or inconsistent double reads and label them; do not call game getters, query the Broker through native calls or write process memory. External timestamps demonstrate snapshots, **not** function-entry or physics-thread admission.

For missing thread/order proof, separately use user-driven x32dbg log-only breakpoints on the verified entry/return sites in the JSON companion. A debugger breakpoint modifies execution/debug state and may perturb timing; do not label it a passive byte-identical execution. Log register/stack arguments, thread ID and exact old/new relationships with a finite event budget. Do not automatically launch the game or execute native functions. One original vehicle can be the shared convex-interface control; no private tumbleweed is spawned during this capture.

Native physical spawning remains gated until these controls establish the interfaces. No body collision, contact impulse, runtime port success or PS2 visual/physics parity is claimed here.

## Reproducibility and evidence

The JSON companion holds original-byte probe offsets, hashes, slot layouts, exact entry/return sites and current REA Evidence IDs. Key new REA results: `0x004E8CD0` = `ev_240a1a81630fdee0904e2ce97a94ad464698f35cf5832af4a025c1467a47c4dd`; `0x0043F350` = `ev_66ff0620e6ed28a23de87b60e0537bb41e47c9d71aecc5fe131de52fea32e976`; `0x0043F450` = `ev_913fa76bb52eb19f91bcc272c03c7f772317046ada8902798c7e435fe1bc646f`; `0x0057CE60` = `ev_727a47c23cd4163a08c78ccb747c8e121cfc3efecd6190161095114a300583b3`. All native contracts here are **CONFIRMED_BY_EXE**, with explicitly bounded inference and **runtime NOT_PERFORMED**.

Commands actually executed: exact EXE SHA-256; REA `open_binary(..., provider_id="ghidra")`; focused `analyze_function` on the listed addresses; `objdump --version`; `objdump -d -Mintel --start-address=<VA> --stop-address=<exclusive VA>` on the original EXE; `objdump -s` for original backend/body vtables; independent PE section-to-file probe mapping; `git rev-parse HEAD`, `git rev-parse HEAD:modernization/renderer`, `git diff --stat -- modernization/renderer`. No REA database annotations were made. Frozen renderer tree at this check was `e33386bcf682db6983380c499e4928726c758fe0` and its working diff was empty.
