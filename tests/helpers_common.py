#!/usr/bin/env python3
###############################################################################
#
# common - Helper items for testing classes
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2022 fra87
#

from dataclasses import dataclass, field
import requests
import random
from abc import ABC, abstractmethod


def randomHexString(numChars: int) -> str:
    '''Generate a random HEX string

    String will be numChars chars long

    Returns:
        str: A random string
    '''
    return (f'%0{numChars}x') % random.randrange(16**numChars)


@dataclass
class MockResponse:
    '''Class mocking a request response
    '''

    content: bytes = b''
    status_code: int = 404
    encoding: str = 'ISO-8859-1'

    def raise_for_status(self):
        '''Raise an exception if the request was not successful

        Raises:
            requests.exceptions.HTTPError: Server replied with an error
        '''
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError()


@dataclass
class RecordedRequest:
    '''Class to store a recorded request information
    '''

    type: str
    url: str
    reqParameters: dict
    other_args: list
    other_kwargs: dict
    url_args: str = ''
    params_args: dict = field(default_factory=dict)


class SessionMock_Auth_Base(ABC):
    '''Base class to mock the Session object to mimic the authentication steps

    The base class manages the recording of the requests.
    '''

    def __init__(self):
        '''Initialize the variables
        '''
        self._storedRequests = []

    @property
    def lastRequest(self) -> RecordedRequest:
        '''Return the last recorded request

        If no requests were performed it returns None

        Returns:
            RecordedRequest: The last request
        '''
        return self._storedRequests[-1] if self._storedRequests else None

    @property
    def storedRequests(self) -> list[RecordedRequest]:
        '''Return all recorded requests

        Returns:
            list[RecordedRequest]: The recorded requests
        '''
        return self._storedRequests

    def get(self, *args, **kwargs) -> MockResponse:
        '''Get the response to the GET request performed

        Returns:
            MockResponse: The response to the GET request
        '''
        return self._process('get', args, kwargs)

    def post(self, *args, **kwargs) -> MockResponse:
        '''Get the response to the POST request performed

        Returns:
            MockResponse: The response to the POST request
        '''
        return self._process('post', args, kwargs)

    def _process(self, type: str, args: list, kwargs: dict) -> MockResponse:
        '''Function used to process a request

        This function uses _internal_process, implemented in child classes, to
        actually perform a request.

        type can be either 'get' or 'post'; other values trigger an exception.

        Args:
            type (str): The type of the request
            args (list): List of unnamed arguments to the GET or POST call
            kwargs (dict): Dict with named arguments to the GET or POST call

        Raises:
            RuntimeError: type is not an allowed one

        Returns:
            MockResponse: The response to the GET or POST call
        '''
        if type == 'get':
            paramsKey = 'params'
        elif type == 'post':
            paramsKey = 'data'
        else:
            raise RuntimeError('SessionMock_Auth_Base._internal_process - '
                               'wrong type for request')

        # Arguments extraction
        url_args = args[0] if len(args) >= 1 else ''
        params_args = args[1] if len(args) >= 2 else {}
        other_args = args[2:] if len(args) >= 3 else []

        url = kwargs.get('url', url_args)
        params = kwargs.get(paramsKey, params_args)
        other_kwargs = {k: v for k, v in kwargs.items()
                        if k not in ['url', paramsKey]}

        reqParameters = {k: v for k, v in params.items()}

        lastRequest = RecordedRequest(type=type,
                                      url=url,
                                      reqParameters=reqParameters,
                                      other_args=other_args,
                                      other_kwargs=other_kwargs
                                      )

        if url_args and url_args != url:
            lastRequest.url_args = url_args
        if params_args and params_args != params:
            lastRequest.params_args = params_args

        self._storedRequests.append(lastRequest)

        return self._internal_process(type, url, params, args, kwargs)

    @abstractmethod
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
        pass
