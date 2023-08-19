#!/usr/bin/env python3
###############################################################################
#
# baseScraper - Base class for Scraper classes.
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2022 fra87
#

from abc import ABC, abstractmethod

from .dataTypes import (
        responsePayload,
        loginResult,
        connectedDevice
    )


class baseScraper(ABC):
    '''Base class for the router scraper classes
    '''

    def __init__(self, host: str, user: str, password: str):
        '''Initialize the object

        Args:
            host (str): The host address of the router
            user (str): The username for the connection
            password (str): The password for the connection
        '''
        self._host = host
        self._user = user
        self._password = password
        self._lastLoginResult = loginResult.NotLoggedIn

    @property
    def lastLoginResult(self) -> loginResult:
        '''Return the last login result

        Returns:
            loginResult: The last login result
        '''
        return self._lastLoginResult

    @property
    def isLoggedIn(self) -> bool:
        '''Get whether the object is logged in

        Returns:
            bool: True if the object is logged in
        '''
        return self._lastLoginResult == loginResult.Success

    @staticmethod
    def isLoginRequest(payload: responsePayload) -> bool:
        '''Check if the extracted data corresponds to a login request

        Args:
            result (responsePayload): The payload object to be checked

        Returns:
            bool: True if the data corresponds to a login request
        '''
        return False

    def login(self, cleanStart: bool = True) -> loginResult:
        '''Perform a login action

        Note: this is just a wrapper function used to track the last login
        status. Subclasses need to implement the _internal_login function
        that actually performs the login

        Args:
            cleanStart (bool, optional): Remove cookies and start from scratch.
                                         Defaults to True.

        Returns:
            loginResult: The login outcome
        '''
        result = self._internal_login(cleanStart)
        self._lastLoginResult = result
        return result

    @abstractmethod
    def _internal_login(self, cleanStart: bool = True) -> loginResult:
        '''Perform a login action

        Note: this function must not be used directly, but only through the
        wrapping login(cleanStart) function.

        Args:
            cleanStart (bool, optional): Remove cookies and start from scratch.
                                         Defaults to True.

        Returns:
            loginResult: The login outcome
        '''
        pass

    @abstractmethod
    def listDevices(self) -> list[connectedDevice]:
        '''Get the list of connected devices

        If there was a connection error the function returns None

        Returns:
            list[connectedDevice]: The list of connected devices
        '''
        pass
