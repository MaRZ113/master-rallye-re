# One next user test — paused current SpeedDial source

Do not change DLL/config or launch another copy of the game. This is a manual
read-only debugger observation; software breakpoints temporarily instrument
code and timing, but never change original EXE/assets or game data structures.

1. In the existing x32dbg session, attach/select the CURRENT MRallye process
   explicitly. If no current session exists, stop here and let root coordinate
   restart. Never reuse a previous PID or pointers. Enter Turkey3 with HUD
   visible. Keep original graphics settings and no restart while collecting.
2. In Script load `plate-checkpoint.x32dbg`, run it, then F9. The breakpoint
   checks the current owner AI slot0 vtable and current packet directly.
   It emits at most one semantic-matching record and disables itself at that
   first matching pause, or after100000 total interceptions. Nonmatching
   frontend traffic produces no records. It does not run any native function.
3. When paused at EIP0056D65D, save the debugger log and copy CURRENT values
   EIP,ESP,ESI,EAX and current PID. Remain paused. Run once:

```powershell
python ps2-research/pc-port/docs/hud-port1.1/paused-plate-probe.py `
 --pid <CURRENT_PID> --eip 0056D65D --esp <ESP_HEX> `
 --esi <ESI_HEX> --eax <EAX_HEX> `
 --output ps2-research/data/hud-port1.1/current-plate.json
```

Root can run this when supplied those values. Abort if checkpoint/class/span
validation fails; do not relax it to screen position or shared texture.
The original instruction check requires the matching breakpoint to be disabled
(automatic `bpd`); if it remains active manually `bpd 0056D65D` while paused.
4. Resume F9, press F10 once in the same race, and save that capture. Do not
   restart or exit until root validates the current packet and native
   SetTexture argument against the captured binding/generation. A later F10
   is corroboration, not automatically an atomic join to the paused frame.

No stock-vs-PS2 visual A/B is requested yet because replacement gates remain
closed. This one bounded observation determines whether an exact current
plate resource join is feasible without another broad reverse.

The script's commands use documented [conditional breakpoint control](https://help.x64dbg.com/en/latest/commands/conditional-breakpoint-control/SetBreakpointCondition.html)
and [safe dword reads](https://help.x64dbg.com/en/latest/introduction/Expression-functions.html),
which return0 for invalid addresses. Recipe/script syntax is documented and
statically inspected; it has **not** been executed in the live debugger here.
