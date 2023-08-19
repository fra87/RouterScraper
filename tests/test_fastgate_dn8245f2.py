#!/usr/bin/env python3
###############################################################################
#
# fastgate_dn8245f2 - Unit testing file for Fastgate Huawei DN8245f2
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2022 fra87
#

import unittest
from unittest import mock
import base64
import json
import requests

from helpers_common import MockResponse, RecordedRequest
from helpers_fastgate_dn8245f2 import SessionMock_Auth
from routerscraper.fastgate_dn8245f2 import fastgate_dn8245f2
from routerscraper.dataTypes import (
        dataService,
        resultState,
        # responsePayload,
        resultValue,
        loginResult,
        connectedDevice
    )


class TestFastgate_dn8245f2(unittest.TestCase):
    '''Test the scraper implementation for Fastgate Huawei DN8245f2
    '''

    def setUp(self):
        '''Setup for each test

        Tests will have a component already configured, together with the host
        and login credentials already stored
        '''
        self._host = 'correctHost'
        self._user = 'correctUser'
        self._pass = 'correctPass'
        self._hashedpass = base64.b64encode(self._pass.encode('ascii'))
        self._component = fastgate_dn8245f2(self._host, self._user, self._pass)

    @staticmethod
    def connectedDevice_to_dict(connDev: connectedDevice, idx: int,
                                skipName: bool = False, skipMAC: bool = False,
                                skipIP: bool = False, skipFamily: bool = False,
                                skipNetwork: bool = False) -> dict:
        '''Convert a connectedDevice to the corresponding JSON dictionary

        Args:
            connDev (connectedDevice): The item to convert
            idx (int): The index of the item in the dictionary
            skipName (bool): Avoid adding the Name parameter
            skipMAC (bool): Avoid adding the MAC parameter
            skipIP (bool): Avoid adding the IP parameter
            skipFamily (bool): Avoid adding the isFamily parameter
            skipNetwork (bool): Avoid adding the Network parameter

        Returns:
            dict: The JSON dictionary associated to the device
        '''
        result = {}

        if not skipName:
            result[f'dev_{idx}_name'] = connDev.Name
        if not skipMAC:
            result[f'dev_{idx}_mac'] = connDev.MAC
        if not skipIP:
            result[f'dev_{idx}_ip'] = connDev.IP
        if not skipFamily:
            isFamily = connDev.additionalInfo.get('isFamily', False)
            result[f'dev_{idx}_family'] = '1' if isFamily else '0'
        if not skipNetwork:
            Network = connDev.additionalInfo.get('Network', '')
            result[f'dev_{idx}_network'] = Network

        return result

    def prepareMockSession(self, mock_Session, **kwargs):
        '''Prepare a mock session

        kwargs can contain the following parameters:
        - host: the hostname (defaults to self._host)
        - user: the username (defaults to self._user)
        - password: the password (defaults to self._pass)
        - mockSuccessResponse: response to be returned as success response
                               (overriden by explicit successResponse)
        - successResponse: function to call at success (defaults to None)
        - mock1Response: response to be returned as step1 response (overrides
                         default step1Response, overriden by explicit
                         step1Response)
        - step1Response: function to calculate the step1 response (defaults to
                         the normal server behavior)
        - mock2Response: response to be returned as step2 response (overrides
                         default step2Response, overriden by explicit
                         step2Response)
        - step2Response: function to calculate the step2 response (defaults to
                         the normal server behavior)
        '''
        mock_Session.return_value = SessionMock_Auth()
        # reset so Session object can be rebuilt with mock class
        self._component.resetSession()

        successResponse = None
        step1Response = None
        step2Response = None

        if 'mockSuccessResponse' in kwargs:
            def mockSuccessResponseFun(url: str, params: dict):
                return kwargs.get('mockSuccessResponse')
            successResponse = mockSuccessResponseFun
        if 'mock1Response' in kwargs:
            def mock1ResponseFun(url: str, params: dict, **_):
                return kwargs.get('mock1Response')
            step1Response = mock1ResponseFun
        if 'mock2Response' in kwargs:
            def mock2ResponseFun(url: str, params: dict, **_):
                return kwargs.get('mock2Response')
            step2Response = mock2ResponseFun

        host = kwargs.get('host', self._host)
        user = kwargs.get('user', self._user)
        password = kwargs.get('password', self._pass)
        successResponse = kwargs.get('successResponse', successResponse)
        step1Response = kwargs.get('step1Response', step1Response)
        step2Response = kwargs.get('step2Response', step2Response)

        self._component._session.initialize(host=host,
                                            user=user,
                                            password=password,
                                            successResponse=successResponse,
                                            step1Response=step1Response,
                                            step2Response=step2Response)

    def login_cmd7_expFuncCall(self) -> dict:
        '''Return the expected function arguments in a call for CMD7 service

        Returns:
            dict: The dictionary with the arguments
        '''
        type = 'get'
        url = 'http://correctHost/status.cgi'
        reqParameters = {'cmd': '7', 'nvget': 'login_confirm'}

        return RecordedRequest(type=type, url=url, reqParameters=reqParameters,
                               other_args=[], other_kwargs={})

    def login_cmd3_expFuncCall(self, token) -> dict:
        '''Return the expected function arguments in a call for CMD3 service

        Args:
            token: The token to embed in the dictionary

        Returns:
            dict: The dictionary with the arguments
        '''
        type = 'get'
        url = 'http://correctHost/status.cgi'
        reqParameters = {'cmd': '3', 'nvget': 'login_confirm',
                         'username': self._user, 'password': self._hashedpass,
                         'token': token}

        return RecordedRequest(type=type, url=url, reqParameters=reqParameters,
                               other_args=[], other_kwargs={})

    ####################################
    # Check _requestData login         #
    ####################################

    @mock.patch('routerscraper.requestscraper.requests.Session')
    def test_requestData_need_login(self, mock_Session):
        '''Test a reply where the server needs login for the service
        '''
        self.prepareMockSession(mock_Session)

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
                                mock1Response=MockResponse(status_code=400))

        got = self._component._requestData(dataService.ConnectedDevices,
                                           autologin=True).state
        exp = resultState.MustLogin

        self.assertEqual(got, exp)

    ####################################
    # Check login                      #
    ####################################

    @mock.patch('routerscraper.requestscraper.requests.Session')
    def test_login_ConnectionError_step1(self, mock_Session):
        '''Test login fails for ConnectionError at step 1
        '''
        self.prepareMockSession(mock_Session,
                                mock1Response=MockResponse(status_code=400))

        got = self._component.login()
        exp = loginResult.ConnectionError

        self.assertEqual(got, exp)

        gotFuncCalls = self._component._session.storedRequests
        expFuncCalls = [self.login_cmd7_expFuncCall()]

        self.assertEqual(gotFuncCalls, expFuncCalls)

    @mock.patch('routerscraper.requestscraper.requests.Session')
    def test_login_noJson_step1(self, mock_Session):
        '''Test login fails for missing JSON at step 1
        '''
        contentStr = 'test_login_noJson_step1 wrong data'
        resp = MockResponse(status_code=200)
        resp.content = contentStr.encode(resp.encoding)

        self.prepareMockSession(mock_Session, mock1Response=resp)

        got = self._component.login()
        exp = loginResult.ConnectionError

        self.assertEqual(got, exp)

        gotFuncCalls = self._component._session.storedRequests
        expFuncCalls = [self.login_cmd7_expFuncCall()]

        self.assertEqual(gotFuncCalls, expFuncCalls)

    @mock.patch('routerscraper.requestscraper.requests.Session')
    def test_login_locked(self, mock_Session):
        '''Test login fails because login was locked
        '''
        resp = SessionMock_Auth._generate_step1_response('', {},
                                                         login_locked=True)

        self.prepareMockSession(mock_Session, mock1Response=resp)

        got = self._component.login()
        exp = loginResult.Locked

        self.assertEqual(got, exp)

        gotFuncCalls = self._component._session.storedRequests
        expFuncCalls = [self.login_cmd7_expFuncCall()]

        self.assertEqual(gotFuncCalls, expFuncCalls)

    @mock.patch('routerscraper.requestscraper.requests.Session')
    def test_login_no_token(self, mock_Session):
        '''Test login fails because no token was provided
        '''
        resp = SessionMock_Auth._generate_step1_response('', {}, no_token=True)

        self.prepareMockSession(mock_Session, mock1Response=resp)

        got = self._component.login()
        exp = loginResult.NoToken

        self.assertEqual(got, exp)

        gotFuncCalls = self._component._session.storedRequests
        expFuncCalls = [self.login_cmd7_expFuncCall()]

        self.assertEqual(gotFuncCalls, expFuncCalls)

    @mock.patch('routerscraper.requestscraper.requests.Session')
    def test_login_ConnectionError_step2(self, mock_Session):
        '''Test login fails for ConnectionError at step 2
        '''
        self.prepareMockSession(mock_Session,
                                mock2Response=MockResponse(status_code=400))

        got = self._component.login()
        exp = loginResult.ConnectionError

        self.assertEqual(got, exp)

        gotFuncCalls = self._component._session.storedRequests

        # extracting token
        if len(gotFuncCalls) >= 2:
            token = gotFuncCalls[1].reqParameters.get('token')
        else:
            token = None

        expFuncCalls = [
                self.login_cmd7_expFuncCall(),
                self.login_cmd3_expFuncCall(token)
            ]

        self.assertEqual(gotFuncCalls, expFuncCalls)

    @mock.patch('routerscraper.requestscraper.requests.Session')
    def test_login_noJson_step2(self, mock_Session):
        '''Test login fails for missing JSON at step 2
        '''
        contentStr = 'test_login_noJson_step2 wrong data'
        resp = MockResponse(status_code=200)
        resp.content = contentStr.encode(resp.encoding)

        self.prepareMockSession(mock_Session, mock2Response=resp)

        got = self._component.login()
        exp = loginResult.ConnectionError

        self.assertEqual(got, exp)

        gotFuncCalls = self._component._session.storedRequests

        # extracting token
        if len(gotFuncCalls) >= 2:
            token = gotFuncCalls[1].reqParameters.get('token')
        else:
            token = None

        expFuncCalls = [
                self.login_cmd7_expFuncCall(),
                self.login_cmd3_expFuncCall(token)
            ]

        self.assertEqual(gotFuncCalls, expFuncCalls)

    @mock.patch('routerscraper.requestscraper.requests.Session')
    def test_login_wrong_user(self, mock_Session):
        '''Test login fails for wrong user
        '''
        self.prepareMockSession(mock_Session, user='wrongUser')

        got = self._component.login()
        exp = loginResult.WrongUser

        self.assertEqual(got, exp)

        gotFuncCalls = self._component._session.storedRequests

        # extracting token
        if len(gotFuncCalls) >= 2:
            token = gotFuncCalls[1].reqParameters.get('token')
        else:
            token = None

        expFuncCalls = [
                self.login_cmd7_expFuncCall(),
                self.login_cmd3_expFuncCall(token)
            ]

        self.assertEqual(gotFuncCalls, expFuncCalls)

    @mock.patch('routerscraper.requestscraper.requests.Session')
    def test_login_wrong_password(self, mock_Session):
        '''Test login fails for wrong password
        '''
        self.prepareMockSession(mock_Session, password='wrongPass')

        got = self._component.login()
        exp = loginResult.WrongPass

        self.assertEqual(got, exp)

        gotFuncCalls = self._component._session.storedRequests

        # extracting token
        if len(gotFuncCalls) >= 2:
            token = gotFuncCalls[1].reqParameters.get('token')
        else:
            token = None

        expFuncCalls = [
                self.login_cmd7_expFuncCall(),
                self.login_cmd3_expFuncCall(token)
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

        gotFuncCalls = self._component._session.storedRequests

        # extracting token
        if len(gotFuncCalls) >= 2:
            token = gotFuncCalls[1].reqParameters.get('token')
        else:
            token = None

        expFuncCalls = [
                self.login_cmd7_expFuncCall(),
                self.login_cmd3_expFuncCall(token)
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
        mock_get.assert_called_once_with(f'http://{self._host}/status.cgi',
                                         params={
                                            'nvget': 'connected_device_list',
                                         })

    @mock.patch.object(requests.Session, 'get')
    def test_listDevices_noJson(self, mock_get):
        '''Test listDevices fails for missing JSON
        '''
        content = b'test_listDevices_noJson wrong data'
        mock_get.return_value = MockResponse(status_code=200, content=content)

        got = self._component.listDevices()
        exp = None

        self.assertEqual(got, exp)
        mock_get.assert_called_once_with(f'http://{self._host}/status.cgi',
                                         params={
                                            'nvget': 'connected_device_list',
                                         })

    @mock.patch.object(requests.Session, 'get')
    def test_listDevices_emptyJson(self, mock_get):
        '''Test listDevices has no output for an empty JSON
        '''
        json_data = {}
        content = json.dumps(json_data).encode()
        mock_get.return_value = MockResponse(status_code=200, content=content)

        got = self._component.listDevices()
        exp = []

        self.assertEqual(got, exp)
        mock_get.assert_called_once_with(f'http://{self._host}/status.cgi',
                                         params={
                                            'nvget': 'connected_device_list',
                                         })

    @mock.patch.object(requests.Session, 'get')
    def test_listDevices_emptyItem(self, mock_get):
        '''Test listDevices has no output for an empty connected_device_list
        '''
        json_data = {'connected_device_list': {}}
        content = json.dumps(json_data).encode()
        mock_get.return_value = MockResponse(status_code=200, content=content)

        got = self._component.listDevices()
        exp = []

        self.assertEqual(got, exp)
        mock_get.assert_called_once_with(f'http://{self._host}/status.cgi',
                                         params={
                                            'nvget': 'connected_device_list',
                                         })

    @mock.patch.object(requests.Session, 'get')
    def test_listDevices_missingTotal(self, mock_get):
        '''Test listDevices has no output when there is no total
        '''
        connDevs = [
                connectedDevice('A', 'B', 'C',
                                {'isFamily': False, 'Network': 'E'}),
            ]
        connect_list = {}
        for i, c in enumerate(connDevs):
            connect_list.update(self.connectedDevice_to_dict(c, i))
        json_data = {'connected_device_list': connect_list}
        content = json.dumps(json_data).encode()
        mock_get.return_value = MockResponse(status_code=200, content=content)

        got = self._component.listDevices()
        exp = []

        self.assertEqual(got, exp)
        mock_get.assert_called_once_with(f'http://{self._host}/status.cgi',
                                         params={
                                            'nvget': 'connected_device_list',
                                         })

    @mock.patch.object(requests.Session, 'get')
    def test_listDevices_success(self, mock_get):
        '''Test listDevices succeeds
        '''
        connDevs = [
                connectedDevice('A', 'B', 'C',
                                {'isFamily': False, 'Network': 'E'}),
                connectedDevice('J', 'I', 'H',
                                {'isFamily': True, 'Network': 'F'}),
                connectedDevice('K', 'L', 'M',
                                {'isFamily': False, 'Network': 'O'})
            ]
        connect_list = {'total_num': str(len(connDevs))}
        for i, c in enumerate(connDevs):
            connect_list.update(self.connectedDevice_to_dict(c, i))
        json_data = {'connected_device_list': connect_list}
        content = json.dumps(json_data).encode()
        mock_get.return_value = MockResponse(status_code=200, content=content)

        got = self._component.listDevices()
        exp = connDevs

        self.assertEqual(got, exp)
        mock_get.assert_called_once_with(f'http://{self._host}/status.cgi',
                                         params={
                                            'nvget': 'connected_device_list',
                                         })

    @mock.patch.object(requests.Session, 'get')
    def test_listDevices_success_more(self, mock_get):
        '''Test listDevices succeeds and ignores too many devices
        '''
        connDevs = [
                connectedDevice('A', 'B', 'C',
                                {'isFamily': False, 'Network': 'E'}),
                connectedDevice('J', 'I', 'H',
                                {'isFamily': True, 'Network': 'F'}),
                connectedDevice('K', 'L', 'M',
                                {'isFamily': False, 'Network': 'O'})
            ]
        connect_list = {'total_num': 2}
        for i, c in enumerate(connDevs):
            connect_list.update(self.connectedDevice_to_dict(c, i))
        json_data = {'connected_device_list': connect_list}
        content = json.dumps(json_data).encode()
        mock_get.return_value = MockResponse(status_code=200, content=content)

        got = self._component.listDevices()
        exp = connDevs[:2]

        self.assertEqual(got, exp)
        mock_get.assert_called_once_with(f'http://{self._host}/status.cgi',
                                         params={
                                            'nvget': 'connected_device_list',
                                         })

    @mock.patch.object(requests.Session, 'get')
    def test_listDevices_success_fewer(self, mock_get):
        '''Test listDevices succeeds and ignores too few devices
        '''
        connDevs = [
                connectedDevice('A', 'B', 'C',
                                {'isFamily': False, 'Network': 'E'}),
                connectedDevice('J', 'I', 'H',
                                {'isFamily': True, 'Network': 'F'})
            ]
        connect_list = {'total_num': 3}
        for i, c in enumerate(connDevs):
            connect_list.update(self.connectedDevice_to_dict(c, i))
        json_data = {'connected_device_list': connect_list}
        content = json.dumps(json_data).encode()
        mock_get.return_value = MockResponse(status_code=200, content=content)

        got = self._component.listDevices()
        exp = connDevs

        self.assertEqual(got, exp)
        mock_get.assert_called_once_with(f'http://{self._host}/status.cgi',
                                         params={
                                            'nvget': 'connected_device_list',
                                         })

    @mock.patch.object(requests.Session, 'get')
    def test_listDevices_success_fewerInfo(self, mock_get):
        '''Test listDevices succeeds and ignores when some info is missing
        '''
        c = connectedDevice('A', 'B', 'C',
                            {'isFamily': False, 'Network': 'E'})
        c_lst = {'total_num': 20}
        c_lst.update(self.connectedDevice_to_dict(c, 0))
        c_lst.update(self.connectedDevice_to_dict(c, 1, skipName=True))
        c_lst.update(self.connectedDevice_to_dict(c, 2, skipMAC=True))
        c_lst.update(self.connectedDevice_to_dict(c, 3, skipIP=True))
        c_lst.update(self.connectedDevice_to_dict(c, 4, skipFamily=True))
        c_lst.update(self.connectedDevice_to_dict(c, 5, skipNetwork=True))
        c_lst.update(self.connectedDevice_to_dict(c, 6))
        json_data = {'connected_device_list': c_lst}
        content = json.dumps(json_data).encode()
        mock_get.return_value = MockResponse(status_code=200, content=content)

        got = self._component.listDevices()
        exp = [c, c]  # Expecting only the first and the last

        self.assertEqual(got, exp)
        mock_get.assert_called_once_with(f'http://{self._host}/status.cgi',
                                         params={
                                            'nvget': 'connected_device_list',
                                         })
