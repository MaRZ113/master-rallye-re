# XmlData factory and virtual contract

## Registry

Retail `006F9414` points to a lazy registry wrapper (`004D98E0`). The wrapper
owns a vector object with begin/end/capacity pointers at +04/+08/+0C, holding
factory pointers. `004DEE20` searches factory class IDs at factory +04.
Game reset reinitializes the registry via `004D98C0 → 004DEF10` and engine
registration `0052D8E0`. The entire registration set is not named here.

Typed XML parser `004DFA00` reads the XmlData class ID, looks up the registry,
calls factory virtual +04 to construct an object, then object virtual +10 to
load the XML children. A missing factory fails this parse path; a random class
string does not automatically become opaque storage.

## Object virtuals verified for the mapped classes

| Slot | Use | Evidence |
|---|---|---|
| +00 | destruction | entry payload release calls deleting operation with argument 1 |
| +08 | clone | `004DEAA0` entry copying and `0065F170` edit-dialog cloning |
| +0C | ToXml tree | `004E0ED0`, Dump/object enumeration |
| +10 | FromXml tree | factory parser and local parameter-editor notification |

This is a partial virtual interface, not a complete named base class. Slot +04
of an object is not given the factory's construction semantics.

## Two contrasting classes

`gaIContDriverParams`: constructor `0042EC80`, vtable `0068FEFC`, clone
`0042EDA0`, ToXml `0042EEE0`, FromXml `0042F0A0`. Its custom XML fields are
emitted rather than promoted into generic Broker child records.

`gaVehicleOutputData`: constructor `00492020`, vtable `00690DB8`, clone
`00492AE0`. ToXml points to **`0042EE30`, which returns null**; FromXml points
to **`0042EE40`, which returns without processing**. Those tiny stubs were
checked in assembly as well as decompilation. This explains why root `CarN`
objects need not produce an XML continuation in Dump. It does not establish
that all race state can be saved by serializing these objects.

Broker getter `004D6FB0`/entry helper `004DDA10` can check class identity.
Typed XmlData ownership is separate from nested runtime references within a
subclass; those private layouts are not reconstructed in this phase.

The owner's existing Dump observations of XML continuations and CarN leaves
agree with these contrasting implementations. No new object editing occurred.
