# Native Quick Race opponent selector

R-UI1 is independent, starting at COMMON_BASE
8a17f2ddf59d81dd8f4f75e8c7601d61becc4c10. No R-AI2.1 merge or randomizer DLL.
Status: READY FOR HUMAN RUNTIME. See [machine map](opponents-ui-map.json).

The screen owner is gaFEScreenQuickModeSelectAI: factory479A90, constructor
479BB0, tick47A070. Constructor builds four native StringLists; only Opponents
is extended. It asks gaLocal485CF0 virtual+0C ->485BB0 ->485C20 for bank0x40.
All six authored language tables already contain indices0..6. Existing row
stride12 stores bank,index,string-pointer. Languages are English(default),
German1, French2, Italian3, Spanish4, Portuguese5. Original string bytes/font
encoding are reused, without translation, XML overlay or new localization.

| Visible English label | Menu index | Published AI count |
|---|---:|---:|
| ONE |0|1|
| TWO |1|2|
| THREE |2|3|
| FOUR |3|4|
| FIVE |4|5|
| SIX |5|6|
| SEVEN |6|7|

QuickModeSelect.xml binds gaFrontendMultistateAI to
Frontend/QuickModeSelect/NumOpponentsList, NumOpponents and NumOpponentsText.
454290 loads those pointers. 454610 dispatches native UI control2/3 to
454730 decrement /454870 increment. Both use actual list length and clamp,
without wrapping. 454920 reads the selected string into CurrentText; invalid
index produces blank text rather than an unchecked string access. Arrow
graphics/status use gaFrontendArrowAI44B800; underlying input routing is unchanged.
Actual physical keyboard and mouse interaction remains part of the human test.

47A120 sets LeftArrow2-3 for mode1,index>0; RightArrow2-3 for mode1,index<2
in stock. Only the latter bound becomes6. Other Mode, RaceDifficulty and
CountdownDifficulty bounds2 are different selectors and are untouched.
Focus/button index6 is a widget ID, not participant count.

Next47A070 ->47A8C0 publishes index+1 via4AE120 to
Frontend/QuickRace/NumOpponents. This is distinct from the currently browsed
zero-based index. Confirmation47B040 reads count-1 from the same localization
bank, with no max3. Start47B780 reads the numeric count twice and, for one human,
publishes NumCars=count+1. Its CALLs47B88A/47B8DD and chooser47B96E remain original.
Three therefore stays three AI; Four is four AI, without a hidden override.

Data-only extension is insufficient:479BB0 constructs/replaces the Broker list
from native code each screen entry. XML binds it but supplies no authored label
list. The patch uses this existing mechanism, not a replacement UI.

Persistence is stock: DataGame/frontend.xml defaults count1, SaveOptionsFalse,
SavePlayerStateTrue. Entry47A540 restores index=count-1, repairing zero to1.
Next47A8C0 invokes native PlayerState3 save522D80/5229B0. Cancel(-3) skips commit.
Uncommitted browsing can be discarded on re-entry; committed count is reused
when track/vehicle/difficulty changes and through the native save/load mechanism.
New1..7 process-restart persistence still needs human confirmation. Stock has no
extra upper clamp here; manually corrupted counts outside1..7 are not supported
UI inputs and no new save-validation subsystem is added.

Layout uses the original Font2/text element and arrows at x331/x587, unchanged
alignment and offsets. English new labels are no longer in character count than
THREE; all localized labels are at most7 bytes. Glyph widths/clipping and visible
rendering have not been asserted by static state; test them in the human UI pass.

Integration contract: UI publishes numeric AI count. Capacity code determines
whether humans+AI fits proven storage; randomizer receives active AI count and
knows no UI strings. Seven same-class T1 AI also exhaust the ordinary unique
T1 pool with an ID0 human. A later mixed-roster integration must solve that
separately; capacity PASS alone does not make this Stock UI candidate safe at7 AI.
The Four race proof is one human only; higher counts or two-human extensions are
menu-only in this independent branch.
