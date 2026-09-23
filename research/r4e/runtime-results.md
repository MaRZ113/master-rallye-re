# R4E human runtime results

The project owner tested the five controlled Astero candidates. These are human in-game observations, recorded separately from the original pre-runtime candidate metadata. No screenshot or game asset is committed.

| Candidate | Result | Observation |
|---|---|---|
| E1_uv | **PASS** | Sticker visibly shifted toward the door edge; visual geometry unchanged. |
| E2_normal | **INCONCLUSIVE** | No clearly visible difference identified; limited edit does not establish whether runtime consumes the edited normal buffer. |
| E3_color | **PASS** | Localized darkening near front edge of hood/grille; agrees with stage-0 diffuse modulation. |
| E4_alpha | **PASS** | Windscreen became opaque; confirms serialized flag-to-runtime alpha shader path. |
| E5_python_sma | **PASS** | Original game accepted archive, loaded Astero, and displayed E1 UV modification. |

E1 confirms same-topology UV writing. E3 confirms that edited DX vertex colors reach runtime diffuse modulation. E4 confirms that the serialized alpha-family enable flag controls the windscreen alpha path. E5 confirms the Python full-tree Data.sma workflow with one controlled override: the game accepted it and loaded the E1 edit.

E2 is **INCONCLUSIVE**, not a failed normal writer. Eight of 192 chrome draw normals at about 15 degrees provided insufficient visual contrast. A stronger all-normal probe is prepared in R4E.1.

E5 proof applies to a complete original extracted tree plus controlled override. It does not establish acceptance of sparse, malformed, or arbitrary archives. Candidate hashes and structural reports are in `runtime-results.json`. The SHA-256 of the owner's tested E5 archive was not supplied; the local E5 hash records generation, not byte identity with the tested archive. Generated game files remain ignored under `.research-output/r4e/runtime-tests`.
