#!/usr/bin/env python3
###############################################################################
#
# baseScraper - Base class for Scraper classes.
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2022 fra87
#

from abc import ABC, abstractmethod
from typing import Any
import requests

from .dataTypes import (
        resultValue,
        resultState,
        loginResult,
        connectedDevice
    )


class baseScraper(ABC):
    '''Base class for the router scraper classes
    '''

    # List of valid services (to be overriden by the classes implementation)
    _validServices = []

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

    def _requestData(self, service: str, params: dict[str, str] = None,
                     autologin: bool = True, forceJSON: bool = False
                     ) -> resultValue:
        '''Request data from the router

        Args:
            service (str): The service to request
            params (dict[str,str], optional): Additional parameters to pass to
                                              the request. Defaults to None.
            autologin (bool, optional): If necessary, when user is not logged
                                        in try to perform a login and then
                                        retry the request. Defaults to True.
            forceJSON (bool, optional): If True, result will be an error if
                                        payload is not a valid JSON string.
                                        Defaults to False.

        Raises:
            ValueError: If service is not in the _validServices list

        Returns:
            resultValue: The result of the request
        '''
        if service not in self._validServices:
            errorMessage = (f'Invalid service requested: service {service}, '
                            f'valid services {self._validServices}')
            raise ValueError(errorMessage)

        # Build the GET URL
        GETurl = self._requestData_url(service, params)

        # Build the GET params
        GETparams = self._requestData_params(service, params)

        # Build the cookies variable
        session = self._session if self._session else None

        try:
            # Perform a request
            result = requests.get(GETurl, params=GETparams, cookies=session)

            # Check if request was successful
            result.raise_for_status()

        except (requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError) as e:
            return resultValue(resultState.ConnectionError, str(e))

        # Extract cookies from result
        cookies = result.cookies if result.cookies else None

        # Extract payload
        payload = result.content.decode(result.encoding)

        # Extract JSON representation if available
        try:
            jsonItm = result.json()
        except requests.exceptions.JSONDecodeError:
            if forceJSON:
                return resultValue(resultState.NotJsonResponse, payload,
                                   cookies=cookies)
            jsonItm = {}

        # Verify if this was a login request by the router
        if self.isLoginRequest(payload, jsonItm, cookies):
            if autologin and self.login() == loginResult.Success:
                # If the login was successful, retry the request
                return self._requestData(service, params,
                                         autologin=False,
                                         forceJSON=forceJSON)
            else:
                return resultValue(resultState.MustLogin, payload, jsonItm,
                                   cookies)

        return resultValue(resultState.Completed, payload, jsonItm, cookies)

    @abstractmethod
    def _requestData_url(self, service: str, params: dict[str, str]) -> str:
        '''Build the URL from the requestData parameters

        Args:
            service (str): The service being requested
            params (dict[str, str]): The additional GET params being requested

        Returns:
            str: The URL for the request
        '''
        pass

    @abstractmethod
    def _requestData_params(self, service: str, params: dict[str, str]
                            ) -> dict[str, str]:
        '''Build the GET params from the requestData parameters

        Args:
            service (str): The service being requested
            params (dict[str, str]): The additional GET params being requested

        Returns:
            dict[str, str]: The GET params
        '''
        pass

    @staticmethod
    def isLoginRequest(payload: str, jsonItm: dict, cookies: Any) -> bool:
        '''Check if the extracted data corresponds to a login request

        Args:
            payload (str): The raw payload of the response
            jsonItm (dict): The JSON representation of the response
            cookies (Any): The cookies in the response

        Returns:
            bool: True if the data corresponds to a login request
        '''
        return False

    @abstractmethod
    def login(self) -> loginResult:
        '''Perform a login action

        Returns:
            loginResult: The login outcome
        '''
        pass

    @abstractmethod
    def listDevices(self) -> list[connectedDevice]:
        '''Get the list of connected devices

        Returns:
            list[connectedDevice]: The list of connected devices
        '''
        pass
