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
import random
import json

from routerscraper.fastgate_dn8245f2 import fastgate_dn8245f2
from helpers_fastgate_dn8245f2 import MockResponse, ForceAuthenticatedReply
from routerscraper.dataTypes import (
        resultValue,
        resultState,
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
    def create_random_token() -> str:
        '''Create a random token string

        Returns:
            str: The random token string
        '''
        return '%032x' % random.randrange(16**32)

    @staticmethod
    def login_cmd7_reply(login_locked: bool = False, token: str = 0) -> dict:
        '''Create the CMD7 JSON reply

        If token is 0 a random one will be generated; if it is None no token
        will be passed.

        Args:
            login_locked (bool, optional): Create the login_locked version.
                                           Defaults to False.
            token (str, optional): The token to embed. Defaults to 0.

        Returns:
            dict: The reply to the CMD7 request
        '''
        result = {
            'login_confirm': {
                'login_locked': '1' if login_locked else '0',
                'login_confirm': 'end'
                }
            }
        if token == 0:
            token = TestFastgate_dn8245f2.create_random_token()
        if token is not None:
            result['login_confirm']['token'] = token

        return result

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

    ####################################
    # Check _requestData login         #
    ####################################

    @mock.patch('routerscraper.basescraper.requests.get')
    def test_requestData_need_login(self, mock_get):
        '''Test a reply where the server needs login for the service
        '''
        def successResponse(url: str, params: dict):
            return MockResponse(status_code=200, content=b'Dummy')
        helper = ForceAuthenticatedReply(self._host, self._user, self._pass,
                                         successResponse)
        mock_get.side_effect = helper.get_response

        got = self._component._requestData('connected_device_list',
                                           autologin=False).state
        exp = resultState.MustLogin

        self.assertEqual(got, exp)

    @mock.patch('routerscraper.basescraper.requests.get')
    def test_requestData_autologin(self, mock_get):
        '''Test a reply where the server needs login and library performs it
        '''
        contentStr = 'test_requestData_autologin correct result'

        def successResponse(url: str, params: dict):
            result = MockResponse(status_code=200)
            result.content = contentStr.encode(result.encoding)
            return result
        helper = ForceAuthenticatedReply(self._host, self._user, self._pass,
                                         successResponse)
        mock_get.side_effect = helper.get_response

        got = self._component._requestData('connected_device_list',
                                           autologin=True)
        exp = resultValue(resultState.Completed, contentStr)

        self.assertEqual(got, exp)

    @mock.patch('routerscraper.basescraper.requests.get')
    def test_requestData_autologin_fail_step0(self, mock_get):
        '''Test a reply where the server needs login and login failed at step 0
        '''
        def successResponse(url: str, params: dict):
            return MockResponse(status_code=200, content=b'Dummy')
        helper = ForceAuthenticatedReply(self._host, self._user, self._pass,
                                         successResponse)
        helper.setExecuteStep(0, False)
        mock_get.side_effect = helper.get_response

        got = self._component._requestData('connected_device_list',
                                           autologin=True).state
        exp = resultState.MustLogin

        self.assertEqual(got, exp)

    @mock.patch('routerscraper.basescraper.requests.get')
    def test_requestData_autologin_fail_step1(self, mock_get):
        '''Test a reply where the server needs login and login failed at step 1
        '''
        def successResponse(url: str, params: dict):
            return MockResponse(status_code=200, content=b'Dummy')
        helper = ForceAuthenticatedReply(self._host, self._user, self._pass,
                                         successResponse)
        helper.setExecuteStep(1, False)
        mock_get.side_effect = helper.get_response

        got = self._component._requestData('connected_device_list',
                                           autologin=True).state
        exp = resultState.MustLogin

        self.assertEqual(got, exp)

    ####################################
    # Check login                      #
    ####################################

    @mock.patch('routerscraper.basescraper.requests.get')
    def test_login_ConnectionError_step1(self, mock_get):
        '''Test login fails for ConnectionError at step 1
        '''
        mock_get.return_value = MockResponse(status_code=400)

        got = self._component.login()
        exp = loginResult.ConnectionError

        self.assertEqual(got, exp)
        mock_get.assert_called_once_with(f'http://{self._host}/status.cgi',
                                         params={
                                            'nvget': 'login_confirm',
                                            'cmd': '7'
                                         }, cookies=None)

    @mock.patch('routerscraper.basescraper.requests.get')
    def test_login_noJson_step1(self, mock_get):
        '''Test login fails for missing JSON at step 1
        '''
        content = b'test_login_noJson_step1 wrong data'
        mock_get.return_value = MockResponse(status_code=200, content=content)

        got = self._component.login()
        exp = loginResult.ConnectionError

        self.assertEqual(got, exp)
        mock_get.assert_called_once_with(f'http://{self._host}/status.cgi',
                                         params={
                                            'nvget': 'login_confirm',
                                            'cmd': '7'
                                         }, cookies=None)

    @mock.patch('routerscraper.basescraper.requests.get')
    def test_login_locked(self, mock_get):
        '''Test login fails because login was locked
        '''
        json_data = self.login_cmd7_reply(login_locked=True)
        contentStr = json.dumps(json_data)
        positiveResponse = MockResponse(status_code=200)
        positiveResponse.json_data = json_data
        positiveResponse.content = contentStr.encode(positiveResponse.encoding)
        mock_get.return_value = positiveResponse

        got = self._component.login()
        exp = loginResult.Locked

        self.assertEqual(got, exp)
        mock_get.assert_called_once_with(f'http://{self._host}/status.cgi',
                                         params={
                                            'nvget': 'login_confirm',
                                            'cmd': '7'
                                         }, cookies=None)

    @mock.patch('routerscraper.basescraper.requests.get')
    def test_login_no_token(self, mock_get):
        '''Test login fails because no token was provided
        '''
        json_data = self.login_cmd7_reply(token=None)
        contentStr = json.dumps(json_data)
        positiveResponse = MockResponse(status_code=200)
        positiveResponse.json_data = json_data
        positiveResponse.content = contentStr.encode(positiveResponse.encoding)
        mock_get.return_value = positiveResponse

        got = self._component.login()
        exp = loginResult.NoToken

        self.assertEqual(got, exp)
        mock_get.assert_called_once_with(f'http://{self._host}/status.cgi',
                                         params={
                                            'nvget': 'login_confirm',
                                            'cmd': '7'
                                         }, cookies=None)

    @mock.patch('routerscraper.basescraper.requests.get')
    def test_login_ConnectionError_step2(self, mock_get):
        '''Test login fails for ConnectionError at step 2
        '''
        token = self.create_random_token()
        json_data = self.login_cmd7_reply(token=token)
        contentStr = json.dumps(json_data)
        firstResponse = MockResponse(status_code=200)
        firstResponse.json_data = json_data
        firstResponse.content = contentStr.encode(firstResponse.encoding)
        secondResponse = MockResponse(status_code=400)
        mock_get.side_effect = [firstResponse, secondResponse]

        got = self._component.login()
        exp = loginResult.ConnectionError

        self.assertEqual(got, exp)

        calledParams = {
                'nvget': 'login_confirm',
                'cmd': '3',
                'username': self._user,
                'password': self._hashedpass,
                'token': token
            }
        mock_get.assert_called_with(f'http://{self._host}/status.cgi',
                                    params=calledParams, cookies=None)

    @mock.patch('routerscraper.basescraper.requests.get')
    def test_login_noJson_step2(self, mock_get):
        '''Test login fails for missing JSON at step 2
        '''
        token = self.create_random_token()
        json_data = self.login_cmd7_reply(token=token)
        contentStr = json.dumps(json_data)
        firstResponse = MockResponse(status_code=200)
        firstResponse.json_data = json_data
        firstResponse.content = contentStr.encode(firstResponse.encoding)
        content2 = b'test_login_noJson_step2 wrong data'
        secondResponse = MockResponse(status_code=200, content=content2)
        mock_get.side_effect = [firstResponse, secondResponse]

        got = self._component.login()
        exp = loginResult.ConnectionError

        self.assertEqual(got, exp)

        calledParams = {
                'nvget': 'login_confirm',
                'cmd': '3',
                'username': self._user,
                'password': self._hashedpass,
                'token': token
            }
        mock_get.assert_called_with(f'http://{self._host}/status.cgi',
                                    params=calledParams, cookies=None)

    @mock.patch('routerscraper.basescraper.requests.get')
    def test_login_wrong_user(self, mock_get):
        '''Test login fails for wrong user
        '''
        def successResponse(url: str, params: dict):
            return MockResponse(status_code=200, content=b'Dummy')
        helper = ForceAuthenticatedReply(self._host, 'wrongUser', self._pass,
                                         successResponse)
        mock_get.side_effect = helper.get_response

        got = self._component.login()
        exp = loginResult.WrongUser

        self.assertEqual(got, exp)

    @mock.patch('routerscraper.basescraper.requests.get')
    def test_login_wrong_password(self, mock_get):
        '''Test login fails for wrong password
        '''
        def successResponse(url: str, params: dict):
            return MockResponse(status_code=200, content=b'Dummy')
        helper = ForceAuthenticatedReply(self._host, self._user, 'wrongPass',
                                         successResponse)
        mock_get.side_effect = helper.get_response

        got = self._component.login()
        exp = loginResult.WrongPass

        self.assertEqual(got, exp)

    @mock.patch('routerscraper.basescraper.requests.get')
    def test_login_success(self, mock_get):
        '''Test login was successful
        '''
        def successResponse(url: str, params: dict):
            return MockResponse(status_code=200, content=b'Dummy')
        helper = ForceAuthenticatedReply(self._host, self._user, self._pass,
                                         successResponse)
        mock_get.side_effect = helper.get_response

        got = self._component.login()
        exp = loginResult.Success

        self.assertEqual(got, exp)

    ####################################
    # Check listDevices                #
    ####################################

    @mock.patch('routerscraper.basescraper.requests.get')
    def test_listDevices_ConnectionError(self, mock_get):
        '''Test listDevices fails for ConnectionError
        '''
        mock_get.return_value = MockResponse(status_code=400)

        got = self._component.listDevices()
        exp = []

        self.assertEqual(got, exp)
        mock_get.assert_called_once_with(f'http://{self._host}/status.cgi',
                                         params={
                                            'nvget': 'connected_device_list',
                                         }, cookies=None)

    @mock.patch('routerscraper.basescraper.requests.get')
    def test_listDevices_noJson(self, mock_get):
        '''Test listDevices fails for missing JSON
        '''
        content = b'test_listDevices_noJson wrong data'
        mock_get.return_value = MockResponse(status_code=200, content=content)

        got = self._component.listDevices()
        exp = []

        self.assertEqual(got, exp)
        mock_get.assert_called_once_with(f'http://{self._host}/status.cgi',
                                         params={
                                            'nvget': 'connected_device_list',
                                         }, cookies=None)

    @mock.patch('routerscraper.basescraper.requests.get')
    def test_listDevices_emptyJson(self, mock_get):
        '''Test listDevices has no output for an empty JSON
        '''
        json_data = {}
        mock_get.return_value = MockResponse(status_code=200,
                                             json_data=json_data)

        got = self._component.listDevices()
        exp = []

        self.assertEqual(got, exp)
        mock_get.assert_called_once_with(f'http://{self._host}/status.cgi',
                                         params={
                                            'nvget': 'connected_device_list',
                                         }, cookies=None)

    @mock.patch('routerscraper.basescraper.requests.get')
    def test_listDevices_emptyItem(self, mock_get):
        '''Test listDevices has no output for an empty connected_device_list
        '''
        json_data = {'connected_device_list': {}}
        mock_get.return_value = MockResponse(status_code=200,
                                             json_data=json_data)

        got = self._component.listDevices()
        exp = []

        self.assertEqual(got, exp)
        mock_get.assert_called_once_with(f'http://{self._host}/status.cgi',
                                         params={
                                            'nvget': 'connected_device_list',
                                         }, cookies=None)

    @mock.patch('routerscraper.basescraper.requests.get')
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
        mock_get.return_value = MockResponse(status_code=200,
                                             json_data=json_data)

        got = self._component.listDevices()
        exp = []

        self.assertEqual(got, exp)
        mock_get.assert_called_once_with(f'http://{self._host}/status.cgi',
                                         params={
                                            'nvget': 'connected_device_list',
                                         }, cookies=None)

    @mock.patch('routerscraper.basescraper.requests.get')
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
        mock_get.return_value = MockResponse(status_code=200,
                                             json_data=json_data)

        got = self._component.listDevices()
        exp = connDevs

        self.assertEqual(got, exp)
        mock_get.assert_called_once_with(f'http://{self._host}/status.cgi',
                                         params={
                                            'nvget': 'connected_device_list',
                                         }, cookies=None)

    @mock.patch('routerscraper.basescraper.requests.get')
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
        mock_get.return_value = MockResponse(status_code=200,
                                             json_data=json_data)

        got = self._component.listDevices()
        exp = connDevs[:2]

        self.assertEqual(got, exp)
        mock_get.assert_called_once_with(f'http://{self._host}/status.cgi',
                                         params={
                                            'nvget': 'connected_device_list',
                                         }, cookies=None)

    @mock.patch('routerscraper.basescraper.requests.get')
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
        mock_get.return_value = MockResponse(status_code=200,
                                             json_data=json_data)

        got = self._component.listDevices()
        exp = connDevs

        self.assertEqual(got, exp)
        mock_get.assert_called_once_with(f'http://{self._host}/status.cgi',
                                         params={
                                            'nvget': 'connected_device_list',
                                         }, cookies=None)

    @mock.patch('routerscraper.basescraper.requests.get')
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
        mock_get.return_value = MockResponse(status_code=200,
                                             json_data=json_data)

        got = self._component.listDevices()
        exp = [c, c]  # Expecting only the first and the last

        self.assertEqual(got, exp)
        mock_get.assert_called_once_with(f'http://{self._host}/status.cgi',
                                         params={
                                            'nvget': 'connected_device_list',
                                         }, cookies=None)
