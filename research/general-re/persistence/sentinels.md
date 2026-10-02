# Reserved-looking names: actual consumers

## Separate interned copies

Literal-address xrefs are dominated by many per-translation-unit string-ID
initializers. A census validated `PUSH literal; MOV ECX,id-object; CALL intern`
and then followed **ID-object** references. Hundreds of literal refs are not
hundreds of independent runtime policy checks. Relevant retail examples:

| Label | ID object | Runtime consumer/context |
|---|---|---|
| __NO_SAVE | `006F9474` | entry constructor/reset, type-default metadata |
| __NO_SAVE / __NO_CHANGE | `0070AEE8 / 0070AEEC` | Broker opener registers SaveFile names |
| __NO_SAVE / __NO_CHANGE | application-local IDs | `005B16C0` whole-Game registry saver skips these groups |
| __NO_SAVE | edit-dialog local ID | blank per-value SaveFile choice |
| __NO_CHANGE | `0070AFC0` | `00673130` blank Branch Options SaveFile choice |
| __IGNORE | `0070AFA4` | `00671570`, temporary Broker→XmlData mode-0 conversion |
| __IGNORE | `0070AF84` | EGG property-dialog notification near `0066F0FC`, temporary mode-0 conversion |
| __IGNORE | `0070AF74` | multi-editor consumer near `0066DDEA`; full owner callback still bounded UNKNOWN |

## __NO_SAVE

Default SaveFile for fresh/reset entries with save bits cleared. Explicit whole
Game saving excludes that registry name. The generic Options/PlayerState modes
do **not** compare this sentinel, so an entry assigned it with those bits enabled
can still be selected. The usual transient behavior is the conjunction of
default flags and grouping, not magic string-only protection.

## __NO_CHANGE

Registered as a pseudo-filename and excluded by whole-Game registry saving.
In Branch Options, empty filename text assigns this ID. Crucially,
`006608A0 → 004D58F0` applies it **unconditionally** to matching entries; the
setter has no “keep old filename” branch. The recovered code does not prove a
read-only value, revision suppression, callback suppression or persistence-wide
veto. The apparent UI intention and any additional owner behavior remain unknown.
Do not use it as a safety guard for editing.

## __IGNORE

The Broker value-dialog callback `00671570` passes it to `005FE460(..., mode=0)`
and loads the returned tree into a temporary XmlData object. Mode 0 does not
apply the SaveFile-group filter. The EGG consumer uses a similar in-memory tree
conversion. Thus these are dummy grouping arguments on an unfiltered conversion
path, **not evidence of a global “ignore changes/save” policy**. The multi-editor
callback and application-local reuse are not assigned additional semantics merely
from the label. No __IGNORE SaveFile registry entry appeared in the supplied
runtime observations.

None of these names universally forbids typed Broker writes. The literal census
is a discovery mechanism; constructor/filter/assignment/consumer control flow
is the evidence for the above conclusions.
