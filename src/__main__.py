import argparse
import traceback
from datetime import datetime

from _constants import *

import valve.rcon

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

    try:
        initial_time = datetime.now()

        server_address = ("127.0.1.1", 27015)
        password = "asdasd"

        with valve.rcon.RCON(server_address, password) as rcon:
            print(rcon("echo Hello, world!"))

        elapsed_time = datetime.now() - initial_time
        elapsed_secs = elapsed_time.total_seconds()
        print('{:.1f} seconds elapsed'.format(elapsed_secs))

    except Exception as e:
        print('There is a problem with ' + NAME)
        print('Please report issues here: https://github.com/The-Orange-Toolbox/BuildCube/issues')
        traceback.print_exc()
        print(e)
