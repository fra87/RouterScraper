#!/usr/bin/env python3
###############################################################################
#
# dataTypes - Module to group data types used in the functions
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2022 fra87
#

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class resultState(Enum):
    '''Enum expressing the state of a request
    '''
    Completed = 'Request was completed correctly; data is in payload'
    ConnectionError = 'Error performing the HTTP request'
    MustLogin = 'Request failed because user is not logged in'
    NotJsonResponse = 'Requested JSON response, but received plain text'
    GenericError = 'Generic error performing the request'


@dataclass
class resultValue:
    '''Class containing the result of a request
    '''
    state: resultState
    payload: str
    payloadJSON: dict = field(default_factory=dict)
    cookies: Any = None


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
    additionalInfo: dict = field(default_factory=dict)
