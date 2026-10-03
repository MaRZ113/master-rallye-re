# Owner and smallest intervention

**CONFIRMED_BY_EXE:** homogeneity originates at the combination
`0x47B780` (Quick Race passes Car0 class) and `0x458090` (class-filtered
absolute-ID pool). This is model B, with the race owner's class argument as its
input. It is not class-local AI ID normalization.

The later CarClass write at `0x458456` is derived from the selected ID's registry
record. Changing only that class field would leave the wrong model/physics ID.
Changing the class argument would replace all AI choices and fail the one-AI
isolation requirement. The selected absolute-ID local is the narrower seam.

## Existing data/Broker initialization seams

Retail vehicles.xml supplies **named** physical families, not an ordinary
Quick Race participant preset. Frontend Broker values store the selected
absolute human ID and opponent count. Race/CarN keys are real executable
consumers, but stock Quick Race overwrites the generated AI ID/class/driver
before preparation. Adding XML initial values does not make them survive.
The inspected DataGame XML contains no Race/CarN participant class/ID preset
or Race/OpponentClass override. `MasterRallye.xml` does contain campaign Car0..3
ID/class/driver values; their `0x44A710` campaign consumer is a different mode
path, not a Quick Race AI override. Extra campaign slot declarations encountered
by the text search are deferred capacity clues.

`frontend.xml` defaults to mode1, one opponent and Track10; those are frontend
defaults, not four-car race capacity. The proof explicitly selects mode2 and
three opponents, using the unchanged stock count mechanism. It keeps default
Track10; no course content or selection code is changed.

Race/OpponentClass is registered in `0x4ABCE0` at wrapper+0x54. Its getter
`0x4AC160` and setter `0x4AC530` have no direct CALL sites in the pristine
disassembly; Quick Race instead uses `0x4AC730` for Car0. Thus a data-only or
existing Broker-init override for this path is **NOT ESTABLISHED**. No unsupported
XML field, new command or live process-memory write was added.

## Later normalization

**NO in the audited ordinary offline Quick Race path.** `0x44A510` derives
CarType/WheelType and colour from each CarID; `0x44ED50` binds named physics;
`0x4B6A00` uses that participant's family. A cross-check found24 direct CarID
setter calls and13 class setter calls. Other groups belong to frontend human
restore, campaign/network setup, alternate chooser `0x4584F0`, and an uncalled
result fixture. `0x46B47D` restores Car0, not every AI. These are not a later
ordinary AI class clamp. Indirect/scenario branches outside the tested lifecycle
are not asserted safe.

The AI's Car0-derived balancing scalar and the result-description class label
remain race-level assumptions, [documented separately](driver-coupling.md).
Neither is an identity or physics normalizer. Arbitrary class combinations,
game modes, IDs or counts are not claimed.
