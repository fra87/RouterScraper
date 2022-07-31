#!/usr/bin/env python3
###############################################################################
#
# technicolor_tg789vacv2 - Class for scraping data from Technicolor TG789vac v2
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2022 fra87
#

import base64
import srp
from typing import Any
import requests
from bs4 import BeautifulSoup
import re

from .basescraper import baseScraper
from .dataTypes import (
        resultValue,
        responsePayload,
        resultState,
        loginResult,
        connectedDevice
    )

class technicolor_tg789vacv2(baseScraper):
    '''Class for scraping data from Technicolor TG789vac v2
    '''

    # List of valid services
    _validServices = [
        '/',
        'authenticate',
        'modals/device-modal.lp',
    ]

    # Fixed value for k parameter in authentication
    k_val = '05b9e8ef059c6b32ea59fc1d322d37f04aa30bae5aa9003b8321e21ddb04e300'

    def _requestData(self, service: str, params: dict[str, str] = None,
                     autologin: bool = True, forceJSON: bool = False,
                     postRequest: bool = False) -> resultValue:
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
            postRequest (bool, optional): If True, a POST request will be sent.
                                          If False, a GET request will be sent.
                                          Defaults to False.

        Raises:
            ValueError: If service is not in the _validServices list

        Returns:
            resultValue: The result of the request
        '''
        print(f'REQ {service} - {params}')
        result = super()._requestData(service, params, autologin, forceJSON,
                                      postRequest)
        try:
            if result.payload.as_html():
                self._CSRFtoken = result.payload.as_html().find(attrs=
                                        {'name': 'CSRFtoken'})['content']
        except TypeError:
            # Ignoring TypeError: 'NoneType' object is not subscriptable
            pass
        return result

    def _requestData_url(self, service: str, params: dict[str, str]) -> str:
        '''Build the URL from the requestData parameters

        Args:
            service (str): The service being requested
            params (dict[str, str]): The additional GET params being requested

        Returns:
            str: The URL for the request
        '''
        service = service.strip('/')
        return f'http://{self._host}/{service}'

    def _requestData_params(self, service: str, params: dict[str, str]
                            ) -> dict[str, str]:
        '''Build the GET params from the requestData parameters

        Args:
            service (str): The service being requested
            params (dict[str, str]): The additional GET params being requested

        Returns:
            dict[str, str]: The GET params
        '''

        if isinstance(params, dict):
            result = params
        else:
            result = {}

        return result

    @staticmethod
    def isLoginRequest(payload: responsePayload) -> bool:
        '''Check if the extracted data corresponds to a login request

        Args:
            result (responsePayload): The payload object to be checked

        Returns:
            bool: True if the data corresponds to a login request
        '''
        result = False
        if payload.as_html():
            result = str(payload.as_html().title) == '<title>Login</title>'
        return result

    def login(self, cleanStart: bool = False) -> loginResult:
        '''Perform a login action

        Args:
            cleanStart (bool, optional): Remove cookies and start from scratch.
                                         Defaults to False.

        Returns:
            loginResult: The login outcome
        '''
        if cleanStart:
            # Clear the cookies and the CSRF token
            self.resetSession()
            self._CSRFtoken = None

        # Initiate communication to get the CSRF token
        firstRequest = self._requestData('/', autologin=False)

        if firstRequest.state == resultState.Completed:
            # Already logged in
            return loginResult.Success

        if firstRequest.state != resultState.MustLogin:
            return loginResult.ConnectionError

        # Check CSRFtoken is present
        if not self._CSRFtoken:
            return loginResult.NoToken

        # Generate initial authentication parameters (I, A)
        usr = srp.User(self._user, self._password,
                       hash_alg=srp.SHA256,
                       ng_type=srp.NG_2048,
                       k_hex=self.k_val.encode('ascii'))
        I, A = usr.start_authentication()

        # Send initial parameters
        secondParams = {'CSRFtoken': self._CSRFtoken, 'I': I, 'A': A.hex()}
        secondRequest = self._requestData('authenticate', params=secondParams,
                                          autologin=False, forceJSON=True, postRequest=True)

        if secondRequest.state != resultState.Completed:
            return loginResult.ConnectionError

        # Extract and verify parameters from server
        s = secondRequest.payload.as_json().get('s', None)
        B = secondRequest.payload.as_json().get('B', None)

        if s is None or B is None:
            if secondRequest.payload.as_json().get('error') == 'failed':
                return loginResult.WrongUser
            return loginResult.WrongData

        # Calculate response to challenge
        M = usr.process_challenge( bytes.fromhex(s), bytes.fromhex(B) )

        if M is None:
            return loginResult.WrongData

        # Send response
        thirdParams = {'CSRFtoken': self._CSRFtoken, 'M': M.hex()}
        thirdRequest = self._requestData('authenticate', params=thirdParams,
                                         autologin=False, forceJSON=True, postRequest=True)

        if thirdRequest.state != resultState.Completed:
            return loginResult.ConnectionError

        # Extract and verify parameters from server
        HAMK = thirdRequest.payload.as_json().get('M', None)
        error = thirdRequest.payload.as_json().get('error', None)

        if HAMK is None or error is not None:
            return loginResult.WrongPass

        usr.verify_session(bytes.fromhex(HAMK))

        if not usr.authenticated():
            return loginResult.WrongPass

        return loginResult.Success

    def listDevices(self) -> list[connectedDevice]:
        '''Get the list of connected devices

        Returns:
            list[connectedDevice]: The list of connected devices
        '''
        print(self._requestData('modals/device-modal.lp'))
        return []
