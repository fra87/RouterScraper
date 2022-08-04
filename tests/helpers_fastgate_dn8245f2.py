#!/usr/bin/env python3
###############################################################################
#
# fastgate_dn8245f2 - Helper functions for testing Fastgate Huawei DN8245f2
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2022 fra87
#

import base64
import typing
import json

from helpers_common import MockResponse, SessionMock_Auth_Base, randomHexString


class SessionMock_Auth(SessionMock_Auth_Base):
    '''Class to mock the Session object to mimic the authentication steps
    '''

    def __init__(self):
        '''Initialize the variables

        Note: initialize must be called before the object can actually be used
        '''
        super().__init__()
        self._initialized = False

    def initialize(self,
                   host: str,
                   user: str,
                   password: str,
                   successResponse: typing.Callable,
                   step1Response: typing.Callable = None,
                   step2Response: typing.Callable = None):
        '''Initialize the object

        If step1Response or step2Response are provided, they will be called in
        case one step is required and their output will be sent as request
        response. If they are None, the reply will be the one that the router
        would normally send.

        All the callbacks have prototype:
        f(url: str, params: dict, **kwargs) -> MockResponse

        For kwargs documentation check _generate_login_request,
        _generate_step1_response and _generate_step2_response.

        Args:
            user (str): The username to authenticate
            password (str): The password to authenticate
            successResponse (typing.Callable): The function to calculate the
                                               response when authenticated.
            step1Response (typing.Callable, optional): Function to create the
                                                       step1 response. Defaults
                                                       to None.
            step2Response (typing.Callable, optional): Function to create the
                                                       step2 response. Defaults
                                                       to None.
        '''
        self._host = host
        self._user = user
        self._hashedpass = base64.b64encode(password.encode('ascii'))
        self._successResponse = successResponse
        self._step1Response = (step1Response if step1Response
                               else self._generate_step1_response)
        self._step2Response = (step2Response if step2Response
                               else self._generate_step2_response)
        self._currentToken = ''
        self._authenticated = False
        self._initialized = True

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
        if not self._initialized:
            raise RuntimeError('SessionMock_Auth item was not initialized')

        if type != 'get':
            return MockResponse(status_code=400)

        # The only valid URL is the following one
        if url != f'http://{self._host}/status.cgi':
            return MockResponse(status_code=404)

        # Request was authenticated; return success response
        if self._authenticated:
            self._currentToken = ''
            return self._successResponse(url, params)

        nvget = params.get('nvget', '')
        cmd = params.get('cmd', '')

        if nvget == 'login_confirm' and cmd == '7':
            self._currentToken = randomHexString(32)
            result = self._step1Response(url, params,
                                         generated_token=self._currentToken)
        elif nvget == 'login_confirm' and cmd == '3':
            # Step 2: authenticate

            user = params.get('username', '')
            passw = params.get('password', '')
            token = params.get('token', '')

            if not token or token != self._currentToken:
                result = MockResponse(status_code=400)
            else:
                user_correct = user and user == self._user
                pass_correct = (user_correct and passw and
                                passw == self._hashedpass)

                result = self._step2Response(
                            url, params, generated_token=self._currentToken,
                            user_correct=user_correct,
                            pass_correct=pass_correct)

                if user_correct and pass_correct:
                    self._authenticated = True

                self._currentToken = ''
        else:
            # Request a login
            result = self._generate_login_request(url, params)
            self._currentToken = ''

        return result

    @classmethod
    def _generate_login_request(cls, url: str, params: dict, **kwargs
                                ) -> MockResponse:
        '''Generate a login request message

        No kwargs are used

        Args:
            url (str): The url for the request
            params (dict): The parameters for the request

        Returns:
            MockResponse: The login request
        '''
        result = MockResponse(status_code=200)
        json_data = {
                'login_confirm': {
                        'login_status': '0',
                        'token': randomHexString(32),
                        'login_confirm': 'end'
                    }
            }
        result.content = json.dumps(json_data).encode(result.encoding)
        return result

    @classmethod
    def _generate_step1_response(cls, url: str, params: dict, **kwargs
                                 ) -> MockResponse:
        '''Generate a default response for step 1

        The reply will be the one that the router would normally send to a
        step1 request.

        kwargs values:
        - generated_token: shall contain the generated token, otherwise a
                           random one will be generated
        - login_locked: if it is present and Truthy then the response will have
                        a locked status
        - no_token: if it is present and Truthy then the response will not
                    contain a token

        Args:
            url (str): The url for the request
            params (dict): The parameters for the request

        Returns:
            MockResponse: The positive response to a step1 request
        '''
        token = kwargs.get('generated_token', randomHexString(32))
        login_locked = kwargs.get('login_locked', False)
        no_token = kwargs.get('no_token', False)

        result = MockResponse(status_code=200)
        json_data = {
                'login_confirm': {
                        'login_locked': '1' if login_locked else '0',
                        'login_confirm': 'end'
                    }
            }

        if not no_token:
            json_data['login_confirm']['token'] = token

        result.content = json.dumps(json_data).encode(result.encoding)
        return result

    @classmethod
    def _generate_step2_response(cls, url: str, params: dict, **kwargs
                                 ) -> MockResponse:
        '''Generate a default response for step 2

        The reply will be the one that the router would normally send to a
        step2 request

        kwargs values:
        - generated_token: shall contain the generated token, otherwise a
                           random one will be generated
        - user_correct: if it is present and Truthy then the response will show
                        that user is valid
        - pass_correct: if it is present and Truthy then the response will show
                        that password is valid

        Args:
            url (str): The url for the request
            params (dict): The parameters for the request

        Returns:
            MockResponse: The positive response to a step2 request
        '''
        token = kwargs.get('generated_token', randomHexString(32))
        userCorrect = kwargs.get('user_correct', False)
        passCorrect = kwargs.get('pass_correct', False)

        result = MockResponse(status_code=200)
        json_data = {
                'login_confirm': {
                        'check_user': '1' if userCorrect else '0',
                        'check_pwd': '1' if passCorrect else '0',
                        'loginfail_times': '0',
                        'token': token,
                        'login_confirm': 'end'
                    }
            }
        result.content = json.dumps(json_data).encode(result.encoding)
        return result
