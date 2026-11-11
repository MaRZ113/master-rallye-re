# ForesterSTI PS2 race and lamp geometry

Base: c0dd9d0, owner-selected host-roster-v4-01 with published Renderer
e366951f122f4b39917a09ea9c77e4e5cd0c3c1108fec3880bbcce3b6fd3bec9 and loader
80561f219e342d80f5f81997e6b0a61d56dd870eb90b4059333509f3bf175c94.
The source host and published builds are preserved.

## Private-tree startup

FleetDamageState previously required a material/reference observation before
admitting private-tree records. SDK vehicles can start directly in that tree,
so neither selection nor observation could initialize the reference. This
is independently reproducible with all fourteen actual Forester source draws.
The initial observation now requires exact ordered original positions and
UV/winding even in a private tree. Later observations still require the same
owned material/token; deformed first observations are refused. The existing
whole-body certificate, queue cohort, lifetime and damage checks remain.

The previous c0dd9d0 correction excluding brake-only records from the chassis
certificate is retained. No class, ID, physical record or MODEL menu mapping
changes. This is a general exact-source initialization correction.

## Original PS2 conditional lamps

`tools/forester_ps2_lamps.py` reuses the accepted PS2 source prototype,
strip decoder and SDK native state writer. FORESTER/CAR.PSM root.15.0.0
supplies the 16-vertex/12-triangle ON core; root.15.0.1 supplies the
36-vertex/32-triangle glow. No position scaling, fitting or guessed geometry.
UV uses the established PS2 runtime 1-v orientation; original vertex colours
come from the accepted converter. Body/off-state triangles and collision
bytes are checked unchanged. Both active and manager/base resources are
updated in a new private candidate, so later Manager Apply retains the fix.

The native model binds ordinary PC lamp textures. Optional PS2 textures are
used only with a successfully rendered same-owner PS2 body in the current
frame and the
existing BrakeGlow config opt-in. PC selection and fallback retain PC art.
MR-ADDON-LAMPS 2 adds ANY_MODEL / PS2_MODEL_ONLY texture policy; the reader
continues to accept v1. Other demo lamp roles keep their accepted policy.
A bounded current-frame presence ledger keeps participants independent across
opaque-body and alpha-lamp ordering; another participant cannot enable the
wrong car's PS2 art. Device/reset/frame changes discard these observations.
MODEL selects geometry; BrakeGlow controls PS2 lamp art. Changing BrakeGlow
requires a game restart, as before. No loader change is needed.

## Checks and owner gate

The overlay build runs baseline/PS2 CTest and existing Python checks. Targeted
native tests use actual lamp geometry, both v3 config values, and all fourteen
Forester body draws. Private initial exact observations pass; initially
deformed geometry and foreign material fail. Authoring checks preserve the
body, UV, collision, native roster, loader, saves and configuration.

Owner check on the new private candidate:

1. ForesterSTI ID30: select PS2 in the menu, start Quick Race, verify the actual
   PS2 body instead of PC fallback, then check braking and damage/glass.
2. Select PC and repeat braking: PS2 lamp geometry with ordinary PC texture.
3. Restart with BrakeGlow=0, then 1: PC art remains PC; PS2 selection follows
   the switch. Check one existing demo car for unchanged lamp behavior.

These are pending gameplay checks. Offline source/geometry/native-state
evidence is not a claim that this candidate has passed a real race.
