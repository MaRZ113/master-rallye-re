# Master Rallye Observatory — Quickstart

## Requirements

- Windows and Python **3.11 or newer** (standard library only).
- Pristine PC retail `MRallye.exe`. Demo and patched builds are rejected.
- Extract the Observatory ZIP into a writable folder, separate from the game.

## Capture → capture → diff

1. With the game stopped, back up your installation's `DataGame/dev.xml`.
   Set the existing Bool value **`Menues/Enabled` to `True`**, preserving the
   XML structure and other values. This enables the native developer/Debug
   window. `DebugWindow/Enabled` is not the verified startup gate. Use a test
   installation; no game XML is supplied or edited by Observatory.
   If no loose `dev.xml` exists, extract that file from your own Data.sma with
   Master Rallye-compatible asset tools first, then use the loose DataGame
   override. Do not modify the archive or use another build's XML.
2. Double-click **MRallye-Observatory.cmd**. It uses the Windows Python launcher
   `py -3`. Alternatively run `python mr_observe.py` from the extracted folder.
3. Select your retail installation on first run. Choose **Launch Game**, or
   launch it manually and choose **Recheck**. Retail verification is mandatory.
4. Choose **Capture Snapshot** and enter a label (Enter accepts `snapshot`).
   The Broker opens automatically if needed. Large Dumps normally display
   “Broker Dump is still processing...” — wait for “Fresh Broker Dump captured.”
   The command is never automatically resent.
5. Change game state using normal game controls, then capture again.
6. Choose **Diff Last Two**. Revision-only changes remain visible by default;
   the menu offers to hide them.
7. **Capture Folder** opens your results. **Status** shows full paths/hash.

Leave editor Edit/Remove/Save/Build actions alone. Observatory does not automate
gameplay or developer editing.

## Results and installation settings

The portable ZIP stores config in `observatory-data/config.json` and captures in
`observatory-data/captures/<date>/`. Each capture is a JSON + `.dump.bin` pair.
Keep both files unchanged. In the source repository, the existing ignored
`research-output/general-re/` storage is retained.

Use **Installation** to show/change/clear the selected game. Corrupt config can
be reset from the startup prompt or `python mr_observe.py config reset`.

```text
python mr_observe.py --version
python mr_observe.py capture frontend
python mr_observe.py show --last
python mr_observe.py diff --last
python mr_observe.py --verbose status
python mr_observe.py --debug capture diagnostic
```

If a previous Dump completed but publishing failed, use
`python mr_observe.py recover salvaged-session`. Recovery sends no commands,
saves the latest complete block/full raw buffer and clearly marks freshness as
**NOT command-proven**. It may salvage an older Dump. Do not retry Capture while
it is still waiting. A missing/incomplete Dump produces no pair.

## Safety and privacy

Observatory reads Master Rallye process memory and sends original window
commands for reviewed tool opening and Broker Debug→Dump. It does not inject
code, use WriteProcessMemory, patch MRallye.exe, change Broker values or
automatically save Game/Options/PlayerState. Opening Broker may register its
reserved in-memory SaveFile names.

Captures can contain runtime configuration, race state, filesystem paths and
value strings emitted by the original Broker. **Review captures before sharing
them publicly.** Nothing is uploaded automatically.

This is an observability/research tool, not a gameplay trainer or save editor.
It captures the original diagnostic text: empty slots are omitted and ordinary
numeric values have limited printed precision. The two files are checked and
published without overwriting earlier captures; they are not one atomic OS
transaction. Incomplete/corrupt pairs are excluded from history.

Supported retail SHA256:
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
No unsupported-build bypass is provided.
