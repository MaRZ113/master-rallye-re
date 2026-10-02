# XmlFilename is a dependency value

`CONFIRMED_BY_EXE` and `CONFIRMED_BY_CORPUS`.

Tag 0x0B stores an interned logical filename in an owned 4-byte wrapper. It is
neither an open file handle nor embedded XML. Loader `00522BD0` finds nonempty
XmlFilename entries whose **SaveFile matches the just-loaded source** using
case-insensitive filename comparison. It gathers a separate work list, registers
each dependency filename and requests `DataGame/<value>.xml` through `00522B60`
and `005FC950`. The new jobs use no reset and no immediate nested pump.

This corrects any interpretation of `005D1660` as a Load/ prefix test: it is
`_stricmp`, comparing **SaveFile/source identities** in this path. Names such as
Load/Dev or Load/Vehicles are a shipped-data convention, not the selection
condition. A differently named key with the same type/source could participate.

Retail Game.xml has 22 dependency Values spanning dev, Input, Video, audio,
Frontend, vehicles, Editors, Drivers, Cameras, Progress, DefaultOptions and
other config families. These anchors connect file archaeology to actual consumer
code, rather than merely matching executable text literals.

Game serializer mode 1 can preserve these references when save flags/group
match. Options/PlayerState modes have no general exclusion for tag 0x0B.
Mode 4 specifically skips XmlFilename. Editing a dependency value could change
later loading behavior; no such edit is authorized or implemented here.
