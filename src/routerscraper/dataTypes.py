#!/usr/bin/env python3
###############################################################################
#
# dataTypes - Module to group data types used in the functions
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2022 fra87
#

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Union
import json
from bs4 import BeautifulSoup


class dataService(Enum):
    '''Enum expressing the services that can be requested
    '''
    Home = 'main page'
    Login = 'login service'
    ConnectedDevices = 'get connected devices'
    TestValid = 'test service - to be implemented in test classes'
    TestNotValid = 'test service - not to be implemented in test classes'


class resultState(Enum):
    '''Enum expressing the state of a request
    '''
    Completed = 'Request was completed correctly; data is in payload'
    ConnectionError = 'Error performing the HTTP request'
    MustLogin = 'Request failed because user is not logged in'
    NotJsonResponse = 'Requested JSON response, but received plain text'
    GenericError = 'Generic error performing the request'


class responsePayload:
    '''Class holding the payload of a response
    '''
    def __init__(self, payload: str):
        '''Constructor

        Args:
            payload (str): The payload
        '''
        self._payload = payload
        self._payloadJSON = None
        self._payloadHTML = None

    def __repr__(self) -> str:
        '''Return the string representation of the item (i.e. the payload)

        Returns:
            str: The string representation of the item
        '''
        return self._payload

    def __eq__(self, other: Any) -> bool:
        '''Test if the two objects are equal

        If the other object is not a responsePayload object, it will be
        converted into such an object through the buildFromPayload function. If
        this function fails, the payloads are not equal

        Args:
            other (Any): The other response payload

        Returns:
            bool: True if the two objects are equal
        '''
        if not isinstance(other, responsePayload):
            try:
                other = responsePayload.buildFromPayload(other)
            except ValueError:
                # other could not be converted; payloads are different
                return False
        return self._payload == other._payload

    def as_str(self) -> str:
        '''The payload in string format

        Returns:
            str: The payload
        '''
        return self._payload

    def as_json(self) -> dict:
        '''The payload in JSON representation

        If payload is not JSON then None will be returned

        Returns:
            dict: The payload in JSON representation
        '''
        if self._payloadJSON is None:
            try:
                self._payloadJSON = json.loads(self._payload)
            except json.JSONDecodeError:
                self._payloadJSON = None
        return self._payloadJSON

    def as_html(self) -> BeautifulSoup:
        '''The payload in HTML representation

        Returns:
            BeautifulSoup: The payload in HTML representation
        '''
        if self._payloadHTML is None and self._payload:
            self._payloadHTML = BeautifulSoup(self._payload, 'html.parser')
        return self._payloadHTML

    @classmethod
    def buildFromPayload(cls, payload: Union[str, bytes, responsePayload],
                         encoding: str = 'utf-8') -> responsePayload:
        '''Converts a payload to a responsePayload object

        In case payload is already a responsePayload object it will be cloned

        Args:
            payload (Union[str, bytes, responsePayload]): The payload
            encoding (str, optional): The encoding in case payload is a bytes
                                      object. Defaults to 'utf-8'.

        Raises:
            ValueError: If payload is not a supported type

        Returns:
            responsePayload: The responsePayload object
        '''
        if isinstance(payload, str):
            return cls(payload)
        if isinstance(payload, bytes):
            return cls(payload.decode(encoding))
        if isinstance(payload, cls):
            return cls(payload.as_str())

        raise ValueError('payload is not str, bytes or responsePayload')


class resultValue:
    '''Class containing the result of a request
    '''

    def __init__(self,
                 state: resultState,
                 payload: Union[str, bytes, responsePayload] = "",
                 error: str = ""):
        '''Constructor

        Args:
            state (resultState): The state associated to the result
            payload (Union[str, bytes, responsePayload], optional): The
                                                    payload. Defaults to "".
            error (str, optional): An error string describing the fault.
                                   Defaults to "".
        '''
        self._state = state
        self._payload = responsePayload.buildFromPayload(payload)
        self._error = error

    def __repr__(self) -> str:
        '''Return the string representation of the item

        Returns:
            str: The string representation of the item
        '''
        pl = str(self._payload)
        if not pl:
            if self._error:
                pl = "ERR" + self._error
            else:
                pl = "NONE"
        return f'("{self._state}, {pl}")'

    def __eq__(self, other: resultValue) -> bool:
        '''Test if the two objects are equal

        If the other object is not a resultValue object, function will return
        False

        Args:
            other (resultValue): The other resultValue object

        Returns:
            bool: True if the two objects are equal
        '''
        if not isinstance(other, resultValue):
            return False
        return (self._state == other._state and
                self._payload == other._payload and
                self._error == other._error)

    @property
    def state(self) -> resultState:
        '''The state of the request

        Returns:
            resultState: The state of the request
        '''
        return self._state

    @property
    def payload(self) -> responsePayload:
        '''The payload

        Returns:
            responsePayload: The payload object
        '''
        return self._payload

    @property
    def error(self) -> str:
        '''An error string describing the fault

        Returns:
            str: An error string describing the fault
        '''
        return self._error


class loginResult(Enum):
    '''Enum with possible login results
    '''

    Success = 'Login successful'
    NotLoggedIn = 'Login was not attempted'
    ConnectionError = 'Connection error'
    Locked = 'Login is locked'
    NoToken = 'Could not extract token from request'
    WrongUser = 'Wrong username provided'
    WrongPass = 'Wrong password provided'
    WrongData = 'Wrong data exchanged with server'


@dataclass
class connectedDevice:
    '''Class containing one connected device information
    '''
    Name: str
    MAC: str
    IP: str
    additionalInfo: dict = field(default_factory=dict)
