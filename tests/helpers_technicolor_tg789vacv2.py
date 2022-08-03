#!/usr/bin/env python3
###############################################################################
#
# technicolor_tg789vacv2 - Helper functions for testing Technicolor TG789vac v2
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2022 fra87
#

import typing
import json
from pathlib import Path
import srp
from enum import Enum, auto

from helpers_common import MockResponse, SessionMock_Auth_Base, randomHexString
from routerscraper.technicolor_tg789vacv2 import technicolor_tg789vacv2


class SessionState(Enum):
    '''Enumeration with the different session states
    '''
    Created = auto()
    Initialized = auto()
    Requested_sM = auto()
    Authorized = auto()


class SessionMock_Auth(SessionMock_Auth_Base):
    '''Class to mock the Session object to mimic the authentication steps
    '''

    def __init__(self):
        '''Initialize the variables

        Note: initialize must be called before the object can actually be used
        '''
        super().__init__()
        self._state = SessionState.Created

    def initialize(self, host: str, user: str, password: str,
                   successResponse: typing.Callable,
                   auth1Response: typing.Callable = None,
                   auth2Response: typing.Callable = None,
                   mustLoginResponse: typing.Callable = None):
        '''Initialize the object

        If step1Response or step2Response are provided, they will be called in
        case one step is required and their output will be sent as request
        response. If they are None, the reply will be the one that the router
        would normally send.

        All the callbacks have prototype:
        f(url: str, params: dict) -> MockResponse

        Args:
            user (str): The username to authenticate
            password (str): The password to authenticate
            successResponse (typing.Callable): The function to calculate the
                                               response when authenticated.
            auth1Response (typing.Callable, optional): Function to create the
                                                       1st response. Defaults
                                                       to None.
            auth2Response (typing.Callable, optional): Function to create the
                                                       2nd response. Defaults
                                                       to None.
            mustLoginResponse (typing.Callable, optional): Function to create
                                                           the login response.
                                                           Defaults to None.
        '''
        self._host = host
        self._user = user
        self._pass = password

        self._successResponse = successResponse
        self._auth1Response = (auth1Response if auth1Response
                               else self._generate_auth_response)
        self._auth2Response = (auth2Response if auth2Response
                               else self._generate_auth_response)
        self._mustLoginResponse = (mustLoginResponse if mustLoginResponse
                                   else self._generate_login_request)

        self._token = randomHexString(64)

        self._state = SessionState.Initialized

    def _internal_process(self, type, url, params, args, kwargs
                          ) -> MockResponse:
        '''Get the response to the GET request performed

        Returns:
            MockResponse: The response to the GET request
        '''
        if self._state == SessionState.Created:
            raise RuntimeError('SessionMock_Auth item was not initialized')

        hostname = f'http://{self._host}'

        # The only valid hostname is the calculated one
        if not url.startswith(hostname):
            return MockResponse(status_code=404)

        # The service is the other part of the URL
        service = url[len(hostname)+1:]

        if type == 'get':
            params['##generated_token'] = self._token

            # Request was authenticated; return success response
            if self._state == SessionState.Authorized:
                return self._successResponse(url, params)
            else:
                return self._mustLoginResponse(url, params)

        if type == 'post' and service == 'authenticate':
            if self._state == SessionState.Initialized:
                # Step 1
                user = params.get('I', None)
                A = params.get('A', None)
                CSRFtoken = params.get('CSRFtoken', None)

                # Check CSRFtoken is present and valid
                if not CSRFtoken or CSRFtoken != self._token:
                    return MockResponse(status_code=403)

                # Check I and A params are present
                if not user or not A:
                    return MockResponse(status_code=400)

                params['##generated_token'] = self._token

                if user != self._user:
                    params['##fail_I'] = True
                else:
                    cfg = technicolor_tg789vacv2.srp_configuration
                    salt, vkey = srp.create_salted_verification_key(self._user,
                                                                    self._pass,
                                                                    **cfg)
                    self._svr = srp.Verifier(user, salt, vkey,
                                             bytes.fromhex(A), **cfg)
                    s, B = self._svr.get_challenge()
                    params['##s'] = s.hex()
                    params['##B'] = B.hex()
                    self._state = SessionState.Requested_sM

                return self._auth1Response(url, params)

            if self._state == SessionState.Requested_sM:
                # Reset state (so if something goes wrong authentication shall
                # start again)
                self._state = SessionState.Initialized

                # Step 2
                M = params.get('M', None)
                CSRFtoken = params.get('CSRFtoken', None)

                # Check CSRFtoken is present and valid
                if not CSRFtoken or CSRFtoken != self._token:
                    return MockResponse(status_code=403)

                # Check M param is present
                if not M:
                    return MockResponse(status_code=400)

                if not self._svr:
                    raise RuntimeError('Verifier not present')

                HAMK = self._svr.verify_session(bytes.fromhex(M))

                params['##generated_token'] = self._token

                if not HAMK:
                    params['##fail_M'] = True
                else:
                    params['##M'] = HAMK.hex()
                    self._state = SessionState.Authorized

                return self._auth2Response(url, params)

        # Not a valid request
        return MockResponse(status_code=400)

    @classmethod
    def _fileToMockResponse(cls, filename: str, encoding: str = 'ISO-8859-1',
                            status_code: int = 200, token: str = None
                            ) -> MockResponse:
        '''Create a MockResponse from a file

        When None is passed as token, a new random 64B hex string is generated

        Args:
            filename (str): Filename of the page
            encoding (str, optional): Encoding of the file. Defaults to
                                      'ISO-8859-1'.
            status_code (int, optional): The status code to return. Defaults to
                                         200.
            token (str, optional): The token to embed. Defaults to None.

        Raises:
            ValueError: When the file does not exist

        Returns:
            MockResponse: The MockResponse
        '''
        ScriptFolder = Path(__file__).parent.absolute()
        FilesFolder = ScriptFolder / 'files_technicolor_tg789vacv2'
        pageFile = FilesFolder / filename

        if not pageFile.exists():
            raise ValueError(f'{pageFile} does not exist')

        content = b''

        # Read the content of the file
        with pageFile.open('rb') as f:
            content = f.read()

        if token is None:
            token = randomHexString(64)

        content = content.replace(b'##CSRFTOKEN##', token.encode())

        return MockResponse(status_code=status_code, content=content,
                            encoding=encoding)

    @classmethod
    def _generate_login_request(cls, url: str, params: dict) -> MockResponse:
        '''Generate a login request message

        params['##generated_token'] shall contain the generated token,
        otherwise a random one will be generated

        Args:
            url (str): The url for the request
            params (dict): The parameters for the request

        Returns:
            MockResponse: The login request
        '''
        token = (params.get('##generated_token')
                 if isinstance(params, dict) else None)

        return cls._fileToMockResponse('mustLogin_ISO-8859-1.html',
                                       encoding='ISO-8859-1',
                                       status_code=200,
                                       token=token)

    @classmethod
    def _generate_auth_response(cls, url: str, params: dict) -> MockResponse:
        '''Generate a response for an authentication

        The reply will be the one that the router would normally send to a
        step1 request

        params['##s'] shall contain the param s of the response, otherwise no
        s param will be sent

        params['##B'] shall contain the param B of the response, otherwise no
        B param will be sent

        params['##M'] shall contain the param M of the response, otherwise no
        M param will be sent

        To send an error message failure the params['##error'] can be used. The
        message passed as params['##error'] is sent in the result object.

        If params['##fail_I'] is set and Truthy, the default error message for
        I mismatch will be set if ##error and ##fail_M are not set.

        If params['##fail_M'] is set and Truthy, the default error message for
        M mismatch will be set if ##error is not set.

        Usually step1 responses have s and B, while step2 responses have M

        Args:
            url (str): The url for the request
            params (dict): The parameters for the request

        Returns:
            MockResponse: The positive response to a step1 request
        '''
        s = params.get('##s', None)
        B = params.get('##B', None)
        M = params.get('##M', None)
        error = 'failed' if params.get('##fail_I', False) else None
        error = 'M didn\'t match' if params.get('##fail_M', False) else error
        error = params.get('##error', error)

        result = MockResponse(status_code=200, encoding='utf-8')
        json_data = {}

        if s:
            json_data['s'] = s
        if B:
            json_data['B'] = B
        if M:
            json_data['M'] = M
        if error:
            json_data['error'] = error

        result.content = json.dumps(json_data).encode(result.encoding)
        return result
