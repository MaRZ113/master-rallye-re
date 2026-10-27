# Results Names and Frontend Presentation

Open Vehicle Studios → Vehicle Details / Race HUD. Driver / Results Name changes
one fixed per-vehicle Results label; it does not change DriverID, AI behavior,
manufacturer/model, or native human/network names. The row uses the actual32×16
icon, enlarged for inspection. Font/layout/time are illustrative. Enter printable
ASCII (1–64), Apply Results Name, Save. Undo/Redo and Restore Results Name are targeted.

Open the Frontend Presentation tab → Open Frontend Presentation. This controls
the large rotating menu model, not icons or gameplay. Original/Modified/stock
NewRav comparisons share the source scene and4:3 projection. Vertical offset
±1.5m is a conservative SDK guard, not an engine limit. Positive raises the car
by lowering a private camera target; it does not raise the body or wheels.
Auto Frame returns a draft matching NewRav's lower geometry baseline. It does
not scale different cars to the same size. Change the field while Live3D Preview
runs, then Apply to save. Inspect cancels the draft; Reset original, Undo/Redo,
Save/reopen and Build use the shared project history. Close ends the owned viewer.

Only uniquely namespaced qualified addons currently support native frontend
build overrides. NewRav is read-only; stock framing build is not qualified.
The full source vertex viewport envelope is measured. Dashed panel guides are
illustrative, not recovered scissor bounds. Windows/D3D9 material rendering and
rest poses are not proof of in-game D3D8 parity, spinner dynamics or widescreen
proxy behavior. Verify the isolated candidate in-game later. Source hashes
reject stale appearance versions; requalify conflicts instead of silently
reapplying an old correction. Race geometry/physics/audio/camera assets stay unchanged.
