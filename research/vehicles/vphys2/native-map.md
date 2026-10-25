# Retail native parameter semantics added in V-PHYS2

Exact EXE identity is pinned in README and all controlled replays. REA supplied
functions/xrefs/instructions; ignored `scratch/phys2` contains a complementary
Ghidra export for missing boundaries. Decompiled C is not original source.
Controlled replay means original x86 instructions with synthetic inputs, not
an actual race or a full replacement physics implementation.

| Site | Verified relation / scope |
|---|---|
| 0044C780 | Front menu ride min=-.15, max=+.15; fader=(base+saved+.15)/.30 |
| 004847C0, 00484A1C | Display Real*1000 as mm; original FMUL constant 1000 |
| 0044E490 | Saved ride delta = frontend Real minus named family base |
| 0044ED50 | Add native player changes, multiply gear array by 1+gear delta, publish CarN |
| 0044F334..0044F33E | Exact LEA/PUSH/CALL ABI, temporary parameter block and family string; optional SDK reference applied here |
| 00440770 | X=+/-track/2, Y=-effective RideHeight, Z=+/-WheelBase/2; radius and travel copied |
| 00446B10 | Contact normal load includes `(sprung_corner*spring_arm+unsprung)*g*upY` plus K*arm²*jounce, C*damper_arm²*velocity and opposite-side roll coupling |
| 00446D20 | Body suspension force includes `sprung_corner*g*upY + K*spring_arm*jounce + C*damper_arm*velocity` and roll coupling |
| 00446A10 | Relative suspension velocity derives from change of contact-plane samples and chassis velocity; it is not the menu delta |
| 004463B0, 00440D70 | Contact projection updates wheel jounce; positive value limited to MaxBounce |
| 00441270 | Render suspension displacement clamps between -MaxDroop and +MaxBounce, with chassis-up direction, then toe/camber/spin/orientation |
| 0043C350 | Configuration DriveType 0/1/2 -> internal differential mode 0/2/1 |
| 0043D480 | Internal0 transmits torque through centre and both axle splits (AWD), internal1 front only, internal2 rear only |
| 0043D6A0 | Limited-slip traction torque split uses bias ratio; conservative author guard [1,20], not an engine clamp |
| 0043C570..0043C606 | Crank torque = interpolated curve(RPM/revlimit)*PeakTorque*throttle minus omega*interpolated throttle/coast damping; cut drive term at rev limit |
| 0043DC50 | Piecewise linear torque curve with endpoint clamping |
| 00441240 | Brake and handbrake control multiply initialized wheel torque limits |
| 00440F70 | Front-wheel steering input copies controller+C; rear remains unsteered |

Mass and inertia relations from V-PHYS1 remain: sprung body mass excludes two
front and two rear unsprung masses; non-cuboid inertia is sprung mass times the
squared configured radius components. Native corner mass uses CG.z/Length,
not WheelBase. Front suspension application offsets are copied for all four
wheels in this constructor. Rear XML values are loaded but this does not prove
they are consumed independently later. No solver patches change these quirks.

The local symmetric preload estimate assumes upright body, equal left/right
jounce, zero relative velocity and established contact. It omits whole-body
pitch/roll balance, different support loads, tyre deflection, aero and terrain.
Spring/damper/travel changes therefore remain tunable prototype choices.

The reference adapter appends code to the existing sealed damage payload while
preserving its complete byte prefix. It changes only the one original publish
call and the selected scratch parameter block. Exact full family+NUL matching
prevents prefix collisions; state is not cached, so repeated publications do
not accumulate an offset. Registers/flags, stack ABI and balanced x87 additions
are checked by replay from the **original callsite instructions**. Foreign and
stock families pass through, including a longer shared-prefix family name.
