# Broker Editor

Retail command 0x27 opens the window through 0065E990. Constructor 0065E650, event handler 0065EC40 and edit route 0065F170 form the core path. The editor shares the live parameter broker.

The broker uses 0x1c-byte entries. Debug dump 00601D00 corroborates types including Bool, Float, Int, Matrix, String, StringList, vectors, MarkerListName and XmlFilename, plus save flags/scope/revision fields. The editor includes refresh/dump/help/edit/copy/Commit Changes/Cancel Changes/remove/update actions.

No direct file writer was found on the Commit Changes path. “Commit” is supported as an in-memory broker action; persistence is a separate Game/Scene XML Save operation. The constructor references DataEditors/BrokerEditorHelpInfo.txt through the generic resource reader, but the file is absent from supplied views.

The Editing/EditorsOpen name is used by camera/editor-list accessors, but its representation and registration policy remain UNKNOWN. Do not test edits on live authoritative data.
