#!/usr/bin/env python3
###############################################################################
#
# requestScraper - Base class for requests Scraper classes.
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2022 fra87
#

import unittest
from unittest import mock
import json
import base64
import requests

from helpers_common import MockResponse, RecordedRequest
from helpers_requestscraper import tester_for_requestData, SessionMock_Auth
from routerscraper.dataTypes import (
        dataService,
        resultState,
        responsePayload,
        resultValue,
        # loginResult,
        # connectedDevice
    )


class TestRequestScraper(unittest.TestCase):
    '''Test the requests scraper implementation
    '''

    def setUp(self):
        '''Setup for each test

        Tests will have a component already configured, together with the host
        and login credentials already stored
        '''
        self._host = 'correctHost'
        self._user = 'correctUser'
        self._pass = 'correctPass'
        self._component = tester_for_requestData(self._host, self._user,
                                                 self._pass)

    ####################################
    # Check session saving/restoring   #
    ####################################

    def test_getSessionDict(self):
        '''Test _getSessionDict function
        '''
        got = self._component._getSessionDict()
        exp = {'lastLoginResult': 'Login was not attempted'}
        self.assertEqual(got, exp)

    def test_setSessionDict_fail(self):
        '''Test _getSessionDict function when failing
        '''
        dicts = {
                'empty dict': {},
                'wrong key': {'key': 'val'},
                'wrong val': {'lastLoginResult': 'Wrong login'}
            }
        # Store original value (it shall not be modified
        expDict = self._component._getSessionDict()

        for caption, dict in dicts.items():
            got = self._component._setSessionDict(dict)
            self.assertFalse(got, f'Error with case {caption}')

            currDict = self._component._getSessionDict()
            self.assertEqual(currDict, expDict, f'Error with case {caption}')

    def test_setSessionDict_success(self):
        '''Test _getSessionDict function when succeeding
        '''
        dict = {'lastLoginResult': 'Login successful'}

        oriDict = self._component._getSessionDict()
        self.assertNotEqual(oriDict, dict)

        got = self._component._setSessionDict(dict)
        self.assertTrue(got)

        currDict = self._component._getSessionDict()
        self.assertEqual(currDict, dict)

    def test_exportSessionStatus(self):
        '''Test exportSessionStatus function
        '''
        dict = {'lastLoginResult': 'Login successful'}
        got = self._component._setSessionDict(dict)
        self.assertTrue(got)

        got = self._component.exportSessionStatus()
        dictStr = json.dumps(dict)
        exp = base64.b64encode(dictStr.encode('utf-8')).decode('ascii')
        self.assertEqual(got, exp)

    def test_restoreSessionStatus_fail(self):
        '''Test restoreSessionStatus function when failing
        '''
        strings = {
                'empty string': '',
                'wrong base64 chars': 'ZXlKc1lYTjA@=',
                'wrong base64 padding': 'eyJsYXN0TG9naW5SZXN',
                'wrong json': 'eyJsYXN0TG9naW5SZXM='
            }
        # Store original value (it shall not be modified)
        expString = self._component.exportSessionStatus()

        for caption, string in strings.items():
            got = self._component.restoreSessionStatus(string)
            self.assertFalse(got, f'Error with case {caption}')

            currStr = self._component.exportSessionStatus()
            self.assertEqual(currStr, expString, f'Error with case {caption}')

    def test_restoreSessionStatus_success(self):
        '''Test restoreSessionStatus function when succeeding
        '''
        string = 'eyJsYXN0TG9naW5SZXN1bHQiOiAiTG9naW4gc3VjY2Vzc2Z1bCJ9'

        oriString = self._component.exportSessionStatus()
        self.assertNotEqual(oriString, string)

        got = self._component.restoreSessionStatus(string)
        self.assertTrue(got)

        currString = self._component.exportSessionStatus()
        self.assertEqual(currString, string)

    ####################################
    # Check _requestData               #
    ####################################

    @mock.patch('routerscraper.requestscraper.requests.Session')
    def test_requestData_get_params(self, mock_Session):
        '''Test parameters passing for GET
        '''
        mock_Session.return_value = SessionMock_Auth()
        # reset so Session object can be rebuilt with mock class
        self._component.resetSession()

        customParams = {'testpar': 'testval'}
        self._component._requestData(dataService.TestValid, customParams,
                                     autologin=False)

        got = self._component._session.lastRequest

        exp = RecordedRequest(type='get', url='testing_library_service',
                              reqParameters={'testpar': 'testval'},
                              other_args=[], other_kwargs={})

        self.assertEqual(got, exp)

    @mock.patch('routerscraper.requestscraper.requests.Session')
    def test_requestData_post_params(self, mock_Session):
        '''Test parameters passing for POST
        '''
        mock_Session.return_value = SessionMock_Auth()
        # reset so Session object can be rebuilt with mock class
        self._component.resetSession()

        customParams = {'testpar': 'testval'}
        self._component._requestData(dataService.TestValid, customParams,
                                     autologin=False, postRequest=True)

        got = self._component._session.lastRequest

        exp = RecordedRequest(type='post', url='testing_library_service',
                              reqParameters={'testpar': 'testval'},
                              other_args=[], other_kwargs={})

        self.assertEqual(got, exp)

    def test_requestData_wrong_service(self):
        '''Test a wrong service
        '''
        with self.assertRaises(ValueError):
            self._component._requestData(dataService.TestNotValid)

    @mock.patch.object(requests.Session, 'get')
    def test_requestData_ConnectionError(self, mock_get):
        '''Test a ConnectionError issue
        '''
        def raise_ConnectionError(*args, **kwargs):
            raise requests.exceptions.ConnectionError()
        mock_get.side_effect = raise_ConnectionError

        got = self._component._requestData(dataService.TestValid).state
        exp = resultState.ConnectionError

        self.assertEqual(got, exp)

    @mock.patch.object(requests.Session, 'get')
    def test_requestData_http_client_error(self, mock_get):
        '''Test a HTTP client error reply
        '''
        mock_get.return_value = MockResponse(status_code=400)

        got = self._component._requestData(dataService.TestValid).state
        exp = resultState.ConnectionError

        self.assertEqual(got, exp)

    @mock.patch.object(requests.Session, 'get')
    def test_requestData_http_server_error(self, mock_get):
        '''Test a HTTP server error reply
        '''
        mock_get.return_value = MockResponse(status_code=500)

        got = self._component._requestData(dataService.TestValid).state
        exp = resultState.ConnectionError

        self.assertEqual(got, exp)

    @mock.patch('routerscraper.requestscraper.requests.Session')
    def test_requestData_need_login(self, mock_Session):
        '''Test a reply where the server needs login for the service
        '''
        mock_Session.return_value = SessionMock_Auth()
        # reset so Session object can be rebuilt with mock class
        self._component.resetSession()

        got = self._component._requestData(dataService.TestValid,
                                           autologin=False).state
        exp = resultState.MustLogin

        self.assertEqual(got, exp)
        self.assertEqual(self._component.isLoggedIn, False)

    @mock.patch('routerscraper.requestscraper.requests.Session')
    def test_requestData_autologin(self, mock_Session):
        '''Test a reply where the server needs login and library performs it
        '''
        mock_Session.return_value = SessionMock_Auth()
        # reset so Session object can be rebuilt with mock class
        self._component.resetSession()

        got = self._component._requestData(dataService.TestValid,
                                           autologin=True)
        exp = resultValue(resultState.Completed, payload='success')

        self.assertEqual(got, exp)
        self.assertEqual(self._component.isLoggedIn, True)

    @mock.patch('routerscraper.requestscraper.requests.Session')
    def test_requestData_autologin_fail(self, mock_Session):
        '''Test a reply where the server needs login and login failed
        '''
        mock_Session.return_value = SessionMock_Auth()
        # reset so Session object can be rebuilt with mock class
        self._component.resetSession()
        self._component._session.positiveResponse = False

        got = self._component._requestData(dataService.TestValid,
                                           autologin=True).state
        exp = resultState.MustLogin

        self.assertEqual(got, exp)
        self.assertEqual(self._component.isLoggedIn, False)

    @mock.patch.object(requests.Session, 'get')
    def test_requestData_success_no_json(self, mock_get):
        '''Test a positive response without JSON
        '''
        contentStr = 'test_requestData_success_no_json correct result'
        positiveResponse = MockResponse(status_code=200)
        positiveResponse.content = contentStr.encode(positiveResponse.encoding)
        mock_get.return_value = positiveResponse

        got = self._component._requestData(dataService.TestValid)

        expPayload = responsePayload.buildFromPayload(contentStr)
        exp = resultValue(resultState.Completed, payload=expPayload)

        self.assertEqual(got, exp)

    @mock.patch.object(requests.Session, 'get')
    def test_requestData_success_json(self, mock_get):
        '''Test a positive response with JSON
        '''
        json_data = {'test': 'test_requestData_success_json'}
        contentStr = json.dumps(json_data)
        positiveResponse = MockResponse(status_code=200)
        positiveResponse.json_data = json_data
        positiveResponse.content = contentStr.encode(positiveResponse.encoding)
        mock_get.return_value = positiveResponse

        got = self._component._requestData(dataService.TestValid)
        expPayload = responsePayload.buildFromPayload(contentStr)
        exp = resultValue(resultState.Completed, payload=expPayload)

        self.assertEqual(got, exp)

    @mock.patch.object(requests.Session, 'get')
    def test_requestData_forced_no_json(self, mock_get):
        '''Test a positive response without JSON when JSON is mandatory
        '''
        contentStr = 'test_requestData_forced_no_json correct result'
        positiveResponse = MockResponse(status_code=200)
        positiveResponse.content = contentStr.encode(positiveResponse.encoding)
        mock_get.return_value = positiveResponse

        got = self._component._requestData(dataService.TestValid,
                                           forceJSON=True)
        expPayload = responsePayload.buildFromPayload(contentStr)
        exp = resultValue(resultState.NotJsonResponse, payload=expPayload,
                          error="Not a JSON response")

        self.assertEqual(got, exp)

    @mock.patch.object(requests.Session, 'get')
    def test_requestData_forced_success(self, mock_get):
        '''Test a positive response without JSON when JSON is mandatory
        '''
        json_data = {'test': 'test_requestData_forced_success'}
        contentStr = json.dumps(json_data)
        positiveResponse = MockResponse(status_code=200)
        positiveResponse.json_data = json_data
        positiveResponse.content = contentStr.encode(positiveResponse.encoding)
        mock_get.return_value = positiveResponse

        got = self._component._requestData(dataService.TestValid,
                                           forceJSON=True)
        expPayload = responsePayload.buildFromPayload(contentStr)
        exp = resultValue(resultState.Completed, payload=expPayload)

        self.assertEqual(got, exp)
