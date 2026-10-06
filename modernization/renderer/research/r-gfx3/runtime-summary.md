# Human runtime results retained at closeout

The user reported A Stock PASS; B AF visually/technically PASS with unnecessary MAG alteration; C race FOV PASS and frontend preview isolation FAIL; D combined PASS except that same preview leak; E isolated one-draw shadow Off PASS; F pristine Reset with AF+FOV PASS. All refer to pre-fix DLL307a5fe4c83d95bd14d460cf767aa751e94b7f0a8e962c8c29c67681f2c17313 (1015808 bytes). Human visual judgments are supplied evidence, not inferred from trace counts.

Read-only digest rechecks 14 matching pristine sessions and26 frame captures from D:/Game/Master Rallye Pristine/MRRRenderer/logs. The main12 sessions063348 through070742 contain10189 frame summaries. The two later sessions071604 and071620 add40+354, totaling10583. Both scopes have zero Present errors and bypass_suspected always false. There are27 Reset records, all S_OK, with640x480 and1920x1027 destinations. Session/frame input filenames and SHA256 are in closeout-evidence.json. No raw logs or Broker dumps were copied into Git.

Source90 race and source45 preview share the projection returnRVA0x0013FA75 /VA0x0053FA75. This explains the old leak and motivates the final family gate. The digest uses logical/original payload_bits rather than the already overridden matrix. New candidate runtime is PENDING_HUMAN; the earlier F10 captures cannot prove either final fix visually.

Reproduce: python modernization/renderer/tools/summarize_closeout.py <external-logs> <external-Broker-2026-10-06> . Output is deterministic and read-only. Synthetic tests cover counter errors, bypass, success/failure Reset, malformed projections and source-angle reconstruction.
