import os
import sys
import argparse
import traceback
from datetime import datetime

from valveexe import ValveExe

from _constants import *

def stdout(str):
    print(str, end="\n", flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Automates nav mesh generation in-game.')

    parser.add_argument('input', type=ascii,
                        help='The name of the map to build (without extension).')

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

    parser.add_argument('-v', '--version', action='version', version=VERSION)

    args = parser.parse_args()

    stdout('{org} - {name}.exe ({date})\n'.format(org=ORGNAME,
                                                 name=NAME,
                                                 date=BUILD_DATE))

    if (args.steam):
        steamExe = os.path.normpath(eval(args.steam))
    else:
        steamExe = None
    steamId = args.appid

    gameExe = os.path.normpath(eval(args.exe))
    gameDir = os.path.normpath(eval(args.game))

    mapName = eval(args.input)

    try:
        initial_time = datetime.now()

        valveExe = ValveExe(gameExe, gameDir, steamExe, steamId)
        stdout('Launching game...')

        valveExe.launch(['-windowed', '-novid', '-nosound', 
                         '+sv_cheats', '1', '+map', mapName])
        stdout('Waiting for map load...')

        valveExe.logger.log_until('Redownloading all lightmaps|connected\.')

        with valveExe as console:
            stdout('Generating Navigation Mesh...')

            console.run("nav_generate")
            valveExe.logger.log_until("\.nav' saved\.")

            if (valveExe.hijacked):
                console.run("disconnect")
            else:
                console.run("quit")

        del valveExe
        stdout('Generation complete!')

        elapsed_time = datetime.now() - initial_time
        elapsed_secs = elapsed_time.total_seconds()
        stdout('{:.1f} seconds elapsed'.format(elapsed_secs))

    except Exception as e:
        stdout('There is a problem with ' + NAME)
        stdout('Please report issues here: ' + URL +'/issues')
        traceback.print_exc()
        sys.stdout.flush()
        exit(1)

    exit(0)
