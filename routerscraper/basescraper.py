#!/usr/bin/env python3
###############################################################################
#
# baseScraper - Base class for Scraper classes.
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2022 fra87
#

class baseScraper():
    '''Base class for the router scraper classes
    '''

    def __init__(self, host: str, user: str, password: str):
        '''Initialize the object

        Args:
            host (str): The host address of the Fastgate router
            user (str): The username for the connection
            password (str): The password for the connection
        '''
        self._host = host
        self._user = user
        self._password = password
        self._session = None
