# Physical pose reaches the actual entity world matrix

**174318** iterates registered props and calls **267f60**. It constructs a 4x4 matrix from body basis/pose:

```text
row0 = [right.x,right.y,right.z,0]   body+ec
row1 = [up.x,up.y,up.z,0]           body+e0
row2 = [forward.x,forward.y,forward.z,0] body+f8
row3.xyz = position - R * local_COM
row3.w = 1
```

Local COM comes from body+94..9c, position from+a0, and rotation from+bc. Original basis globals are positively initialized by21cec0; quaternion restore updates their world transforms with27c7a0. The diagnostic requires explicit COM and, for direct pose mode, explicit basis vectors. It never invents a model origin from a screenshot.

**267f60 at268108 calls1e3f50**, publishing the matrix to the body's Broker key. **265e80** constructs that key as **Physics/{entity name}/Transform**. Init creates/attaches the separate transform AI **265ae8**, whose initializer **265b58** uses the same entity-derived key and an initial en3d transform. This matches producer to consumer by exact key construction, not by neighboring matrix-like fields.

**265d18 ->1e36d8** retrieves the Broker matrix, then copies all16 original scalar words into **the same scene entity's en3d+20..+5c**. Translation ends at +50/+54/+58/+5c. The DelayInterpolation property manipulates en3d+74 high-half bit2; no interpolation equation is inferred from the name.

```text
integrated body x,q ->2670b0 R/bases
 ->267f60 world matrix ->1e3f50 Broker Transform
 ->same key in265b58 ->265d18/1e36d8
 ->same entity en3d world matrix
 ->shared entity model draw
```

The update and actual visual-matrix writes are **CONFIRMED_BY_EXE**. Authored selected prop models connect the chain as **CONFIRMED_BY_BOTH**. Live model movement and draw capture remain **NOT_PERFORMED**.
