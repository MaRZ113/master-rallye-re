# Exactly one next deep phase: PS2-AMBIENT1

Reverse **gaEntitySpline course-object ownership and movement**, using the
airship, barge and dinghy cases as independent consumers of the same contract.
This selects a bounded subproblem within AMBIENT1; bird spawning and rigid-body
physics are deferred rather than silently folded into its first scope.

The unresolved causal question is: **how does the owner consume the named
MarkerList, evaluate its curve and timing, apply loop/trigger/rest/banking
settings, and publish the model's world transform?** XML alone establishes
inputs, not executed movement. Trace the factory/configuration/update and
transform consumer in the exact canonical ELF with the existing Ghidra bridge.
Then validate a captured runtime course/object state independently.

Inputs already exist: 24 explicit owner-bound placements on 17 courses,
24 referenced nonempty marker lists, exact named non-stub model resources,
serialized controls and paired PC scenery. ITALY3's trigger-enabled barge and
TURKEYW's trigger-disabled barge give a controlled contrast; France1's two boats
and FRANCEM's airship provide other family/loop/speed cases. Preserve original
assets and keep the next phase in the PS2 research folder.

This wins over the fixed Grass -> Water -> Reflections sequence for the next
reverse because a single identifiable runtime owner spans three prominent
object families and many independently authored paths. Grass has wider probable
pixel coverage, but its generation contract is less localized. Water is largely
already present as PC geometry/materials; Turkey3 remains an interesting
material-to-draw question. Reflection ownership is less evidenced. No claim
is made that boats contribute more pixels than all vegetation.

Defer PS2-GRASS1, PS2-WATER1, PS2-REFL1, PS2-CHECKPOINT1, PS2-DRESSING1,
smoke emission, BirdManager populations and physics until the spline contract
is closed. Do not implement a PC port during that reverse. PC embedded dinghy
geometry must be considered to avoid adding duplicate static scenery.

Already understood for future ports: PackFS named addressing, the static HUD
banks, PS2 minimap's ordered RaceLine consumer and PC SDK's ordered Marker Pos
XYZ. **PC-PS2MAP1** remains a future port backlog item. PS2-UI2.1's COP2 sprite
projection/video-offset gap remains deferred and does not reopen this survey.

CDELTA1 ends after its survey commit. This recommendation does not start
PS2-AMBIENT1 or authorize a renderer, SDK, asset or gameplay implementation.
