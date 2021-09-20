import os
import argparse
import traceback
from datetime import datetime

from _constants import *
from nav_generate import nav_generate


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Automates building cubemaps in-game.')

    parser.add_argument('input', metavar='path', type=ascii,
                        help='The path of the BSP to build.')
    parser.add_argument('-e', '--exe', metavar='path', type=ascii, default='',
                        help='Where the game .exe is located)')
    parser.add_argument('-g', '--game', metavar='path', type=ascii, default='',
                        help='The mod folder to be loaded')
    parser.add_argument('-x', '--textmode', action='store_true',
                        help='Operates the game in textmode')
    parser.add_argument('--hijack', action='store_true',
                        help='Hijacks the current game instance ' +
                        '(must have been launched with "-usercon")')
    parser.add_argument('-v', '--version', action='version', version=VERSION)

    args = parser.parse_args()

    print('{org} - {name}.exe ({date})\n'.format(org=ORGNAME,
                                                 name=NAME,
                                                 date=BUILD_DATE))
    gameExe = os.path.normpath(eval(args.exe))
    gameDir = os.path.normpath(eval(args.game))

    try:
        initial_time = datetime.now()
        nav_generate(eval(args.input), gameExe,
                     eval(args.game), args.hijack, args.textmode)
        print('Generation complete!')

        elapsed_time = datetime.now() - initial_time
        elapsed_secs = elapsed_time.total_seconds()
        print('{:.1f} seconds elapsed'.format(elapsed_secs))

    except Exception as e:
        print('There is a problem with ' + NAME)
        print('Please report issues here: ' + URL + '/issues')
        traceback.print_exc()
        print(e)
