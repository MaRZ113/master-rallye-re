# R4E material authoring boundary

The executable maps serialized flag byte 0 to alpha enable, byte 1 to alpha blend versus test selection, and draw mask bit 4 to the environment capability. R4D.1 human M1/M3 confirms whitepaint and chrome helpers are gated by Reflections; M2 confirms source-alpha glass; M4 confirms active brake glow alpha.

R4E permits changing byte 0 between 0 and 1 on existing physical vehicle draws with alpha-test selector byte 1 already zero. It permits toggling only mask bit 4 on a draw with an existing slot-1 helper and no unrecognized mask bits. Texture slot strings, bytes 1-3, and all unknown fields remain untouched. Alpha test is engine supported but absent from the normal vehicle corpus and is not an authoring default. E4 tests disabling alpha on an existing Astero windscreen draw. Environment-bit switching has structural validation but awaits targeted runtime confirmation.

The Blender panel shows ordered slot 0/1, raw flags, alpha/env status and evidence; its helper mix is an approximate preview and does not claim D3D8 parity.
