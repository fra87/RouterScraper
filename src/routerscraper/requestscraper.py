#!/usr/bin/env python3
###############################################################################
#
# requestScraper - Base class for Scraper classes using requests.
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2022 fra87
#

from abc import abstractmethod
import requests
import json
import base64
from typing import Union, Any

from .basescraper import baseScraper
from .dataTypes import (
        dataService,
        resultState,
        responsePayload,
        resultValue,
        loginResult,
    )


class requestScraper(baseScraper):
    '''Base class for router scraper classes that directly use requests
    '''

    def __init__(self, host: str, user: str, password: str):
        '''Initialize the object

        Args:
            host (str): The host address of the router
            user (str): The username for the connection
            password (str): The password for the connection
        '''
        super().__init__(host, user, password)
        self.resetSession()

    def resetSession(self):
        '''Resets the current session object
        '''
        self._session = requests.Session()

    def exportSessionStatus(self) -> Union[str, None]:
        '''Export the session status as a string

        The string will be a base64 representation of a JSON dictionary with
        the relevant data.

        If the data cannot be retrieved, the function returns None

        Returns:
            str or None: The base64 string with the data
        '''
        result = None

        currDict = self._getSessionDict()

        if currDict:
            dictStr = json.dumps(currDict)
            result = base64.b64encode(dictStr.encode('utf-8')).decode('ascii')

        return result

    def restoreSessionStatus(self, string: str) -> bool:
        '''Restore the session status from a string

        The string must be a base64 representation of a JSON dictionary with
        the relevant data

        Args:
            string (str): The string with the data to apply

        Returns:
            bool: `True` if the session was restored correctly
        '''
        try:
            stringBytes = string.encode('ascii')
            dictBytes = base64.b64decode(stringBytes, validate=True)
            dictStr = dictBytes.decode('utf-8')
            newDict = json.loads(dictStr)
        except (UnicodeEncodeError,
                base64.binascii.Error,
                json.decoder.JSONDecodeError):
            # In case of error in decoding, do not apply the string
            return False

        return self._setSessionDict(newDict)

    def _getSessionDict(self) -> Union[dict, None]:
        '''Create a dictionary representing the current session

        Shall be inherited by the child classes, who shall still call this one

        If the data cannot be retrieved, the function returns None

        Returns:
            dict or None: The dictionary with the session data
        '''
        result = {}

        result['lastLoginResult'] = str(self._lastLoginResult.value)

        return result

    def _setSessionDict(self, dictionary: dict) -> bool:
        '''Restore the session status from a dictionary

        Shall be inherited by the child classes, who shall still call this one

        Args:
            dictionary (dict): The dictionary with the data to apply

        Returns:
            bool: `True` if the session was restored correctly
        '''
        # Check all the specific keys are present in the dictionary
        if 'lastLoginResult' not in dictionary:
            return False

        # Extract data
        try:
            self._lastLoginResult = loginResult(dictionary['lastLoginResult'])
        except ValueError:
            # In this case, the string is not a valid loginResult
            return False

        return True

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
            if autologin:
                if (self.login(cleanStart=True) == loginResult.Success):
                    # If the login was successful, retry the request
                    return self._requestData(service, params,
                                             autologin=False,
                                             forceJSON=forceJSON)

            # If we arrived here, the autologin failed or was not enabled
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
                            ) -> Any:
        '''Build the params from the requestData parameters

        Args:
            service (dataService): The service being requested
            params (dict[str, str]): The additional params being requested

        Returns:
            Any: The params
        '''
        pass
