# Water/puddle geometry to submission

The recovered path is a general landscape strip renderer selected by mesh
material modes, with water auxiliaries. It reaches an original CPU VIF1 DMA
start. Embedded VU bytes and the CPU upload address are also connected; actual
resident micro-RAM and visible GIF output remain uncaptured.

| Stage | Canonical ELF contract |
|---|---|
| Authored mesh |391d38 tag2, mesh+74 strips, model+18 shared vertices|
| Geometry/cache |31f2f8/31f1c8 ->31f4e0;361a58 invokes auxiliary updates|
| Input record |64 bytes: normal/control16, float color16, two UV pairs16, XYZW16|
| Source control |First strip vertex carries strip count; following vertices copy source bit0 for ADC suppression|
| Batch |Whole strips accumulated while `(count+next_count)*4+1 <128`; flush on failure or rising scale ratio>1.5|
| Geometry packet |31f478 ->31d7c8: REF30000000 with4qwords/vertex, STCYCL01000404, UNPACK6c008000 with count, MSCAL000f|
| Packet finalization |31dce8 fixes REF physical addresses;31ddd8 emits RET60000000|
| Mesh draw |3bca80 sets mode and handles, then31d250 queues cached wrapper|
| Queue drain |31cd98 calls312610 mode,311c50/312130 textures,31c438 state;31e010 appends DMA CALL50000000|
| State inputs |31e478/31e6a8 transfer11qwords from42dec0/42df70; MSCAL37c/377|
| Selector input |31af50 transfers selector0 water /3 puddle with MSCAL36a|
| Transform |Shared317470 projection UNPACK+MSCAL30e;317770 worldview UNPACK+MSCAL2cf|
| Frame close |316ce0 virtual+34 ->316b88 adds NEXT links and advances producer42da10 in a4-context ring|
| Hardware start |30ea80 consumes context at42d690+index*e0, writes VIF1 QWC/TADR/CHCR|

Selected water strips are at most31 source vertices. The128-qword guard is a
batching comparison, **not** a proven universal rejection of an oversized strip:
the code flushes before appending the next whole strip. No invented general
maximum is substituted into the decoder.

The shared DMA drain is grounded by original words and instruction order:
at **30ed64**, QWC at10009020 is zeroed; **30ed70** writes the current context's
physical chain address to10009030; **30ed80** writes145 to10009000. Busy checks
include VIF1/GIF/VU state. `30ea38/30e9f0` are critical-section helpers, not
DMA-start functions. `316b88` cache synchronization and ring advancement alone
would not have been sufficient evidence of hardware submission.

The upload producer **317208**, called at **311370** during renderer
initialization, writes DMA CALL to **442170**, followed by BASE/OFFSET and
MSCAL0 commands. Original embedded MPG headers address the following chunks:

| Source VA | Micro PC | Instructions | SHA256 |
|---|---|---:|---|
|442180|000..0ff|256|4af35729b5ac7753e65b730f491fcd107e7978ce87a6ccca9f711702ca830e4e|
|442988|100..1ff|256|0950571ea077b21f9f6dbb54b5463f71789895062c75c90ae0a94bdef3ab92ff|
|443190|200..2ff|256|f9ef7bfe3214431a925e1d4b2dce3fe73914d2819e7f4108e7fbc107ee52ab1a|
|443998|300..3ff|256|See exact hash in elf-functions.json|
|4441a0|400..4c8|201|See exact hash in elf-functions.json|

This establishes the actual **CPU upload address** beyond mere compatible
instructions. It is not an independently captured residency result and does
not close deferred GRASS2 work. Only the water-relevant entries were decoded:
00f strip processing,36a selector,37c/377 primary/secondary state,3dc..3f1 puddle
UV rebasing, and the associated output/XGKICK path.

At strip entry00f, XTOP locates four-qword input records. The code transforms
positions, produces STQ/color/XYZF output and applies copied control-bit ADC
suppression to both streams. Static XGKICK at micro PC0fa is the final GIF
operation in the decoded representative path. Selector3 invokes packet-local
integer UV rebasing; it is not vertex-wave synthesis. GS state transfers are
compatible with the two context templates decoded above.

**UNKNOWN LINK:** exact live upload completion/residency, current micro-RAM
contents, active branch/LOD and final captured GS state for a visible Turkey3
puddle. No emulator frame or source preview certifies those runtime facts.
The recovered CPU producer, texture/mode association, upload address, state
words and DMA start are **CONFIRMED_BY_EXE**; the uncaptured executed VU output
remains a conditional static program contract.
