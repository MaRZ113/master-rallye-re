# Static versus runtime ledger — awaiting human captures

There are **no Master Rallye runtime captures in this phase yet**. Native-test
JSONL is synthetic and cannot fill the runtime column. Original R-GFX1 findings
remain unchanged; contradictory observations and their evidence go here.

| R-GFX1 input / hypothesis, VA / RVA | Observation needed | Current runtime status |
|---|---|---|
| Factory0055905B /0015905B uses SDK120 | Session factory SDK, correct EXE/proxy/system path | PENDING_HUMAN |
| CreateDevice0055ACD7 /0015ACD7 | Actual presentation/behavior flags and returned HRESULT; compare device-creation.md | PENDING_HUMAN |
| Clear0056BA1A /0016BA1A before BeginScene0056BA23 /0016BA23 | Complete ordered frame API list, counts and caller matches | PENDING_HUMAN |
| Camera005614A0 /001614A0 | VIEW/PROJECTION caller matches, raw matrices, viewport sequence | PENDING_HUMAN |
| Common mesh00576970 /00176970 and0057F9A0 /0017F9A0 | Indexed draw caller matches; object identity remains ambiguous | PENDING_HUMAN |
| Billboards005641C0 /001641C0 | Appropriate dusty race, mapped draws, FVF/stride/state | PENDING_HUMAN |
| Shadows00587DB0 /00187DB0 | Visible stock projected shadows plus matched owner/state | PENDING_HUMAN |
| UI packet0056D110 /0016D110 | Menu/HUD/results capture with packet owner and ortho matrices | PENDING_HUMAN |
| EndScene0056CE60 /0016CE60, Present0055B0DE /0015B0DE | Ordered completion and HRESULT | PENDING_HUMAN |
| Mostly FVF; no mapped primary SetLight/SetMaterial/real PS requirement | Intercepted shader/light/material counts in complete captures | PENDING_HUMAN |
| Reset0055AE57 /0015AE57 | Native loss/reset/recreation progression | PENDING_HUMAN; optional |
| Raw children safe in reviewed flows | Owner coverage, unexpected QI/parent mismatch and bypass investigation | STATIC_INFERENCE; runtime pending |

Use callmap **return_rva** fields for matches, not the displayed CALL addresses.
New entries must identify capture filename/SHA, device/frame, sequence/draw, caller
and scenario. Distinguish CONFIRMED_BY_RUNTIME_TRACE (specific observed call/state)
from NOT_OBSERVED (bounded scenario) and HYPOTHESIS (semantic attribution).
No observed calls in one frame does not prove absence throughout the game.
