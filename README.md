# AutoNav

Automates nav mesh generation for Source Engine games during compile-time.

Download: [see the release page](https://github.com/The-Orange-Toolbox/AutoNav/releases)

## Installation

### Using with CompilePal
AutoNav is packaged as ready to be used in CompilePal. Follow these quick steps to install it:
- Copy the AutoNav folder into "Compile Pal 02x.xx/Parameters"
- Restart CompilePal.
- From the CompilePal UI, use the "Add..." button to add AutoNav to your list of executables.
- Tick the checkmark to have it run on your next compile.

### Using with Hammer (expert compile)
The executable can be used standalone without any of the other files it is bundled with. Follow these quick steps to add it to your Hammer compile:
- Copy the AutoNav.exe from AutoNav/ to your bin folder (e.g. steamapps/common/Team Fortress 2/bin, or any prefered folder).
- In Hammer's expert compile window, use the "New" button to add a new command.
- For the command, click the "Cmds" button, select "executable", select the location of the AutoNav.exe.
- For the parameters, add `$file --exe $game_exe --game $gamedir` into the text field. (A path to the compiled `.bsp` also works, as long as it sits in the game's `maps` folder.)
- Use the "Move Up"/"Move Down" buttons to order the command properly (recommended to be placed after the copy command).
- Hit "Go!" and compile away!

### Using with command line
Run the executable with `AutoNav --help` for complete information about its usage.

## Console mode
By default AutoNav relaunches the game with `-hijack` and sends it commands through `+exec`. Some games cannot be hijacked; for those, add `--console rcon` (talks to the game over the network) or `--console auto` (picks by what the game supports). Games that must be launched through Steam also need `--steam` and `--appid`.

<!--- start txt omit -->
## Building from source

```bat
build.bat
```

Produces `dist/AutoNav-v<version>/` with a standalone one-file exe, the VGCT
sidecar, and the CompilePal plugin configuration, plus a zip of the lot.

## Running from source

```bat
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python src\__main__.py mymap --exe "…\hl2.exe" --game "…\tf"
```

Tests:

```bat
.venv\Scripts\python -m unittest discover -s tests
```

## Documentation site

The documentation website is generated from this README, the argument parser,
and the CompilePal and VGCT definitions, and is published to GitHub Pages on
every push to `master`. To preview it locally:

```bat
.venv\Scripts\pip install -r docs\requirements.txt
.venv\Scripts\python docs\tot_docs.py serve
```

## Project layout

```
src/__main__.py       CLI
src/nav_generate.py   launches the game, generates the nav mesh
tests/                the VGCT sidecar
plugins/vgct/         VGCT tool definition, and the schema it is
                      checked against at build time and in the tests
plugins/compilepal/   CompilePal plugin configuration
docs/                 documentation site generator (shared by every tool)
```
<!--- end txt omit -->

## License

GPL-3.0.
