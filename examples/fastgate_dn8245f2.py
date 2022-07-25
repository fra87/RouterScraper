#!/usr/bin/env python3
###############################################################################
#
# Example script for Fastgate Huawei DN8245f2
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2022 fra87
#

# Include repository directory to be able to include routerscraper folder
import pathlib
import sys
sys.path.append(str(pathlib.PurePath(__file__).parent.parent))

# Ignoring E402 (module level import not at top of file) since including
# routerscraper requires the sys.path.append above
from routerscraper.fastgate_dn8245f2 import fastgate_dn8245f2  # noqa: E402


def executeMain(host: str, user: str, password: str):
    '''Execute main function

    Args:
        host (str): The host address of the Fastgate router
        user (str): The username for the connection
        password (str): The password for the connection
    '''
    scrap = fastgate_dn8245f2(host, user, password)
    print(scrap.listDevices())


if __name__ == '__main__':
    if len(sys.argv) != 4:
        errStr = 'Error, wrong number of arguments\n'
        errStr += 'Call the script with arguments HOST USER PASSWORD where\n'
        errStr += '  - HOST     The hostname or IP of the router\n'
        errStr += '  - USER     The username for the connection\n'
        errStr += '  - PASSWORD The password for the connection'
        sys.exit(errStr)

    host, user, password = sys.argv[1], sys.argv[2], sys.argv[3]

    executeMain(host, user, password)
