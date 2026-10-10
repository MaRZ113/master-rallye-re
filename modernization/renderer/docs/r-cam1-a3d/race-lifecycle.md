# R-CAM1-A3d: hierarchical race lifecycle

The A3c capture at frame 2864 and its later frame 6252 came from pristine retail
SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
Session DLL was `70992f4c1a8ea115f5bee942c7af781bab039740407eb30e85cc78073eb83cb4`.
The [curated golden excerpts](../../research/r-cam1-a3d/a3c-golden-excerpts.json)
retain actual hashes, selected events and original snapshot fields.

`CONFIRMED_BY_RUNTIME_CAPTURE`: event 4 rejected a request while frontend job
54744440/lifetime 1 was executing. That permanent poison prevented later queues,
success commits and returns from being correlated. Owner lifetime 1 was initialized
in scene generation 7, followed by generation 8/Hud0; lifetime 3 in generation 19
was followed by generation 20/Hud0. Native owner membership/arrays were never
probed: `no_current_owner_lifetime` was the early generation check, not evidence
that RaceLimits was absent. The later capture retains destroy/retire events
47, 64, 65 and 79. No successful callback is invented in the golden fixtures.

`CONFIRMED_BY_EXE`: request VA `0x00522330` / RVA `0x00122330` can run from
native scene execution. Each request still gets a scene serial. Queue binds
its source, flags and parent execution lifetime; a bounded eight-entry execution
stack supports synchronous nesting and deferred child execution. Jobs have their
own monotonically increasing lifetime, independent of raw pointer reuse.
Terminal unrelated jobs may be evicted from the 64-entry table; active/root/parent
jobs remain protected. The event ring holds 128 entries.

Native Commit VA `0x00522680` / RVA `0x00122680` copies SceneManager requested
ID `+4` into committed ID `+0` on success. It does not copy the executing job's
original scene. Parent success can therefore report the subsequent HUD scene.
A job requires the actual successful parse/Commit and matching callback return.
It cannot succeed from an inferred final HUD ID.

The narrowly supported HUD edge requires the outer request return PC
VA `0x004AA0C1` / RVA `0x000AA0C1`, `Hud/Hud0`, flags `+21=1,+22=0`, and an
initialized owner attached inside the current parent job. Native selector
`0x004AA020` produces that request. The origin reader uses original PUSHAD ESP
`+24`: request prefix pushes ECX/ESI/EDI, the observed argument, CALL and PUSHFD.
A real x86 fixture verifies this offset. Names and adjacent generations alone
never preserve a race certificate.

An unrecognized request starts a new candidate race lifecycle and revokes the
previous certificate. It does not permanently poison normal nested loading or
erase independently measured native liveness. Root and every accepted HUD child
must terminate successfully in the same race lifecycle. Failed/open/read jobs,
Reset, retirement, destruction and integrity rejection set a revocation fence;
late completion cannot resurrect that lifecycle. Unknown ancestry stays unqualified.
Thread mismatch, active-pointer reuse, impossible execution stack/duplicate return,
hook ownership loss and overflow remain integrity failures. A new observed lifecycle
can recover local unsupported/loading failures, never permanent integrity poison.

Actor ABA protection combines attachment serial, actor+AI identity, initializer,
job lifetime, live registry/list membership and retirement/destructor events.
An owner from an older lifecycle cannot authorize the new race even if its address
or the course name matches. Raw scene IDs never identify a course by themselves.
