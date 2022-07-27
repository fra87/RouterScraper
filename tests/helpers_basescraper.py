#!/usr/bin/env python3
###############################################################################
#
# baseScraper - Helper functions for testing base class
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2022 fra87
#

from dataclasses import dataclass
from typing import Any
import requests

from routerscraper.basescraper import baseScraper
from routerscraper.dataTypes import (
        resultState,
        loginResult,
        connectedDevice
    )


@dataclass
class MockResponse:
    '''Class mocking a request response
    '''
    content: bytes = b''
    json_data: dict = None
    status_code: int = 404
    encoding: str = 'ISO-8859-1'
    cookies: str = None
    # cookies is not a string in the class, but they are for internal use only
    # anyway, so the type just needs to be consistent

    def json(self) -> dict:
        '''Return the JSON representation of the item

        Raises:
            requests.exceptions.JSONDecodeError: No JSON data available

        Returns:
            dict: The JSON dictionary
        '''
        if self.json_data:
            return self.json_data
        raise requests.exceptions.JSONDecodeError('', '', 0)

    def raise_for_status(self):
        '''Raise an exception if the request was not successful

        Raises:
            requests.exceptions.HTTPError: Server replied with an error
        '''
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError()


class tester_for_requestData(baseScraper):
    '''Class for testing _requestData
    '''

    # List of valid services
    _validServices = [
        'testing_library_service',
        'login'
    ]

    def _requestData_url(self, service: str, params: dict[str, str]) -> str:
        '''Build the URL from the requestData parameters

        Args:
            service (str): The service being requested
            params (dict[str, str]): The additional GET params being requested

        Returns:
            str: The URL for the request
        '''
        return f'{service}'

    def _requestData_params(self, service: str, params: dict[str, str]
                            ) -> dict[str, str]:
        '''Build the GET params from the requestData parameters

        Args:
            service (str): The service being requested
            params (dict[str, str]): The additional GET params being requested

        Returns:
            dict[str, str]: The GET params
        '''
        return params if isinstance(params, dict) else {}

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
        return payload == 'mustlogin'

    def login(self) -> loginResult:
        '''Perform a login action

        Returns:
            loginResult: The login outcome
        '''

        result = self._requestData('login', {}, autologin=False,
                                   forceJSON=False)

        # If request is not completed we were not able to login
        if result.state != resultState.Completed:
            return loginResult.ConnectionError

        self._session = result.cookies

        return loginResult.Success

    def listDevices(self) -> list[connectedDevice]:
        '''Get the list of connected devices

        Returns:
            list[connectedDevice]: The list of connected devices
        '''
        return []


class ForceAuthenticatedReply:
    '''Class to mimic the authentication steps
    '''

    def __init__(self, positiveResponse: bool):
        '''Initialize the variables

        Args:
            positiveResponse (bool): True if the response to the login request
                                     must be positive
        '''
        self._positiveResponse = positiveResponse

    def get_response(self, *args, **kwargs) -> MockResponse:
        '''Get the response to the GET request performed

        Returns:
            MockResponse: The response to the GET request
        '''
        # Arguments extraction
        url = args[0] if len(args) >= 1 else ''
        params = args[1] if len(args) >= 2 else {}

        url = kwargs.get('url', url)
        params = kwargs.get('params', params)
        cookies = kwargs.get('cookies', '')

        # Login requested
        if url == 'login':
            status_code = 200 if self._positiveResponse else 400
            return MockResponse(status_code=status_code, cookies='logged')

        # Request was authenticated; return success response
        if cookies == 'logged':
            return MockResponse(status_code=200, content=b'success')

        return MockResponse(status_code=200, content=b'mustlogin')
