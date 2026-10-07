# XML -> owner -> visual commands

All addresses refer to SLES_509.06 SHA256
`b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2`.
Labels are working descriptions, not recovered original symbols.

## Factory and lifecycle

`15b190` allocates prototype objects and appends pointers to the registry
held by `1fc760`. Constructors intern owner strings through `1d4040`, write
the resulting ID at owner +4 and AI vtable at +8. `1fc500` compares +4 while
walking the registry's begin/end vector. IDs are process-created identifiers;
the report does not invent fixed numeric owner IDs.

The active `EggLists_Version4` parser is `295d58`, including `en2d 2dGlobal`.
It reads name, model, matrix, key, flags and four AI/config pairs into a
`0xe0` template. The older `294b38/295428` parsers omit 2dGlobal and cannot
alone explain this HUD0 resource. XML matrix lands at template +90, model
at +30, key at +38; flags are +40, with global bit6 and Draw2D bit0.

`292a48` allocates the `0x7c` runtime entity, creates `0x90` en2d when
template Use en2d is true, copies the entire matrix to en2d +20, assigns
bank/key, maps flags and attaches it to entity +4c. Draw2D false yields mode0;
Draw2D true with global false yields mode1; true/true yields mode2.

The four AI records resolve through `1fc4c0`, which looks up the prototype
and invokes vtable +14 to clone it. Config calls +24 when an owner broker
exists. `21e620` stores the owner in entity +4+4*slot, then calls virtual
+34 with the entity. Vtables use eight-byte entries (adjustment plus
function pointer); generic C++ destructor entry is +c, schema +1c, update
+2c, initialize +34. Map slot +34 is `1461f8`, +2c is `147038`.
Exact generic scheduling of every owner is outside this admitted map;
`21eb38/21e7a0` are visual refresh, not evidence of the AI tick dispatcher.

`21e4f0` requests **deferred entity removal**, not ordinary visibility hiding.
`206218` replaces cached renderer data, not the visible flag. Ordinary en2d
visibility is bit0 of the eight-byte flags at +78. No parent pointer was
identified, so its layout entry remains null.

## HUD bank commands

`en2d` contains a vector of 52-byte commands. Each holds a u16 key vector,
bank ID, cursor XYZ, color and carry-cursor setting. `2062a8` sets command
bank, `205ce0` appends the authored integer as a u16 **key**, and `205dc8`
appends unsigned byte characters as u16 keys. `337a98` resolves the bank
through the resource manager, looks up the key in the bank table and indexes
12-byte image-vector objects. Triangle stride in memory is 72 bytes;
on-disk records retain UI1's variable-length texture names.

The UI1 path `380a08 -> 380998 -> 386d28` adds `.psb`, loads/checks F001/125,
reads mapping/images and constructs texture handles. The runtime path uses
that bank representation rather than treating XML index as a texture index.
Default glyph advance is recovered image geometry width (`3853d8`), not a
new field added to PSB. Null triangle handling remains opaque in the parser.

Authored HUD0 SpeedDial/Needle/progress sprites retain `hud/hud-template`.
There is no evidence that every authored model is globally replaced by
NEWHUD. `14de38` independently defaults rank to **HUD/newhud**, with Font No
`0x67`; `14dfc0` allows RankImageBank/Font No/Hud No overrides. Scene choice
and visual bank choice are distinct operations.

## Representative dynamic owner

`14e250` resolves `Race/CarN/Rank`, saves the entity and resolves the frontend
font resource. `14e360` polls the rank key; a change invokes `14e028`.
That function clears and rebuilds commands of the **same en2d object**:
select rank bank, append decimal rank character keys, measure width, move
cursor, switch to font bank and append the localized ordinal suffix.
The large digit mapping in NEWHUD is consequently exercised by ASCII keys;
it is not necessarily image index = numeric rank. Bank/key commands change;
there is no need to patch UVs or spawn a fresh rank entity for each value.
The complete locale/font layout is not reverse-engineered, so final text
rectangles and every HUD text owner remain UNKNOWN.

`14b290 -> 14b388` reads dial XML offsets, obtains en2d translation +50/+54,
and publishes Needle/Gear/Speed positions through the HUD broker. HUD0 dial
at (557,98) with zero Needle Offset initializes the needle at (557,98), even
though the needle's own authored position is (0,0). `14b6c8` writes that
translation to the needle visual. Its subsequent RPM rotation is outside
the offline fixed-rectangle prediction; the update address `14b8b0` is
confirmed by vtable bytes, but its full behavior is not claimed recovered.

## Scene visibility selection

`14dbd8` uses race state/NumPlayers/Replay to load HUD scenes. Attract mode
selects its own HUD; one player selects Hud/Hud0, two players select Hud/Hud1.
Replay affects the broker keys Hud/HudN/Visable (spelling retained).
`193138` supplies a true default when the visibility key is absent.
Map initialization removes the entity when its HUD is not visible.
Split-screen graphics and independent state between maps are unverified;
Map half extents and frame counter are shared globals, not per-owner fields.

`hud-runtime-map.json` includes all 49 authored HUD0 entities. Five HUD owner
vtables are resolved; other owner names are retained with null code records.
Final rectangles are null, and conditional estimates have explicit scope.
