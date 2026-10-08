# Next decision

1. **Turkey3 discrepancy understood?** Yes at source/content level:17 authored
   PS2 puddle mesh records with745 source faces have no corresponding surface
   in the compared validated PC compiled landscape. A live frame/mesh correlation
   is still missing.
2. **Primary difference?** Additional authored content plus PS2 material/draw
   behavior. Do not generalize: Italy/France water geometry is shared.
3. **Existing PC geometry sufficient?** France/Italy supply corresponding
   surfaces. It is insufficient for the recovered Turkey3 mesh set.
4. **Course SDK intervention?** Future Turkey3 visual surface conversion,
   material assignment, LOD/transform and scene delivery need a data interface.
   Water collision choices must remain separate from drawing.
5. **PC renderer material identity sufficient?** A universal material-token
   interface at final D3D8 draws has not been established. Offline matches do
   not solve that runtime interface automatically.
6. **Resources needing conversion?** Selected extra Turkey3 visual meshes,
   retained course WATER-TGA, common WATERSURFACE2 and, if needed, the common
   waterfall pair. No port/conversion is performed here.
7. **Real water reflection?** Two textures, normal-dependent UVs and additive
   puddle secondary blend are proved. A dynamic reflection capture/render target
   is not connected to the traced water texture slots. Global basis ownership
   remains open; complete reflection semantics are UNKNOWN.
8. **Proved animation/blend?** Puddle cached UV update, static auxiliary water
   frame callback, hardcoded waterfall dual scrolling; primary alpha blend,
   puddle FIX56 additive second layer, water alpha-based second layer. Clock
   units and inherited depth enable still need capture.
9. **Would WATER2 help?** A small targeted packet/micro-RAM/visible-frame capture
   would be valuable before implementation, especially inherited GS fields and
   live VU residency. It is deferred while surveying remaining visual areas.
10. **Single next phase:** **PS2-REFL1 — vehicle/environment reflection pipeline.**

REFL1 offers the highest survey value because it can classify a major visual
family and establish ownership of environment resources/global coordinate
bases that WATER1 deliberately did not expand. The choice follows the recovered
static water dependency boundary and the user's broad survey priority, rather
than simply following the old phase order. It does not authorize starting
REFL1 in this turn. WATER1 stops after validation, commit and handoff archive.
