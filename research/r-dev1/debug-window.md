# Debug window and message producers

0064E4C0 creates an application-owned log sink with a roughly 0x800-byte text buffer. Global formatter 004D0620 dispatches formatted output to the current sink's virtual method +4. 0064E5C0 creates a native window titled Debug using wsUIWindow; 0064EC50 uses BeginPaint/TextOutA, line splitting and a scroll offset.

The window is owner-drawn. No standard Edit child exists, so GetWindowText on the top-level HWND only returns the caption. It is not a DebugView/OutputDebugString path.

The gate at 005AFB20 reads Menues/Enabled and uses that value for main UI and a separate capability-checked Debug window path. DebugWindow/Enabled is registered at 004D7BD0 but has no consumer xref in all four EXEs. Previous human evidence enabled both values and observed the window; it does not isolate the gate.

Retail 0053C3F0 emits cache/source model messages; 0054D6E0 emits GXM build stages while calling stage functions for moSortPlane insertion, vertex welding, convex hull, BSP, cylinders, 2D geometry, object nodes, land database and optimization. 00586B70 emits shader-selection messages. Build-specific anchors and xrefs are in debug-message-producers.json.

The helper tools/scanner/r_dev1_debug_capture.py can enumerate windows and OCR the owner-drawn window using optional Tesseract. It sends no game input. Tesseract was unavailable in the analysis environment; OCR was not runtime-tested.
