# Master Rallye Source Cooker 0.1.0

The Source Cooker prepares vehicle model resources for retail Master Rallye. It can either ask the original retail game to cook supported local GXM source, convert supported demo vehicle DX files, or validate already-cooked retail DX. Texture files are resolved separately and copied or encoded by the documented offline path.

The release contains tooling and documentation only. It does not include Master Rallye, demo files, or any game assets.

## Requirements

- Python 3.10 or newer. The tool uses the Python standard library; no third-party packages are required.
- Windows for the retail-native GXM workflow, because that workflow runs an isolated copy of the Windows game and manages Windows Junctions.
- Your own compatible Master Rallye retail files and your own source/demo vehicle files.
- For retail-native GXM, the supported retail executable SHA256 is `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. The isolated cook harness and its `Data.sma` must also match the hashes recorded by the tool.

Offline revision-131 conversion and package validation do not launch the game. The release does not promise support for unknown retail executable builds.

## Quick start

From the extracted release directory, check the commands:

```powershell
python tools/source_cooker.py --help
python tools/source_cooker.py --version
```

For your own vehicle folder, inventory and preview the selected strategy first. Replace the quoted folder with the folder containing that vehicle's files:

```powershell
python tools/source_cooker.py inventory --source "<your vehicle folder>" --family Forester
python tools/source_cooker.py plan --source "<your vehicle folder>" --family Forester
```

The paths in angle brackets are values you supply; they are not files shipped with the tool.

## Model and texture strategies

| Available input | Strategy | Result |
| --- | --- | --- |
| Supported `complete.gxm`, `car.gxm`, `wheel.gxm` source | `retail-native-gxm` | Prepares an isolated cook job for the original supported retail game. This is an orchestrator, not a GXM serializer. |
| Supported vehicle `complete.dx`, `car.dx`, `wheel.dx` at revision 131 | `offline-131-to-135` | Converts the supported vehicle DX grammar through the R-COOKER2 adapter. |
| Structurally valid vehicle DX at revision 135 | `pass-through-135` | Validates and copies the files unchanged. |
| Revision-127 DX without a usable source GXM set | unsupported | Refused; the tool does not guess a conversion. |

Texture handling is independent. A valid DXT is reused byte-for-byte. If a required DXT is absent and a supported GXI is present, the known offline GXI-to-DXT encoder may be used. The native runtime cache-miss path is not relied on to regenerate DXT from GXI. Portable packages contain no GXM or GXI.

## Native GXM cooking

Use a separate copy of the verified retail cook harness. Do not point the tool at the canonical game installation. First make a plan:

```powershell
python tools/source_cooker.py plan --source "<your vehicle folder>" --family Forester
```

Then create the isolated job. The example uses the already tested `Mercedes` harness namespace; select a namespace that matches the isolated harness profile you prepared:

```powershell
python tools/source_cooker.py cook `
  --source "<your vehicle folder>" `
  --family Forester `
  --retail-root "<your isolated retail harness folder>" `
  --runtime-family Mercedes `
  --output "jobs\Forester-native-cook"
```

Add `--launch` if you want the tool to launch the isolated executable and wait for it to exit. Otherwise start the reported `runtime\MRallye.exe` with that `runtime` directory as its working directory. In the isolated game, load the vehicle preview and then enter Practice/Quick Race so the runtime cooks `complete.dx`, `car.dx`, and `wheel.dx`. Close the game before cleanup.

The job copies the referenced authoring GXI files into its own mirror. It creates a historical-path Junction only when the path is absent, its parent already exists, and the target is that job's mirror. Existing directories, symlinks, foreign Junctions, and target mismatches stop the operation. The Junction is managed by Python and does not require a generated PowerShell script.

## Status, resume, and cleanup

Jobs can be inspected or continued after closing the terminal:

```powershell
python tools/source_cooker.py status --job "jobs\Forester-native-cook"
python tools/source_cooker.py resume --job "jobs\Forester-native-cook"
python tools/source_cooker.py recover --job "jobs\Forester-native-cook"
python tools/source_cooker.py cleanup --job "jobs\Forester-native-cook"
```

`resume` packages the cooked outputs when all three valid files exist. It validates the package before reporting completion. If outputs are still missing and a job-owned Junction is absent, `resume` can safely recreate it after checking the stored target and existing historical parent. A foreign link, ordinary directory, or target mismatch stops the operation. `recover` reconciles only an unambiguous live Junction and ownership record. `cleanup` is safe to repeat; it removes only a Junction recorded as created by that job and never deletes its target.

If you want to run the post-cook steps explicitly, `collect` (also named
`package`) assembles and validates the package. `validate-package` (also named
`validate`) checks an existing cache-only package without changing it:

```powershell
python tools/source_cooker.py collect --job "jobs\Forester-native-cook"
python tools/source_cooker.py validate-package "jobs\Forester-native-cook\runtime-package" --family Forester
```

Jobs use relative paths for files inside the job directory, so a prepared job can be copied or moved. Source and retail-template paths remain provenance inputs; those source files must still be available for a new cook.

## Portable package

A successful package contains the runtime resources under:

```text
DataGx/Vehicles/<family>/
    complete.dx
    car.dx
    wheel.dx
    required textures (*.dxt)
```

Package metadata stays alongside the resource directory. GXM, GXI, authoring mirrors, the retail executable, and `Data.sma` are not included.

## Evidence and scope

The native retail cook strategy has runtime evidence for the Mercedes harness and the Forester source model. Forester's current cook used a temporary `Mercedes` runtime namespace; its successful model, collision, damage, and driving observations do not prove authentic Forester physics configuration. Trooper and Forester also have separate runtime evidence for the minimal revision-131 to revision-135 conversion.

Broader corpus coverage is structural validation, not individual runtime testing. Not every GXM variant, model/physics combination, or source tree has been tested. Unknown grammar, unresolved authoring references, invalid DXT, unsupported DX revisions, and unsafe Junction states fail closed.

## License

The tool's original code and documentation are MIT licensed. Master Rallye and its game assets remain the property of their respective rights holders. No game assets are included.
