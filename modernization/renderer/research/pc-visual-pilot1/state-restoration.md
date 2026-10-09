# Native-state safety boundary

This checkpoint performs **zero foliage state setters**. It does not change logical/effective shadows, material state, native draw arguments, draw order or draw HRESULT. Existing reflection/UI restoration remains unchanged. The new mock exercises production draw_indexed_at with requestedMode1 and diagnostics:one native draw,original failure HRESULT,zero render-state writes; adjacent/disabled-capture/unknown-build draws do not probe.

GetStreamSource/GetIndices/GetTexture references are released. Successful READONLY locks are unlocked before the draw, including index-lock failure/read failure/exception paths. Bounds arithmetic is64-bit; bad format,FVF,range,nonfinite content,WRITEONLY,dynamic and GPU-only resources fail closed for content evidence. Lock HRESULTs and unlock failures are recorded. An unlock failure permanently disables this probe for the device; no false Stock-equivalence or successful identity is claimed after such a native failure. The original draw is still attempted once and returns its actual result. Restart the game after this error.

A material RAII scope was deliberately not installed before live identity approval. Snapshot/apply/partial-apply rollback/exact restore/failure repair interactions for a future five-state override therefore remain NOT_IMPLEMENTED, not mock-certified PS2 behavior.

No resource-generation-only activation is cached. A fresh diagnostic reads current native binding and content; after recreation generation values differ, and missing registry identity suppresses content reading. Managed Reset survival alone is not immutable-content proof.
