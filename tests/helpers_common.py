#!/usr/bin/env python3
###############################################################################
#
# common - Helper items for testing classes
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2022 fra87
#

from dataclasses import dataclass
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


class SessionMock_Auth_Base(ABC):
    '''Base class to mock the Session object to mimic the authentication steps
    '''

    def __init__(self):
        '''Initialize the variables
        '''
        self._storedRequests = []

    @property
    def lastRequest(self) -> dict:
        return self._storedRequests[-1]

    @property
    def storedRequests(self) -> dict:
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
            MockResponse: The response to the GET request
        '''
        return self._process('post', args, kwargs)

    def _process(self, type, args, kwargs) -> MockResponse:
        '''Function used to process a request

        This function uses _internal_process, implemented in child classes, to
        actually perform a request
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

        reqParameters = {k: v for k, v in params.items()
                         if not k.startswith('###')}

        lastRequest = {
            'type': type,
            'url': url,
            'reqParameters': reqParameters,
            'other_args': other_args,
            'other_kwargs': other_kwargs
        }
        if url_args and url_args != url:
            lastRequest['url_args'] = url_args
        if params_args and params_args != params:
            lastRequest['params_args'] = params_args

        self._storedRequests.append(lastRequest)

        return self._internal_process(type, url, params, args, kwargs)

    @abstractmethod
    def _internal_process(self, type, url, params, args, kwargs
                          ) -> MockResponse:
        '''Function used to actually process a request

        Returns:
            MockResponse: The response to the GET request
        '''
        pass
