#!/usr/bin/env python3
###############################################################################
#
# requestScraper - Helper functions for testing base class
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2022 fra87
#

from helpers_common import MockResponse, SessionMock_Auth_Base

from routerscraper.requestscraper import requestScraper
from routerscraper.dataTypes import (
        dataService,
        resultState,
        responsePayload,
        # resultValue,
        loginResult,
        connectedDevice
    )


class tester_for_requestData(requestScraper):
    '''requestScraper implementation for testing _requestData
    '''

    # List of valid services
    _dataServiceUrls = {
        dataService.TestValid: 'testing_library_service',
        dataService.Login: 'login'
    }

    def _requestData_validService(self, service: dataService) -> bool:
        '''Check if the service is a valid service for the router

        Args:
            service (dataService): The service to verify

        Returns:
            bool: True if the service is valid
        '''
        return service in self._dataServiceUrls

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
        result = ''
        if service in self._dataServiceUrls:
            result = self._dataServiceUrls[service]
        return result

    def _requestData_params(self, service: dataService, params: dict[str, str]
                            ) -> dict[str, str]:
        '''Build the params from the requestData parameters

        Args:
            service (dataService): The service being requested
            params (dict[str, str]): The additional params being requested

        Returns:
            dict[str, str]: The params
        '''
        return params if isinstance(params, dict) else {}

    @staticmethod
    def isLoginRequest(payload: responsePayload) -> bool:
        '''Check if the extracted data corresponds to a login request

        Args:
            result (responsePayload): The payload object to be checked

        Returns:
            bool: True if the data corresponds to a login request
        '''
        return payload.as_str() == 'mustlogin'

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
        result = self._requestData(dataService.Login, {}, autologin=False,
                                   forceJSON=False)

        # If request is not completed we were not able to login
        if result.state != resultState.Completed:
            return loginResult.ConnectionError

        return loginResult.Success

    def listDevices(self) -> list[connectedDevice]:
        '''Get the list of connected devices

        If there was a connection error the function returns None

        Returns:
            list[connectedDevice]: The list of connected devices
        '''
        return []


class SessionMock_Auth(SessionMock_Auth_Base):
    '''Class to mock the Session object to mimic the authentication steps
    '''

    def __init__(self):
        '''Initialize the variables
        '''
        super().__init__()
        self._authenticated = False
        self.positiveResponse = True

    def _internal_process(self, type: str, url: str, params: dict, args: list,
                          kwargs: dict) -> MockResponse:
        '''Function used to actually process a request

        type can be either 'get' or 'post'; other values are filtered in the
        base process function.

        Args:
            type (str): The type of the request
            url (str): The URL of the request
            params (dict): The params dictionary for the request
            args (list): Unnamed arguments to the GET or POST call (excluding
                         URL and params)
            kwargs (dict): Named arguments to the GET or POST call (excluding
                         URL and params)

        Returns:
            MockResponse: The response to the GET or POST call
        '''
        if type != 'get':
            return MockResponse(status_code=400)

        # Login requested
        if url == 'login':
            status_code = 200 if self.positiveResponse else 400
            self._authenticated = self.positiveResponse
            return MockResponse(status_code=status_code)

        # Request was authenticated; return success response
        if self._authenticated:
            return MockResponse(status_code=200, content=b'success')

        return MockResponse(status_code=200, content=b'mustlogin')
