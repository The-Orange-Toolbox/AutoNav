import os
import sys
import argparse

# Flush stdout/stderr on every line so output from nested libraries (e.g.
# valveexe debug prints) shows up immediately instead of sitting in a block
# buffer when the stream is piped/captured rather than attached to a terminal.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(line_buffering=True)
    except (AttributeError, ValueError):
        pass

from _constants import *

from totcommon.executable import TOTExecutable

from valveexe import CONSOLES, EXEC

from nav_generate import nav_generate


def resolve_map(target, mapsDir):
    '''Works out the (.bsp, map name) pair from either form of the positional.

    Hammer passes a bare map name ($file); VGCT binds the BSP port and
    passes the compiled map's path. Both have to land on the same pair, since
    the game is told to load the map by name out of its own maps folder, and
    the .nav it writes lands beside the .bsp of that name.
    '''
    target = os.path.normpath(target)

    if os.path.splitext(target)[1].lower() != '.bsp':
        mapName = target.replace(os.sep, '/')
        return os.path.join(mapsDir, *mapName.split('/')) + '.bsp', mapName

    bspPath = os.path.abspath(target)
    try:
        rel = os.path.relpath(bspPath, os.path.abspath(mapsDir))
    except ValueError:  # different drives
        rel = os.pardir

    if rel.split(os.sep)[0] == os.pardir:
        raise ValueError(
            'The game can only load maps out of its own maps folder, so the '
            '.bsp has to live there: ' + bspPath + ' is not under ' + mapsDir)

    return bspPath, os.path.splitext(rel)[0].replace(os.sep, '/')


def build_parser():
    parser = argparse.ArgumentParser(
        description='Automates nav mesh generation in-game.')

    parser.add_argument('input', type=ascii,
                        help='The map to build: either the path to its .bsp, '
                             'or just the map name (without extension).')

    parser.add_argument('-e', '--exe', required=True,
                        metavar='path', type=ascii, default='',
                        help='Where the game .exe is located')
    parser.add_argument('-g', '--game', required=True,
                        metavar='path', type=ascii, default='',
                        help='The mod folder to be loaded')

    parser.add_argument('-s', '--steam', metavar='path', type=ascii,
                        nargs='?', default=None, const=None,
                        help='Where the steam.exe is located')
    parser.add_argument('-a', '--appid',  metavar='N', type=int,
                        nargs='?', default=None, const=None,
                        help='The steam AppId to be launched')

    parser.add_argument('-c', '--console', metavar='MODE',
                        choices=CONSOLES, default=EXEC,
                        help='How to issue console commands to the game: '
                             '"exec" (default) relaunches it with -hijack '
                             '+exec, "rcon" talks to it over the network, '
                             '"auto" picks by what the game supports. Stated '
                             'rather than detected, so runs behave the same.')

    parser.add_argument('-v', '--version', action='version', version=VERSION)
    return parser


def main():
    args = build_parser().parse_args()

    with TOTExecutable(NAME, ORGNAME, URL, VERSION, BUILD_DATE):

        gameExe = os.path.normpath(eval(args.exe))
        gameDir = os.path.normpath(eval(args.game))
        bspPath, mapName = resolve_map(eval(args.input),
                                       os.path.join(gameDir, 'maps'))

        if (args.steam):
            steamExe = os.path.normpath(eval(args.steam))
        else:
            steamExe = None

        steamId = args.appid

        # Validate paths up front so misconfigurations report clearly
        # instead of surfacing as a cryptic WinError 2 from the launcher.
        if not os.path.isfile(gameExe):
            raise FileNotFoundError('Game executable not found: ' + gameExe)
        if not os.path.isdir(gameDir):
            raise FileNotFoundError('Game directory not found: ' + gameDir)
        if not os.path.isfile(bspPath):
            raise FileNotFoundError('Compiled map not found: ' + bspPath)
        if steamExe and not os.path.isfile(steamExe):
            raise FileNotFoundError('Steam executable not found: ' + steamExe)

        nav_generate(mapName, gameExe, gameDir, steamExe, steamId,
                     args.console)


if __name__ == '__main__':
    main()
