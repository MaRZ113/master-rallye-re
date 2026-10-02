# Editor edits, commit and cancel

Static reconstruction only. No edits/commit/remove/save were executed.

## Correct the UI attribution

Broker Editor's own dispatcher `0065EC40` has New(5), Edit(6), Copy(7), Remove(8),
Branch Options(9), branch Delete(10), Refresh(4) and Dump(2). It does **not** have
a top-level “Commit Changes” command. That exact label belongs to the generic
parameter/tree editor menu `006644C0` (local IDs 7 Commit, 8 Cancel). Earlier
R-DEV prose conflated the two UI layers. Broker's value dialog and its embedded
parameter editor communicate through local notifications `0x40B/0x40A`.

## Live Broker acceptance

`0065F170(path, copy_mode, existing_mode)` allocates a temporary 0x8CC value
dialog, copies the selected payload/flags/SaveFile and remembers scope/revision.
XmlData is cloned through virtual +8. Acceptance is gated by dialog +0x20.
Then a typed manager setter writes the live entry; flag setters copy all three
save choices, revision is explicitly set to old+1, scope is assigned, SaveFile
is assigned, and the filename is registered. UI rows are rebuilt.

Edit can remove the old selected key before writing the accepted path (rename).
Copy keeps that removal branch disabled. Remove `0065EC40 case 8 → 004D8D40`
resets the live slot immediately. Branch Options `006608A0` updates selected
prefix entries' checked flags and writes the dialog's SaveFile ID unconditionally.
These operations are not observational and are excluded from the trigger.

No direct serializer, async file queue or disk writer is on the mapped ordinary
value-acceptance chain. Persistence remains separate, but a normal gameplay save
can later serialize changed eligible live values; “no immediate disk write” is
not a guarantee that a live edit can never become persistent.

## Embedded parameter edits

`00660D80` handles the Edit Parameters dialog. OK first calls `006615F0`, then
sends `0x40B` to the registered parent; Cancel/window close sends `0x40A`.
The Broker value parent `00671570` handles `0x40B` by serializing its temporary
manager with mode 0 and passing the tree to its local XmlData FromXml virtual.
`0x40A` clears temporary entries. This is in-memory object editing, not a file
save. The generic menu Commit/Cancel dispatch is documented separately below;
the class callback, not the menu word, determines what gets mutated.

The parent acceptance gate is required before `0065F170` changes the shared
Broker. This does not prove every other editor's Cancel rolls back every
subclass side effect. Object-specific FromXml/commit consumers need separate
audits before editing runtime objects. Open, select and Dump remain separate
from all mutation operations.

## Retail generic menu is largely dormant

The owner constructed by `006643B0` installs vtable `0069CF80`; its message
method is **`006645C0`**. The WM_COMMAND branch masks LOWORD, accepts 0..8,
then jumps through **`00664718`**, a nine-entry table. Entries 0,1,3,4,5,6,7,8
all point to **`00664713` (POP ESI; RET 0x10)**. Only entry 2 points to the Exit
handler `006645E7 → 00664440`. Therefore the mapped retail owner's menu IDs
**7 Commit and 8 Cancel do nothing**; no typed mutation, revision change or disk
IO follows those cases. This was checked in assembly and by reading every
table word, not inferred from Ghidra's reduced switch decompilation.

On closing a dirty generic editor, `00664440`/the SC_CLOSE branch can instead
ask “Accept Changes Made?” and invoke model virtual +34/+38 for Yes/No. Default
EditTool model vtable `0069D144` uses `00674600/00674610`; the Game-labelled model
`0069D0F0` uses `00676580/00676590`. All four are empty return stubs. This is
separate evidence of dormant base-provider callbacks, not permission to edit
every possible subclass. The parameter dialog `00660D80` is another UI owner
and its OK notification is active as mapped above.

This disproves the broad earlier implication that a menu labelled Commit
necessarily commits live Broker changes. The active Broker value OK path does;
the mapped retail generic top-level menu Commit does not.
