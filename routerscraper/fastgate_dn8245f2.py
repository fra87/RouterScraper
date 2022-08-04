#!/usr/bin/env python3
###############################################################################
#
# fastgate_dn8245f2 - Class for scraping data from Fastgate Huawei DN8245f2
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2022 fra87
#

import base64

from .basescraper import baseScraper
from .dataTypes import (
        dataService,
        resultState,
        responsePayload,
        # resultValue,
        loginResult,
        connectedDevice
    )


class fastgate_dn8245f2(baseScraper):
    '''Class for scraping data from Fastgate Huawei DN8245f2
    '''

    # List of services additionalParams
    _dataServicesParams = {
        dataService.Login: {'nvget': 'login_confirm'},
        dataService.ConnectedDevices: {'nvget': 'connected_device_list'},
    }

    def _requestData_validService(self, service: dataService) -> bool:
        '''Check if the service is a valid service for the router

        Args:
            service (dataService): The service to verify

        Returns:
            bool: True if the service is valid
        '''
        return service in self._dataServicesParams

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
        return f'http://{self._host}/status.cgi'

    def _requestData_params(self, service: dataService, params: dict[str, str]
                            ) -> dict[str, str]:
        '''Build the params from the requestData parameters

        Args:
            service (dataService): The service being requested
            params (dict[str, str]): The additional params being requested

        Returns:
            dict[str, str]: The params
        '''
        result = params if isinstance(params, dict) else {}

        if service in self._dataServicesParams:
            result.update(self._dataServicesParams[service])

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
        if payload.as_json():
            login_confirm = payload.as_json().get('login_confirm', {})
            result = login_confirm.get('login_status') == '0'
        return result

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
        if cleanStart:
            self.resetSession()

        # First step: perform a cmd = 7 request to obtain the token
        firstReqResult = self._requestData(
                dataService.Login,
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
        login_confirm = firstReqResult.payload.as_json().get('login_confirm',
                                                             {})
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
                dataService.Login,
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
        login_confirm = secondReqResult.payload.as_json().get('login_confirm',
                                                              {})
        if login_confirm.get('check_user') != '1':
            return loginResult.WrongUser
        if login_confirm.get('check_pwd') != '1':
            return loginResult.WrongPass

        return loginResult.Success

    def listDevices(self) -> list[connectedDevice]:
        '''Get the list of connected devices

        If there was a connection error the function returns None

        Returns:
            list[connectedDevice]: The list of connected devices
        '''
        # Get the list from the router
        res = self._requestData(dataService.ConnectedDevices, forceJSON=True)

        # If the request was not successful return empty list
        if res.state != resultState.Completed:
            return None

        connLst = res.payload.as_json().get('connected_device_list', {})

        result = []
        # Extract the items
        for i in range(int(connLst.get('total_num', '0'))):
            extractedItm = {
                    'name': connLst.get(f'dev_{i}_name'),
                    'mac': connLst.get(f'dev_{i}_mac'),
                    'ip': connLst.get(f'dev_{i}_ip'),
                    'family': connLst.get(f'dev_{i}_family'),
                    'network': connLst.get(f'dev_{i}_network')
                }

            if None not in extractedItm.values():
                result.append(connectedDevice(
                    Name=extractedItm['name'],
                    MAC=extractedItm['mac'],
                    IP=extractedItm['ip'],
                    additionalInfo={
                        'isFamily': extractedItm['family'] == '1',
                        'Network': extractedItm['network']
                    }))

        return result
