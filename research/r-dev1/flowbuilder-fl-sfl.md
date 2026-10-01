# Flow Builder FL-to-SFL converter

The local command ID 10 calls retail 006635B0. It opens a dialog titled Load FlowFile To Convert with an FL Files (*.fl) filter, reads the selected input through 00677050, changes the suffix from .fl to .sfl, and serializes through 006773A0.

The output is a sibling path and the generic writer uses CreateFileA CREATE_ALWAYS. No in-function backup or overwrite guard was found. No conversion was run.

00677050 reads header/origin/spacing/dimensions and allocates width × height × 4 bytes for a grid payload. 006773A0 writes header and per-cell records through 0050C2F0, 0050C5C0 and 004F7900. 0050C2F0 maps integer column/row through origin and step floats and sets Y=0. Exact cell semantics/bit conversion are not fully established.

The converter item is absent from the 8.4.1 Flow Builder menu and present from 9.3.1 onward. Supplied assets shift from .fl in 8.4.1 to .sfl in later builds, providing independent corpus support for the format change. This does not assign SFL course/physics semantics.
