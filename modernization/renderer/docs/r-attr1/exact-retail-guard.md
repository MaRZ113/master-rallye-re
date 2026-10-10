# R-ATTR1 — the specific Loading failure redirect

Target is the pristine retail EXE, SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`,
3,121,214 bytes, ImageBase `0x00400000`. Existing R-AI1.1 findings remain
read-only inputs: [Loading evidence](../../../../research/r-ai1-1/attract-loading-fix.md).
The specific control flow and complete 374-byte Loading function were reverified
against that binary and read-only Ghidra 12.1.4 exports in this task.

`CONFIRMED_BY_EXE`: Loading init VA `0x00464E40` / RVA `0x00064E40` tests the
pre-increment invocation counter at VA `0x006F6030`. Even invocations skip the
media check. Odd invocations decode a SETUP.DLL path, substitute the configured
CDDrive character and call stat; stat failure or signed size <= `0x20001234`
enters the failure branch at VA `0x00464F69` / RVA `0x00064F69`.

The complete original instruction `68 84 1F 6B 00` is PUSH imm32, the
Race/AttractMode key address. The original following calls set AttractMode true
and change native race type. The sole runtime replacement is
`E9 D8 FF FF FF`: JMP VA `0x00464F46` / RVA `0x00064F46`, signed displacement
-40. That is the stock success continuation, which publishes Race/Starter=1
and continues the original invocation counter and return. It is not a global
Broker override. The decoder, stat, threshold, race setup and counter remain.

Legitimate MainMenu update VA `0x004655E0` / RVA `0x000655E0` is untouched.
Its separate timer comparison at VA `0x00465694`, Bool setter call at
VA `0x004656B7`, and transition to native menu state 10 at VA `0x004656C1`
are unchanged. MainMenu initialization, including its original short idle
timeout on its own failed media check, is also unchanged. Attract chooser,
explicit native Attract requests, Race/Type, vehicle policy and normal player
configuration are not patched.

`CONFIRMED_BY_SYNTHETIC_TEST`: 60 native x86 Loading cases cover counters 0..5
with failed stat, zero/threshold/threshold+1 and signed-negative sizes, on
original and guarded code. Six actual native idle timer-branch cases cover
expired/nonexpired timers on both versions. Expired idle still writes Attract
true and transitions to demonstration state 10. No guarded Loading case writes
Attract false. This is not a human Restart/idle verdict; the new DLL's in-game
result remains PENDING.
