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
import requests
import json

from routerscraper.fastgate_dn8245f2 import fastgate_dn8245f2
from routerscraper.fastgate_dn8245f2 import connectedDevice, loginResult
from helpers_fastgate_dn8245f2 import MockResponse, ForceAuthenticatedReply
from routerscraper.requestResult import resultValue, resultState


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
        # Add a valid service for testing purposes only
        self._component._validServices.append('testing_library_service')

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
            dict: _description_
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

    ####################################
    # Check _requestData               #
    ####################################

    def test_requestData_wrong_service(self):
        '''Test a wrong service
        '''
        with self.assertRaises(ValueError):
            self._component._requestData('invalid_service')

    @mock.patch('routerscraper.fastgate_dn8245f2.requests.get')
    def test_requestData_ConnectionError(self, mock_get):
        '''Test a ConnectionError issue
        '''
        def raise_ConnectionError(*args, **kwargs):
            raise requests.exceptions.ConnectionError()
        mock_get.side_effect = raise_ConnectionError

        got = self._component._requestData('testing_library_service').state
        exp = resultState.ConnectionError

        self.assertEqual(got, exp)

    @mock.patch('routerscraper.fastgate_dn8245f2.requests.get')
    def test_requestData_http_client_error(self, mock_get):
        '''Test a HTTP client error reply
        '''
        mock_get.return_value = MockResponse(status_code=400)

        got = self._component._requestData('testing_library_service').state
        exp = resultState.ConnectionError

        self.assertEqual(got, exp)

    @mock.patch('routerscraper.fastgate_dn8245f2.requests.get')
    def test_requestData_http_server_error(self, mock_get):
        '''Test a HTTP server error reply
        '''
        mock_get.return_value = MockResponse(status_code=500)

        got = self._component._requestData('testing_library_service').state
        exp = resultState.ConnectionError

        self.assertEqual(got, exp)

    @mock.patch('routerscraper.fastgate_dn8245f2.requests.get')
    def test_requestData_need_login(self, mock_get):
        '''Test a reply where the server needs login for the service
        '''
        def successResponse(url: str, params: dict):
            return MockResponse(status_code=200, content=b'Dummy')
        helper = ForceAuthenticatedReply(self._host, self._user, self._pass,
                                         successResponse)
        mock_get.side_effect = helper.get_response

        got = self._component._requestData('testing_library_service',
                                           autologin=False).state
        exp = resultState.MustLogin

        self.assertEqual(got, exp)

    @mock.patch('routerscraper.fastgate_dn8245f2.requests.get')
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

        got = self._component._requestData('testing_library_service',
                                           autologin=True)
        exp = resultValue(resultState.Completed, contentStr)

        self.assertEqual(got, exp)

    @mock.patch('routerscraper.fastgate_dn8245f2.requests.get')
    def test_requestData_autologin_fail_step0(self, mock_get):
        '''Test a reply where the server needs login and login failed at step 0
        '''
        def successResponse(url: str, params: dict):
            return MockResponse(status_code=200, content=b'Dummy')
        helper = ForceAuthenticatedReply(self._host, self._user, self._pass,
                                         successResponse)
        helper.setExecuteStep(0, False)
        mock_get.side_effect = helper.get_response

        got = self._component._requestData('testing_library_service',
                                           autologin=True).state
        exp = resultState.MustLogin

        self.assertEqual(got, exp)

    @mock.patch('routerscraper.fastgate_dn8245f2.requests.get')
    def test_requestData_autologin_fail_step1(self, mock_get):
        '''Test a reply where the server needs login and login failed at step 1
        '''
        def successResponse(url: str, params: dict):
            return MockResponse(status_code=200, content=b'Dummy')
        helper = ForceAuthenticatedReply(self._host, self._user, self._pass,
                                         successResponse)
        helper.setExecuteStep(1, False)
        mock_get.side_effect = helper.get_response

        got = self._component._requestData('testing_library_service',
                                           autologin=True).state
        exp = resultState.MustLogin

        self.assertEqual(got, exp)

    @mock.patch('routerscraper.fastgate_dn8245f2.requests.get')
    def test_requestData_success_no_json(self, mock_get):
        '''Test a positive response without JSON
        '''
        contentStr = 'test_requestData_success_no_json correct result'
        positiveResponse = MockResponse(status_code=200)
        positiveResponse.content = contentStr.encode(positiveResponse.encoding)
        mock_get.return_value = positiveResponse

        got = self._component._requestData('testing_library_service')
        exp = resultValue(resultState.Completed, contentStr)

        self.assertEqual(got, exp)

    @mock.patch('routerscraper.fastgate_dn8245f2.requests.get')
    def test_requestData_success_json(self, mock_get):
        '''Test a positive response with JSON
        '''
        json_data = {'test': 'test_requestData_success_json'}
        contentStr = json.dumps(json_data)
        positiveResponse = MockResponse(status_code=200)
        positiveResponse.json_data = json_data
        positiveResponse.content = contentStr.encode(positiveResponse.encoding)
        mock_get.return_value = positiveResponse

        got = self._component._requestData('testing_library_service')
        exp = resultValue(resultState.Completed, contentStr, json_data)

        self.assertEqual(got, exp)

    @mock.patch('routerscraper.fastgate_dn8245f2.requests.get')
    def test_requestData_forced_no_json(self, mock_get):
        '''Test a positive response without JSON when JSON is mandatory
        '''
        contentStr = 'test_requestData_forced_no_json correct result'
        positiveResponse = MockResponse(status_code=200)
        positiveResponse.content = contentStr.encode(positiveResponse.encoding)
        mock_get.return_value = positiveResponse

        got = self._component._requestData('testing_library_service',
                                           forceJSON=True)
        exp = resultValue(resultState.NotJsonResponse, contentStr)

        self.assertEqual(got, exp)

    @mock.patch('routerscraper.fastgate_dn8245f2.requests.get')
    def test_requestData_forced_success(self, mock_get):
        '''Test a positive response without JSON when JSON is mandatory
        '''
        json_data = {'test': 'test_requestData_forced_success'}
        contentStr = json.dumps(json_data)
        positiveResponse = MockResponse(status_code=200)
        positiveResponse.json_data = json_data
        positiveResponse.content = contentStr.encode(positiveResponse.encoding)
        mock_get.return_value = positiveResponse

        got = self._component._requestData('testing_library_service',
                                           forceJSON=True)
        exp = resultValue(resultState.Completed, contentStr, json_data)

        self.assertEqual(got, exp)

    ####################################
    # Check login                      #
    ####################################

    @mock.patch('routerscraper.fastgate_dn8245f2.requests.get')
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

    @mock.patch('routerscraper.fastgate_dn8245f2.requests.get')
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

    @mock.patch('routerscraper.fastgate_dn8245f2.requests.get')
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

    @mock.patch('routerscraper.fastgate_dn8245f2.requests.get')
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

    @mock.patch('routerscraper.fastgate_dn8245f2.requests.get')
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

    @mock.patch('routerscraper.fastgate_dn8245f2.requests.get')
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

    @mock.patch('routerscraper.fastgate_dn8245f2.requests.get')
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

    @mock.patch('routerscraper.fastgate_dn8245f2.requests.get')
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

    @mock.patch('routerscraper.fastgate_dn8245f2.requests.get')
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
