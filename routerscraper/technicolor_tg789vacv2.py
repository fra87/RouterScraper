#!/usr/bin/env python3
###############################################################################
#
# technicolor_tg789vacv2 - Class for scraping data from Technicolor TG789vac v2
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2022 fra87
#

import srp

from .basescraper import baseScraper
from .dataTypes import (
        dataService,
        resultState,
        responsePayload,
        resultValue,
        loginResult,
        connectedDevice
    )


class technicolor_tg789vacv2(baseScraper):
    '''Class for scraping data from Technicolor TG789vac v2
    '''

    # List of services URLs
    _dataServicesUrl = {
        dataService.Home: '',
        dataService.Login: 'authenticate',
        dataService.ConnectedDevices: 'modals/device-modal.lp',
    }

    # Fixed value for authentication parameters
    srp_configuration = {
            'hash_alg': srp.SHA256,
            'ng_type': srp.NG_2048,
            'k_hex': (b'05b9e8ef059c6b32ea59fc1d322d37f0'
                      b'4aa30bae5aa9003b8321e21ddb04e300')
        }

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
        result = super()._requestData(service=service, params=params,
                                      autologin=autologin, forceJSON=forceJSON,
                                      postRequest=postRequest)

        try:
            html = result.payload.as_html()
            if html:
                tokenTag = html.find(attrs={'name': 'CSRFtoken'})
                self._CSRFtoken = tokenTag['content']
        except TypeError:
            # Ignoring TypeError: 'NoneType' object is not subscriptable
            pass
        return result

    def _requestData_validService(self, service: dataService) -> bool:
        '''Check if the service is a valid service for the router

        Args:
            service (dataService): The service to verify

        Returns:
            bool: True if the service is valid
        '''
        return service in self._dataServicesUrl

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
        result = None
        if service in self._dataServicesUrl:
            result = f'http://{self._host}/{self._dataServicesUrl[service]}'
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
        result = False
        if payload.as_html():
            result = str(payload.as_html().title) == '<title>Login</title>'
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
            # Clear the cookies and the CSRF token
            self.resetSession()
            self._CSRFtoken = None

        # Initiate communication to get the CSRF token
        firstRequest = self._requestData(dataService.Home, autologin=False)

        if firstRequest.state == resultState.Completed:
            # Already logged in
            return loginResult.Success

        if firstRequest.state != resultState.MustLogin:
            return loginResult.ConnectionError

        # Check CSRFtoken is present
        if not self._CSRFtoken:
            return loginResult.NoToken

        # Generate initial authentication parameters (I, A)
        usr = srp.User(self._user, self._password, **self.srp_configuration)
        I, A = usr.start_authentication()

        # Send initial parameters
        secondParams = {'CSRFtoken': self._CSRFtoken, 'I': I, 'A': A.hex()}
        secondRequest = self._requestData(dataService.Login,
                                          params=secondParams, autologin=False,
                                          forceJSON=True, postRequest=True)

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
        M = usr.process_challenge(bytes.fromhex(s), bytes.fromhex(B))

        if M is None:
            return loginResult.WrongData

        # Send response
        thirdParams = {'CSRFtoken': self._CSRFtoken, 'M': M.hex()}
        thirdRequest = self._requestData(dataService.Login, params=thirdParams,
                                         autologin=False, forceJSON=True,
                                         postRequest=True)

        if thirdRequest.state != resultState.Completed:
            return loginResult.ConnectionError

        # Extract and verify parameters from server
        HAMK = thirdRequest.payload.as_json().get('M', None)
        error = thirdRequest.payload.as_json().get('error', None)

        if error == "M didn't match":
            return loginResult.WrongPass

        if HAMK is None or error is not None:
            return loginResult.WrongData

        usr.verify_session(bytes.fromhex(HAMK))

        if not usr.authenticated():
            return loginResult.WrongPass

        return loginResult.Success

    def listDevices(self) -> list[connectedDevice]:
        '''Get the list of connected devices

        If there was a connection error the function returns None

        Returns:
            list[connectedDevice]: The list of connected devices
        '''
        res = self._requestData(dataService.ConnectedDevices)

        # If the request was not successful return empty list
        if res.state != resultState.Completed:
            return None

        if res.payload.as_html():
            devicesTable = res.payload.as_html().find('table', id='devices')
        else:
            devicesTable = None

        result = []

        if devicesTable and devicesTable.tbody:
            for row in devicesTable.tbody.findAll('tr'):
                rowTokens = row.findAll('td')

                Status = ', '.join(cl for cl in rowTokens[0].div['class']
                                   if cl != 'light')
                Hostname = rowTokens[1].text
                IP = rowTokens[2].text
                MAC = rowTokens[3].text
                Type = rowTokens[4].text
                Port = rowTokens[5].text

                if IP:
                    # Device is connected if it has an IP
                    result.append(connectedDevice(
                                Name=Hostname,
                                MAC=MAC,
                                IP=IP,
                                additionalInfo={
                                        'Status': Status,
                                        'Type': Type,
                                        'Port': Port
                                    }
                            )
                        )

        return result
