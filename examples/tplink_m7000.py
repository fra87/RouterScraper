#!/usr/bin/env python3
###############################################################################
#
# Example script for TP-Link M7000
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2022 fra87
#

import sys
from routerscraper.tplink_m7000 import tplink_m7000


def executeMain(host: str, user: str, password: str):
    '''Execute main function

    Args:
        host (str): The host address of the Fastgate router
        user (str): The username for the connection
        password (str): The password for the connection
    '''
    with tplink_m7000(host, user, password) as scrap:
        print(scrap.getSmsList())


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
