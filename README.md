# Master Rallye RE

Master Rallye RE is an open reverse-engineering and modding project for the
2001 PC game *Master Rallye*. It provides tools and documentation for vehicle
and course editing, runtime inspection, asset conversion, and experimental
gameplay extensions. Original game files are not distributed here.

## Downloads

Stable and beta packages are published on [GitHub Releases](https://github.com/MaRZ113/master-rallye-re/releases).

### Master Rallye Observatory

Read-only inspection of the game's live Broker state. [Download v0.1.0-beta](https://github.com/MaRZ113/master-rallye-re/releases/tag/v0.1.0-beta) (pristine retail executable only). The standalone v0.2.2-beta candidate is being prepared and is not published.

**Quick Start:** extract the release ZIP, enable `Menues/Enabled=True` in your own `DataGame/dev.xml`, start the game, then run `MRallye-Observatory.cmd`. See the [Observatory guide](docs/releases/observatory-quickstart.md).

### Master Rallye DX Upgrader

Converts supported vehicle DX revision-131 files to revision 135. [Download v0.1.0](https://github.com/MaRZ113/master-rallye-re/releases/tag/dx-upgrader-v0.1.0). Retail testing covered the listed Trooper and Forester resources; see the [Quick Start and limits](docs/releases/dx-upgrader-v0.1.0.md).

### Master Rallye Vehicle Composer

Combines a retail vehicle carrier with a selected physics family and model donor, with compatibility limits that depend on the assets. [Download v0.1.0](https://github.com/MaRZ113/master-rallye-re/releases/tag/v0.1.0). Start with the [Vehicle Composer Quick Start](docs/releases/vehicle-composer-v0.1.0.md).

## What is already possible

- **Vehicle editing:** a Blender add-on imports vehicle DX files and supports tested same-topology edits to positions, UVs, vertex colors, normals, selected material state, and collision data. See the [Blender importer](docs/blender-importer.md), [vehicle materials](docs/blender-materials.md), and [DX writer](docs/dx-writer.md).
- **Course editing:** selected RaceTest logic fields, including StartArea and FinishArea data, can be edited and exported from Blender. Those edits were tested in-game. See [course race-logic authoring](docs/course-race-logic-authoring.md).
- **Runtime inspection:** Observatory captures and compares read-only Broker state. See the [Observatory documentation](docs/broker-observatory.md).
- **Asset conversion and inspection:** the library and CLI inspect supported game formats and convert selected resources; formats and writer limits are documented under [docs/formats](docs/formats/).

## Experimental work

These results are documented in the repository but are not combined into a public gameplay package.

- **Eight-car Quick Race:** manual in-game testing confirmed normal operation with 6, 7, and 8 total cars, including AI, physics, collisions, damage, HUD/progress, results, Replay, and return to the frontend. Support above eight is not established. Several courses need start-grid adjustments for clean eight-car starts.
- **Vehicle registry:** research builds have demonstrated additional vehicle identities, including a Mercedes ML-320. This is not a general-purpose vehicle-slot expansion release.
- **AI opponents:** research builds support mixed vehicle classes and Stock, Mixed, and Diverse opponent policies across tested modes and counts. No public randomizer package is available.
- **Quick Race opponent selector:** One through Seven can be selected in a research build. The full engine/UI combination is not a public release; higher counts require the separately tested capacity work.
- **Course start grids:** an eight-car audit is documenting course-specific start positions and clearances. It does not imply that every course is ready for eight cars without adjustment.

## For testers

Use GitHub Releases for public packages. Research builds may contain newer work, but they are separate from the released tools and may have narrower compatibility or test coverage. Eight-car racing is confirmed in development builds; a public tester package has not been published.

Review Broker captures before sharing them. They may contain game state, paths, or other local values.

## Blender and modding tools

The Blender add-on and command-line tools are built from this repository. See the [Blender importer](docs/blender-importer.md), [Vehicle SDK](docs/vehicle-sdk.md), and [format documentation](docs/formats/). The public Vehicle Composer package is a separate, retail-hash-locked tool; its release notes describe its tested combinations and limitations.

## Documentation

- [`docs/`](docs/) contains user and modder-facing technical documentation.
- [`docs/releases/`](docs/releases/) contains public tool guides and the release-page style convention.
- [`research/`](research/) contains detailed evidence, experiments, and historical findings. Research status does not by itself mean a feature is included in a public release.
- Cross-subsystem executable, Broker, AI, UI, and runtime research is kept in the relevant research areas; detailed evidence remains separate from public tool documentation.

## Development

Run the synthetic test suite from the repository root:

```powershell
python -m unittest discover -s tests\synthetic -v
```

Build the local Blender add-on ZIP:

```powershell
python tools/build_blender_addon.py
```

For library and CLI commands, run `python tools/mrtool.py --help` from the repository root.

## Game files and repository scope

Original executables, archives, assets, saves, and runtime captures are not included. Use your own game installation and keep generated research candidates outside the public package. Compatibility statements apply only to the builds and assets named in each tool's documentation.

## License

Original project code and documentation are licensed under the [MIT License](LICENSE). This license does not cover *Master Rallye*, its names, or its proprietary game files and assets.
