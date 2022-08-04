#!/usr/bin/env python3
###############################################################################
#
# baseScraper - Base class for Scraper classes.
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2022 fra87
#

from abc import ABC, abstractmethod
import requests

from .dataTypes import (
        dataService,
        resultState,
        responsePayload,
        resultValue,
        loginResult,
        connectedDevice
    )


class baseScraper(ABC):
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
        self.resetSession()
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

    def resetSession(self):
        '''Resets the current session object
        '''
        self._session = requests.Session()

    def _requestData(self, service: dataService, params: dict[str, str] = None,
                     autologin: bool = True, forceJSON: bool = False,
                     postRequest: bool = False) -> resultValue:
        '''Request data from the router

        params will be passed in the "params" property for GET requests and in
        the "data" property for POST requests

        Args:
            service (dataService): The service to request
            params (dict[str,str], optional): Additional parameters to pass to
                                              the request. Defaults to None.
            autologin (bool, optional): If necessary, when user is not logged
                                        in try to perform a login and then
                                        retry the request. Defaults to True.
            forceJSON (bool, optional): If True, result will be an error if
                                        payload is not a valid JSON string.
                                        Defaults to False.
            postRequest (bool, optional): If True, a POST request will be sent.
                                          If False, a GET request will be sent.
                                          Defaults to False.

        Raises:
            ValueError: If service is not a valid service

        Returns:
            resultValue: The result of the request
        '''
        if not self._requestData_validService(service):
            raise ValueError(f'Invalid service requested: service {service}')

        # Build the URL
        reqUrl = self._requestData_url(service, params)

        # Build the params
        reqParams = self._requestData_params(service, params)

        try:
            # Perform a request
            if postRequest:
                requestResult = self._session.post(reqUrl, data=reqParams)
            else:
                requestResult = self._session.get(reqUrl, params=reqParams)

            # Check if request was successful
            requestResult.raise_for_status()

        except (requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError) as e:
            return resultValue(resultState.ConnectionError, error=str(e))

        # Extract payload and start building the result object
        payload = responsePayload.buildFromPayload(requestResult.content,
                                                   requestResult.encoding)

        # Check if JSON was respected
        if forceJSON and payload.as_json() is None:
            return resultValue(resultState.NotJsonResponse, payload=payload,
                               error="Not a JSON response")

        # Verify if this was a login request by the router
        if self.isLoginRequest(payload):
            self._lastLoginResult = loginResult.NotLoggedIn
            if autologin and self.login() == loginResult.Success:
                # If the login was successful, retry the request
                return self._requestData(service, params,
                                         autologin=False,
                                         forceJSON=forceJSON)
            else:
                return resultValue(resultState.MustLogin, payload=payload)

        return resultValue(resultState.Completed, payload=payload)

    @abstractmethod
    def _requestData_validService(self, service: dataService) -> bool:
        '''Check if the service is a valid service for the router

        Args:
            service (dataService): The service to verify

        Returns:
            bool: True if the service is valid
        '''
        pass

    @abstractmethod
    def _requestData_url(self, service: dataService, params: dict[str, str]
                         ) -> str:
        '''Build the URL from the requestData parameters

        If the URL cannot be built, None is returned

        Args:
            service (dataService): The service being requested
            params (dict[str, str]): The additional params being requested

        Returns:
            str: The URL for the request
        '''
        pass

    @abstractmethod
    def _requestData_params(self, service: dataService, params: dict[str, str]
                            ) -> dict[str, str]:
        '''Build the params from the requestData parameters

        Args:
            service (dataService): The service being requested
            params (dict[str, str]): The additional params being requested

        Returns:
            dict[str, str]: The params
        '''
        pass

    @staticmethod
    def isLoginRequest(payload: responsePayload) -> bool:
        '''Check if the extracted data corresponds to a login request

        Args:
            result (responsePayload): The payload object to be checked

        Returns:
            bool: True if the data corresponds to a login request
        '''
        return False

    def login(self, cleanStart: bool = False) -> loginResult:
        '''Perform a login action

        Note: this is just a wrapper function used to track the last login
        status. Subclasses need to implement the _internal_login function
        that actually performs the login

        Args:
            cleanStart (bool, optional): Remove cookies and start from scratch.
                                         Defaults to False.

        Returns:
            loginResult: The login outcome
        '''
        result = self._internal_login(cleanStart)
        self._lastLoginResult = result
        return result

    @abstractmethod
    def _internal_login(self, cleanStart: bool = False) -> loginResult:
        '''Perform a login action

        Note: this function must not be used directly, but only through the
        wrapping login(cleanStart) function.

        Args:
            cleanStart (bool, optional): Remove cookies and start from scratch.
                                         Defaults to False.

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
