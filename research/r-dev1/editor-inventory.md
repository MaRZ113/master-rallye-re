# Embedded editor/tool inventory

005AF5C0 constructs these application-owned objects before the menu gate. Allocation size is not a complete layout or capacity.

| Tool/object | Retail allocation/constructor | Dispatch/open | Status |
|---|---|---|---|
| Flow Builder | 0x2c / 00662B20 | 0x30 → 00662D90 | native window/menu mapped; main-menu item absent |
| Large tree/editor object | 0x848 / 00660B30 | 0x3F and indexed family | identity/layout incomplete |
| Broker Editor | 0x20 / 0065E650 | 0x27 → 0065E990 | typed live broker editor; Commit not proven disk save |
| Debug log sink | 0x34 / 0064E4C0 | startup gate → 0064E5C0 | GDI logger window mapped |
| Egg Editor | 0x8c / 0065AAD0 | 0x2E → 00657FD0 | open path confirmed; inner behavior unknown |
| Particle Editor | 0xcc / 00656CD0 | 0x4A → 006557C0 | open path confirmed; inner behavior unknown |
| Marker Editor | 0x68 / 00654F50 | 0x3B → 0065B870 | open path confirmed; inner behavior unknown |

Camera constructors and 0066C180/0066C380 access Editing/EditorsOpen-related broker data. Shared list semantics and ownership remain UNKNOWN. Machine inventory is in editor-inventory.json.
