# Contradictions and apparent disagreements

## No proven source-level contradiction

The REA PC selector/registration agrees with the existing original-PC material
research. The decoded France1 compiled material flags select the generic
`_alphatest` family. PS2 `treeblend` remains a distinct mode with alpha
blending and masked depth writes. Different shader behavior on matched source
geometry is expected and is not a contradiction.

## Evidence precision issue at PC VA `0x005867a0`

REA can map the VA to the verified PE file offset but its Ghidra listing has
no procedure there. GNU objdump independently decodes the original bytes and
supports the state mapping. These facts are compatible: a tool may fail to
define a procedure while raw bytes still decode as instructions. The
revalidation report does not attribute an REA decompilation or function
boundary to this VA.

## Runtime ambiguity

The user-reported pilot mode outcomes do not uniquely isolate a cause: mode 1
and 2 both change alpha state; mode 1 and 3 both disable depth writes. The
reported disappearance under mode 3 implicates the depth-write-only change,
but because raw traces/screens are absent, it remains a directional
observation, not a contradiction or proof.
