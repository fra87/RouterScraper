#!/usr/bin/env python3
###############################################################################
#
# fastgate_dn8245f2 - Class for scraping data from Fastgate Huawei DN8245f2
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2022 fra87
#

import requests
import base64
from enum import Enum
from dataclasses import dataclass

from .basescraper import baseScraper
from .requestResult import resultValue, resultState


class loginResult(Enum):
    '''Enum with possible login results
    '''

    Success = 'Login successful'
    ConnectionError = 'Connection error'
    Locked = 'Login is locked'
    NoToken = 'Could not extract token from request'
    WrongUser = 'Wrong username provided'
    WrongPass = 'Wrong password provided'


@dataclass
class connectedDevice:
    '''Class containing one connected device information
    '''
    Name: str
    MAC: str
    IP: str
    isFamily: bool
    Network: str


class fastgate_dn8245f2(baseScraper):
    '''Class for scraping data from Fastgate Huawei DN8245f2
    '''

    _validServices = [
        'connected_device_list',
        'login_confirm'
    ]

    def __init__(self, host: str, user: str, password: str):
        '''Initialize the object

        Args:
            host (str): The host address of the Fastgate router
            user (str): The username for the connection
            password (str): The password for the connection
        '''
        super().__init__(host, user, password)

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

        Returns:
            resultValue: The result of the request
        '''
        if service not in self._validServices:
            errorMessage = (f'Invalid service requested: service {service}, '
                            f'valid services {self._validServices}')
            raise ValueError(errorMessage)

        # Initialize params dictionary and set the nvget parameter
        if not isinstance(params, dict):
            params = {}
        params['nvget'] = service

        # Build the request URL
        requestUrl = f'http://{self._host}/status.cgi'

        # Build the cookies variable
        session = self._session if self._session else None

        try:
            # Perform a request
            result = requests.get(requestUrl, params=params, cookies=session)

            # Check if request was successful
            result.raise_for_status()

        except (requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError) as e:
            return resultValue(resultState.ConnectionError, str(e))

        # Extract cookies from result
        cookies = result.cookies if result.cookies else None

        # Extract payload
        payload = result.content.decode(result.encoding)

        try:
            # Extract JSON representation if available
            jsonItm = result.json()

            # Verify if this was a login request by the router
            # (valid only if there was a JSON payload)
            if jsonItm.get('login_confirm', {}).get('login_status') == '0':
                if autologin and self.login() == loginResult.Success:
                    # If the login was successful, retry the request
                    return self._requestData(service, params,
                                             autologin=False,
                                             forceJSON=forceJSON)
                else:
                    return resultValue(resultState.MustLogin, payload, jsonItm)
        except requests.exceptions.JSONDecodeError:
            if forceJSON:
                return resultValue(resultState.NotJsonResponse, payload)
            jsonItm = {}

        return resultValue(resultState.Completed, payload, jsonItm, cookies)

    def login(self) -> loginResult:
        '''Perform a login action

        Returns:
            loginResult: The login outcome
        '''

        # First step: perform a cmd = 7 request to obtain the token
        firstReqResult = self._requestData(
                'login_confirm',
                {
                    'cmd': '7'
                },
                autologin=False,
                forceJSON=True
            )

        # If request is not completed we were not able to login
        if firstReqResult.state != resultState.Completed:
            return loginResult.ConnectionError

        # If login was locked we were not able to login
        login_confirm = firstReqResult.payloadJSON.get('login_confirm', {})
        if login_confirm.get('login_locked') == '1':
            return loginResult.Locked

        # Extract token
        token = login_confirm.get('token')
        # If token cannot be extracted we were not able to login
        if not token:
            return loginResult.NoToken

        # Second step: perform a cmd = 3 request with user and pass
        encoded_pass = base64.b64encode(self._password.encode('ascii'))
        secondReqResult = self._requestData(
                'login_confirm',
                {
                    'cmd': '3',
                    'username': self._user,
                    'password': encoded_pass,
                    'token': token
                },
                autologin=False,
                forceJSON=True
            )

        # If request is not completed we were not able to login
        if secondReqResult.state != resultState.Completed:
            return loginResult.ConnectionError

        # Check if login was successful
        login_confirm = secondReqResult.payloadJSON.get('login_confirm', {})
        if login_confirm.get('check_user') != '1':
            return loginResult.WrongUser
        if login_confirm.get('check_pwd') != '1':
            return loginResult.WrongPass

        self._session = secondReqResult.cookies

        return loginResult.Success

    def listDevices(self) -> list[connectedDevice]:
        '''Get the list of connected devices

        Returns:
            list[connectedDevice]: The list of connected devices
        '''
        # Get the list from the router
        res = self._requestData('connected_device_list', forceJSON=True)

        # If the request was not successful return empty list
        if res.state != resultState.Completed:
            return []

        connLst = res.payloadJSON.get('connected_device_list', {})

        result = []
        # Extract the items
        for i in range(int(connLst.get('total_num', '0'))):
            result.append(connectedDevice(
                Name=connLst.get(f'dev_{i}_name'),
                MAC=connLst.get(f'dev_{i}_mac'),
                IP=connLst.get(f'dev_{i}_ip'),
                isFamily=connLst.get(f'dev_{i}_family') == '1',
                Network=connLst.get(f'dev_{i}_network')
                ))

        return result
