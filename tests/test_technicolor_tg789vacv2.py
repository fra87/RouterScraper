#!/usr/bin/env python3
###############################################################################
#
# technicolor_tg789vacv2 - Unit testing file for Technicolor TG789vac v2
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2022 fra87
#

import unittest
from unittest import mock
import requests

from helpers_common import MockResponse, RecordedRequest
from helpers_technicolor_tg789vacv2 import SessionMock_Auth
from routerscraper.technicolor_tg789vacv2 import technicolor_tg789vacv2
from routerscraper.dataTypes import (
        dataService,
        resultState,
        # responsePayload,
        resultValue,
        loginResult,
        connectedDevice
    )


class TestTechnicolor_tg789vacv2(unittest.TestCase):
    '''Test the scraper implementation for Technicolor TG789vac v2
    '''
    random_tag = '##RANDOM##'

    def setUp(self):
        '''Setup for each test

        Tests will have a component already configured, together with the host
        and login credentials already stored
        '''
        self._host = 'correctHost'
        self._user = 'correctUser'
        self._pass = 'correctPass'
        self._component = technicolor_tg789vacv2(self._host, self._user,
                                                 self._pass)

    def prepareMockSession(self, mock_Session, **kwargs):
        '''Prepare a mock session

        kwargs can contain the following parameters:
        - host: the hostname (defaults to self._host)
        - user: the username (defaults to self._user)
        - password: the password (defaults to self._pass)
        - mockSuccessResponse: response to be returned as success response
                               (overriden by explicit successResponse)
        - successResponse: function to call at success (defaults to None)
        - mockAuth1Response: response to be returned as 1st auth response
                             (overrides default authResponse, overriden by
                             explicit authResponse)
        - auth1Response: function to calculate the 1st auth response (defaults
                         to the normal server behavior)
        - mockAuth2Response: response to be returned as 2nd auth response
                             (overrides default authResponse, overriden by
                             explicit authResponse)
        - auth2Response: function to calculate the 2nd auth response (defaults
                         to the normal server behavior)
        - mockLoginResponse: response to be returned as must login response
                             (overrides default authResponse, overriden by
                             explicit authResponse)
        - mustLoginResponse: function to calculate the must login response
                         (defaults to the normal server behavior)
        '''
        mock_Session.return_value = SessionMock_Auth()
        # reset so Session object can be rebuilt with mock class
        self._component.resetSession()

        successResponse = None
        auth1Response = None
        auth2Response = None
        loginResponse = None

        if 'mockSuccessResponse' in kwargs:
            def mockSuccessResponseFun(url: str, params: dict, **_):
                return kwargs.get('mockSuccessResponse')
            successResponse = mockSuccessResponseFun
        if 'mockAuth1Response' in kwargs:
            def mockAuth1ResponseFun(url: str, params: dict, **_):
                return kwargs.get('mockAuth1Response')
            auth1Response = mockAuth1ResponseFun
        if 'mockAuth2Response' in kwargs:
            def mockAuth2ResponseFun(url: str, params: dict, **_):
                return kwargs.get('mockAuth2Response')
            auth2Response = mockAuth2ResponseFun
        if 'mockLoginResponse' in kwargs:
            def mockLoginResponseFun(url: str, params: dict, **_):
                return kwargs.get('mockLoginResponse')
            loginResponse = mockLoginResponseFun

        host = kwargs.get('host', self._host)
        user = kwargs.get('user', self._user)
        password = kwargs.get('password', self._pass)
        successResponse = kwargs.get('successResponse', successResponse)
        auth1Response = kwargs.get('auth1Response', auth1Response)
        auth2Response = kwargs.get('auth2Response', auth2Response)
        loginResponse = kwargs.get('mustLoginResponse', loginResponse)

        self._component._session.initialize(host=host,
                                            user=user,
                                            password=password,
                                            successResponse=successResponse,
                                            auth1Response=auth1Response,
                                            auth2Response=auth2Response,
                                            mustLoginResponse=loginResponse)

    @classmethod
    def handle_random_gotFuncCall(cls, gotFuncCall: dict) -> dict:
        '''Removes the random tags in gotFuncCall

        Random tags will be changed to random_tag

        Args:
            gotFuncCall (dict): The function call parameters to fix

        Returns:
            dict: The dictionary with the arguments
        '''
        result = gotFuncCall
        reqParameters = result.reqParameters

        if reqParameters:
            if 'CSRFtoken' in reqParameters:
                reqParameters['CSRFtoken'] = cls.random_tag
            if 'A' in reqParameters:
                reqParameters['A'] = cls.random_tag
            if 'M' in reqParameters:
                reqParameters['M'] = cls.random_tag
            result.reqParameters = reqParameters

        return result

    @classmethod
    def login_step0_expFuncCall(cls) -> dict:
        '''Return the expected function arguments in a call for initial step of
        login service (home request)

        Returns:
            dict: The dictionary with the arguments
        '''
        type = 'get'
        url = 'http://correctHost/'
        reqParameters = {}

        return RecordedRequest(type=type, url=url, reqParameters=reqParameters,
                               other_args=[], other_kwargs={})

    @classmethod
    def login_step1_expFuncCall(cls, user: str = 'correctUser') -> dict:
        '''Return the expected function arguments in a call for 1st step of
        login service

        The random_tag is used for random hex strings

        Args:
            user (str, optional): The username to embed in the request.
                                  Defaults to 'correctUser'.

        Returns:
            dict: The dictionary with the arguments
        '''
        type = 'post'
        url = 'http://correctHost/authenticate'
        reqParameters = {'CSRFtoken': cls.random_tag, 'I': user,
                         'A': cls.random_tag}

        return RecordedRequest(type=type, url=url, reqParameters=reqParameters,
                               other_args=[], other_kwargs={})

    @classmethod
    def login_step2_expFuncCall(cls) -> dict:
        '''Return the expected function arguments in a call for 2nd step of
        login service

        The random_tag is used for random hex strings

        Returns:
            dict: The dictionary with the arguments
        '''
        type = 'post'
        url = 'http://correctHost/authenticate'
        reqParameters = {'CSRFtoken': cls.random_tag, 'M': cls.random_tag}

        return RecordedRequest(type=type, url=url, reqParameters=reqParameters,
                               other_args=[], other_kwargs={})

    ####################################
    # Check _requestData login         #
    ####################################

    @mock.patch('routerscraper.requestscraper.requests.Session')
    def test_requestData_need_login(self, mock_Session):
        '''Test a reply where the server needs login for the service
        '''
        self.prepareMockSession(mock_Session, mockAuth1Response=None,
                                mockAuth2Response=None)

        got = self._component._requestData(dataService.ConnectedDevices,
                                           autologin=False).state
        exp = resultState.MustLogin

        self.assertEqual(got, exp)

    @mock.patch('routerscraper.requestscraper.requests.Session')
    def test_requestData_autologin_success(self, mock_Session):
        '''Test a reply where the server needs login and library performs it
        '''
        contentStr = 'test_requestData_autologin correct result'
        resp = MockResponse(status_code=200)
        resp.content = contentStr.encode(resp.encoding)

        self.prepareMockSession(mock_Session, mockSuccessResponse=resp)

        got = self._component._requestData(dataService.ConnectedDevices,
                                           autologin=True)
        exp = resultValue(resultState.Completed, payload=contentStr)

        self.assertEqual(got, exp)

    @mock.patch('routerscraper.requestscraper.requests.Session')
    def test_requestData_autologin_fail(self, mock_Session):
        '''Test a reply where the server needs login and login failed

        Login fail reason is not important; let's test with a connection error
        at step 1
        '''
        self.prepareMockSession(mock_Session,
                                mockAuth1Response=MockResponse(status_code=400)
                                )

        got = self._component._requestData(dataService.ConnectedDevices,
                                           autologin=True).state
        exp = resultState.MustLogin

        self.assertEqual(got, exp)

    ####################################
    # Check login                      #
    ####################################

    @mock.patch('routerscraper.requestscraper.requests.Session')
    def test_login_ConnectionError_step0(self, mock_Session):
        '''Test login fails for ConnectionError at step 0 (must login)
        '''
        self.prepareMockSession(
                mock_Session,
                mockLoginResponse=MockResponse(status_code=400)
            )

        got = self._component.login()
        exp = loginResult.ConnectionError

        self.assertEqual(got, exp)

        gotFuncCalls = [self.handle_random_gotFuncCall(r)
                        for r in self._component._session.storedRequests]
        expFuncCalls = [
                self.login_step0_expFuncCall()
            ]

        self.assertEqual(gotFuncCalls, expFuncCalls)

    @mock.patch('routerscraper.requestscraper.requests.Session')
    def test_login_no_token_step0(self, mock_Session):
        '''Test login fails for no token provided at step 0 (must login)
        '''
        resp = SessionMock_Auth._generate_login_request('', {},
                                                        generated_token='')
        self.prepareMockSession(mock_Session, mockLoginResponse=resp)

        got = self._component.login()
        exp = loginResult.NoToken

        self.assertEqual(got, exp)

        gotFuncCalls = [self.handle_random_gotFuncCall(r)
                        for r in self._component._session.storedRequests]
        expFuncCalls = [
                self.login_step0_expFuncCall()
            ]

        self.assertEqual(gotFuncCalls, expFuncCalls)

    @mock.patch('routerscraper.requestscraper.requests.Session')
    def test_login_ConnectionError_step1(self, mock_Session):
        '''Test login fails for ConnectionError at step 1 (I, A)
        '''
        self.prepareMockSession(mock_Session,
                                mockAuth1Response=MockResponse(status_code=400)
                                )

        got = self._component.login()
        exp = loginResult.ConnectionError

        self.assertEqual(got, exp)

        gotFuncCalls = [self.handle_random_gotFuncCall(r)
                        for r in self._component._session.storedRequests]
        expFuncCalls = [
                self.login_step0_expFuncCall(),
                self.login_step1_expFuncCall(self._user)
            ]

        self.assertEqual(gotFuncCalls, expFuncCalls)

    @mock.patch('routerscraper.requestscraper.requests.Session')
    def test_login_wrongUser_step1(self, mock_Session):
        '''Test login fails for wrong user at step 1 (I, A)
        '''
        self.prepareMockSession(mock_Session, user='wrongUser')

        got = self._component.login()
        exp = loginResult.WrongUser

        self.assertEqual(got, exp)

        gotFuncCalls = [self.handle_random_gotFuncCall(r)
                        for r in self._component._session.storedRequests]
        expFuncCalls = [
                self.login_step0_expFuncCall(),
                self.login_step1_expFuncCall(self._user)
            ]

        self.assertEqual(gotFuncCalls, expFuncCalls)

    @mock.patch('routerscraper.requestscraper.requests.Session')
    def test_login_no_s_step1(self, mock_Session):
        '''Test login fails for not receiving s at step 1 (I, A)
        '''
        resp = SessionMock_Auth._generate_auth_response('', {}, B='deadbeef')
        self.prepareMockSession(mock_Session, mockAuth1Response=resp)

        got = self._component.login()
        exp = loginResult.WrongData

        self.assertEqual(got, exp)

        gotFuncCalls = [self.handle_random_gotFuncCall(r)
                        for r in self._component._session.storedRequests]
        expFuncCalls = [
                self.login_step0_expFuncCall(),
                self.login_step1_expFuncCall(self._user)
            ]

        self.assertEqual(gotFuncCalls, expFuncCalls)

    @mock.patch('routerscraper.requestscraper.requests.Session')
    def test_login_no_B_step1(self, mock_Session):
        '''Test login fails for not receiving B at step 1 (I, A)
        '''
        resp = SessionMock_Auth._generate_auth_response('', {}, s='c0ffee')
        self.prepareMockSession(mock_Session, mockAuth1Response=resp)

        got = self._component.login()
        exp = loginResult.WrongData

        self.assertEqual(got, exp)

        gotFuncCalls = [self.handle_random_gotFuncCall(r)
                        for r in self._component._session.storedRequests]
        expFuncCalls = [
                self.login_step0_expFuncCall(),
                self.login_step1_expFuncCall(self._user)
            ]

        self.assertEqual(gotFuncCalls, expFuncCalls)

    @mock.patch('routerscraper.requestscraper.requests.Session')
    def test_login_no_M_step1(self, mock_Session):
        '''Test login fails for not being able to generate M at step 1 (I, A)
        '''
        resp = SessionMock_Auth._generate_auth_response('', {}, s='c0ffee',
                                                        B='00')
        self.prepareMockSession(mock_Session, mockAuth1Response=resp)

        got = self._component.login()
        exp = loginResult.WrongData

        self.assertEqual(got, exp)

        gotFuncCalls = [self.handle_random_gotFuncCall(r)
                        for r in self._component._session.storedRequests]
        expFuncCalls = [
                self.login_step0_expFuncCall(),
                self.login_step1_expFuncCall(self._user)
            ]

        self.assertEqual(gotFuncCalls, expFuncCalls)

    @mock.patch('routerscraper.requestscraper.requests.Session')
    def test_login_ConnectionError_step2(self, mock_Session):
        '''Test login fails for ConnectionError at step 2 (M)
        '''
        self.prepareMockSession(mock_Session,
                                mockAuth2Response=MockResponse(status_code=400)
                                )

        got = self._component.login()
        exp = loginResult.ConnectionError

        self.assertEqual(got, exp)

        gotFuncCalls = [self.handle_random_gotFuncCall(r)
                        for r in self._component._session.storedRequests]

        expFuncCalls = [
                self.login_step0_expFuncCall(),
                self.login_step1_expFuncCall(self._user),
                self.login_step2_expFuncCall()
            ]

        self.assertEqual(gotFuncCalls, expFuncCalls)

    @mock.patch('routerscraper.requestscraper.requests.Session')
    def test_login_no_M_step2(self, mock_Session):
        '''Test login fails for not receiving M at step 2 (M)
        '''
        self.prepareMockSession(
                mock_Session,
                mockAuth2Response=SessionMock_Auth._generate_auth_response('',
                                                                           {})
            )

        got = self._component.login()
        exp = loginResult.WrongData

        self.assertEqual(got, exp)

        gotFuncCalls = [self.handle_random_gotFuncCall(r)
                        for r in self._component._session.storedRequests]
        expFuncCalls = [
                self.login_step0_expFuncCall(),
                self.login_step1_expFuncCall(self._user),
                self.login_step2_expFuncCall()
            ]

        self.assertEqual(gotFuncCalls, expFuncCalls)

    @mock.patch('routerscraper.requestscraper.requests.Session')
    def test_login_error_step2(self, mock_Session):
        '''Test login fails for receiving an error at step 2 (M)
        '''
        resp = SessionMock_Auth._generate_auth_response('', {}, error='Err')
        self.prepareMockSession(mock_Session, mockAuth2Response=resp)

        got = self._component.login()
        exp = loginResult.WrongData

        self.assertEqual(got, exp)

        gotFuncCalls = [self.handle_random_gotFuncCall(r)
                        for r in self._component._session.storedRequests]
        expFuncCalls = [
                self.login_step0_expFuncCall(),
                self.login_step1_expFuncCall(self._user),
                self.login_step2_expFuncCall()
            ]

        self.assertEqual(gotFuncCalls, expFuncCalls)

    @mock.patch('routerscraper.requestscraper.requests.Session')
    def test_login_wrong_password(self, mock_Session):
        '''Test login fails for using a wrong password
        '''
        self.prepareMockSession(mock_Session, password='wrongPass')

        got = self._component.login()
        exp = loginResult.WrongPass

        self.assertEqual(got, exp)

        gotFuncCalls = [self.handle_random_gotFuncCall(r)
                        for r in self._component._session.storedRequests]
        expFuncCalls = [
                self.login_step0_expFuncCall(),
                self.login_step1_expFuncCall(self._user),
                self.login_step2_expFuncCall()
            ]

        self.assertEqual(gotFuncCalls, expFuncCalls)

    @mock.patch('routerscraper.requestscraper.requests.Session')
    def test_login_wrong_verification(self, mock_Session):
        '''Test login fails for having a wrong verification code (HAMK)
        '''
        resp = SessionMock_Auth._generate_auth_response('', {}, M='baaaaaad')
        self.prepareMockSession(mock_Session, mockAuth2Response=resp)

        got = self._component.login()
        exp = loginResult.WrongPass

        self.assertEqual(got, exp)

        gotFuncCalls = [self.handle_random_gotFuncCall(r)
                        for r in self._component._session.storedRequests]
        expFuncCalls = [
                self.login_step0_expFuncCall(),
                self.login_step1_expFuncCall(self._user),
                self.login_step2_expFuncCall()
            ]

        self.assertEqual(gotFuncCalls, expFuncCalls)

    @mock.patch('routerscraper.requestscraper.requests.Session')
    def test_login_success(self, mock_Session):
        '''Test login was successful
        '''
        resp = MockResponse(status_code=200, content=b'Dummy')

        self.prepareMockSession(mock_Session, mockSuccessResponse=resp)

        got = self._component.login()
        exp = loginResult.Success

        self.assertEqual(got, exp)

        gotFuncCalls = [self.handle_random_gotFuncCall(r)
                        for r in self._component._session.storedRequests]
        expFuncCalls = [
                self.login_step0_expFuncCall(),
                self.login_step1_expFuncCall(self._user),
                self.login_step2_expFuncCall()
            ]

        self.assertEqual(gotFuncCalls, expFuncCalls)

    ####################################
    # Check listDevices                #
    ####################################

    @mock.patch.object(requests.Session, 'get')
    def test_listDevices_ConnectionError(self, mock_get):
        '''Test listDevices fails for ConnectionError
        '''
        mock_get.return_value = MockResponse(status_code=400)

        got = self._component.listDevices()
        exp = None

        self.assertEqual(got, exp)
        mock_get.assert_called_once_with(
                f'http://{self._host}/modals/device-modal.lp',
                params={}
            )

    @mock.patch.object(requests.Session, 'get')
    def test_listDevices_emptyItem(self, mock_get):
        '''Test listDevices has no output for an empty response
        '''
        content = b''
        mock_get.return_value = MockResponse(status_code=200, content=content)

        got = self._component.listDevices()
        exp = []

        self.assertEqual(got, exp)
        mock_get.assert_called_once_with(
                f'http://{self._host}/modals/device-modal.lp',
                params={}
            )

    @mock.patch.object(requests.Session, 'get')
    def test_listDevices_success(self, mock_get):
        '''Test listDevices succeeds
        '''
        mock_get.return_value = SessionMock_Auth._fileToMockResponse(
                                                'device-modal_ISO-8859-1.html')

        got = self._component.listDevices()
        exp = [connectedDevice(Name='Second device',
                               MAC='01:23:45:67:89:ab',
                               IP='192.168.1.2',
                               additionalInfo={
                                       'Status': 'green',
                                       'Type': 'Ethernet',
                                       'Port': '1'
                                   }
                               ),
               connectedDevice(Name='Third device',
                               MAC='fe:dc:ba:98:76:54',
                               IP='192.168.1.3',
                               additionalInfo={
                                       'Status': 'green',
                                       'Type': 'Wireless - 2.4GHz',
                                       'Port': ''
                                   }
                               )
               ]

        self.assertEqual(got, exp)
        mock_get.assert_called_once_with(
                f'http://{self._host}/modals/device-modal.lp',
                params={}
            )
