#!/usr/bin/env python3
###############################################################################
#
# fastgate_dn8245f2 - Helper functions for testing Fastgate Huawei DN8245f2
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2022 fra87
#

from dataclasses import dataclass
import base64
import typing
import json
import requests
import random


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


class ForceAuthenticatedReply:
    '''Class to mimic the authentication steps
    '''

    def __init__(self, host: str, user: str, password: str,
                 successResponse: typing.Callable):
        '''Initialize the variables

        Args:
            user (str): The username to authenticate
            password (str): The password to authenticate
            successResponse (typing.Callable): The function to calculate the
                                               response when authenticated.
                                               Prototype: func(url: str,
                                               params: dict)
        '''
        self._host = host
        self._user = user
        self._hashedpass = base64.b64encode(password.encode('ascii'))
        self._successResponse = successResponse
        self._currentToken = ''
        self._allowedCookies = []
        self._executeStep = [True, True]

    def setExecuteStep(self, stepId: int, value: bool):
        '''Set if the login function execute one of the steps

        By default all steps are executed.

        Step 0 is when token is generated (cmd = 7)
        Step 1 is when cookie is generated (cmd = 3)

        Args:
            stepId (int): The step ID to configure (must be 0 or 1)
            value (bool): Whether the step shall be executed or not
        '''
        if stepId in [0, 1]:
            self._executeStep[stepId] = value

    @staticmethod
    def _randomHexString() -> str:
        ''' Generate a random HEX string

        String will be 32 chars (16B) long

        Returns:
            str: A random string
        '''
        return '%032x' % random.randrange(16**32)

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

        # The only valid URL is the following one
        if url != f'http://{self._host}/status.cgi':
            return MockResponse(status_code=404)

        # Request was authenticated; return success response
        if cookies and cookies in self._allowedCookies:
            self._currentToken = ''
            return self._successResponse(url, params)

        nvget = params.get('nvget', '')
        cmd = params.get('cmd', '')

        if self._executeStep[0] and nvget == 'login_confirm' and cmd == '7':
            # Step 1: generate a new token
            self._currentToken = self._randomHexString()
            result = MockResponse(status_code=200)
            result.json_data = {
                    'login_confirm': {
                            'login_locked': '0',
                            'token': self._currentToken,
                            'login_confirm': 'end'
                        }
                }
            jsonStr = json.dumps(result.json_data)
            result.content = jsonStr.encode(result.encoding)
        elif self._executeStep[1] and nvget == 'login_confirm' and cmd == '3':
            # Step 2: authenticate

            user = params.get('username', '')
            passw = params.get('password', '')
            token = params.get('token', '')

            userCorrect = user and user == self._user
            passCorrect = userCorrect and passw and passw == self._hashedpass

            if not token or token != self._currentToken:
                result = MockResponse(status_code=400)
            else:
                result = MockResponse(status_code=200)
                result.json_data = {
                        'login_confirm': {
                                'check_user': '1' if userCorrect else '0',
                                'check_pwd': '1' if passCorrect else '0',
                                'loginfail_times': '0',
                                'token': self._currentToken,
                                'login_confirm': 'end'
                            }
                    }
                jsonStr = json.dumps(result.json_data)
                result.content = jsonStr.encode(result.encoding)
                if userCorrect and passCorrect:
                    newCookie = self._randomHexString()
                    self._allowedCookies.append(newCookie)
                    result.cookies = newCookie

                self._currentToken = ''
        else:
            # Request a login
            result = MockResponse(status_code=200)
            result.json_data = {
                    'login_confirm': {
                            'login_status': '0',
                            'token': self._randomHexString(),
                            'login_confirm': 'end'
                        }
                }
            jsonStr = json.dumps(result.json_data)
            result.content = jsonStr.encode(result.encoding)
            self._currentToken = ''

        return result
