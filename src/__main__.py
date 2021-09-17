import argparse
import traceback
from datetime import datetime

from _constants import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Automates building cubemaps in-game.')

    parser.add_argument('input', metavar='path', type=ascii,
                        help='The path of the BSP to build.')

    parser.add_argument('-v', '--version', action='version', version=VERSION)

    args = parser.parse_args()

    print('{org} - {name}.exe ({date})\n'.format(org=ORGNAME,
                                                 name=NAME,
                                                 date=BUILD_DATE))
    in_bsp = eval(args.input)
    out_bsp = eval(args.output) or in_bsp

    try:
        initial_time = datetime.now()

        elapsed_time = datetime.now() - initial_time
        elapsed_secs = elapsed_time.total_seconds()
        print('{:.1f} seconds elapsed'.format(elapsed_secs))

    except Exception as e:
        print('There is a problem with ' + NAME)
        print('Please report issues here: https://github.com/The-Orange-Toolbox/BuildCube/issues')
        traceback.print_exc()
        print(e)
