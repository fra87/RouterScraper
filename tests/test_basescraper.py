#!/usr/bin/env python3
###############################################################################
#
# baseScraper - Base class for Scraper classes.
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2022 fra87
#

import unittest
from unittest import mock
import json
import requests

from helpers_basescraper import (
        MockResponse,
        tester_for_requestData,
        ForceAuthenticatedReply
    )
from routerscraper.dataTypes import (
        resultValue,
        resultState
    )


class TestBaseScraper(unittest.TestCase):
    '''Test the base scraper implementation
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
    # Check _requestData               #
    ####################################

    def test_requestData_wrong_service(self):
        '''Test a wrong service
        '''
        with self.assertRaises(ValueError):
            self._component._requestData('invalid_service')

    @mock.patch('routerscraper.basescraper.requests.get')
    def test_requestData_ConnectionError(self, mock_get):
        '''Test a ConnectionError issue
        '''
        def raise_ConnectionError(*args, **kwargs):
            raise requests.exceptions.ConnectionError()
        mock_get.side_effect = raise_ConnectionError

        got = self._component._requestData('testing_library_service').state
        exp = resultState.ConnectionError

        self.assertEqual(got, exp)

    @mock.patch('routerscraper.basescraper.requests.get')
    def test_requestData_http_client_error(self, mock_get):
        '''Test a HTTP client error reply
        '''
        mock_get.return_value = MockResponse(status_code=400)

        got = self._component._requestData('testing_library_service').state
        exp = resultState.ConnectionError

        self.assertEqual(got, exp)

    @mock.patch('routerscraper.basescraper.requests.get')
    def test_requestData_http_server_error(self, mock_get):
        '''Test a HTTP server error reply
        '''
        mock_get.return_value = MockResponse(status_code=500)

        got = self._component._requestData('testing_library_service').state
        exp = resultState.ConnectionError

        self.assertEqual(got, exp)

    @mock.patch('routerscraper.basescraper.requests.get')
    def test_requestData_need_login(self, mock_get):
        '''Test a reply where the server needs login for the service
        '''
        helper = ForceAuthenticatedReply(True)
        mock_get.side_effect = helper.get_response

        got = self._component._requestData('testing_library_service',
                                           autologin=False).state
        exp = resultState.MustLogin

        self.assertEqual(got, exp)

    @mock.patch('routerscraper.basescraper.requests.get')
    def test_requestData_autologin(self, mock_get):
        '''Test a reply where the server needs login and library performs it
        '''
        helper = ForceAuthenticatedReply(True)
        mock_get.side_effect = helper.get_response

        got = self._component._requestData('testing_library_service',
                                           autologin=True)
        exp = resultValue(resultState.Completed, payload='success')

        self.assertEqual(got, exp)

    @mock.patch('routerscraper.basescraper.requests.get')
    def test_requestData_autologin_fail(self, mock_get):
        '''Test a reply where the server needs login and login failed
        '''
        helper = ForceAuthenticatedReply(False)
        mock_get.side_effect = helper.get_response

        got = self._component._requestData('testing_library_service',
                                           autologin=True).state
        exp = resultState.MustLogin

        self.assertEqual(got, exp)

    @mock.patch('routerscraper.basescraper.requests.get')
    def test_requestData_success_no_json(self, mock_get):
        '''Test a positive response without JSON
        '''
        contentStr = 'test_requestData_success_no_json correct result'
        positiveResponse = MockResponse(status_code=200)
        positiveResponse.content = contentStr.encode(positiveResponse.encoding)
        mock_get.return_value = positiveResponse

        got = self._component._requestData('testing_library_service')
        exp = resultValue(resultState.Completed, payload=contentStr)

        self.assertEqual(got, exp)

    @mock.patch('routerscraper.basescraper.requests.get')
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
        exp = resultValue(resultState.Completed, payload=contentStr)

        self.assertEqual(got, exp)

    @mock.patch('routerscraper.basescraper.requests.get')
    def test_requestData_forced_no_json(self, mock_get):
        '''Test a positive response without JSON when JSON is mandatory
        '''
        contentStr = 'test_requestData_forced_no_json correct result'
        positiveResponse = MockResponse(status_code=200)
        positiveResponse.content = contentStr.encode(positiveResponse.encoding)
        mock_get.return_value = positiveResponse

        got = self._component._requestData('testing_library_service',
                                           forceJSON=True)
        exp = resultValue(resultState.NotJsonResponse, payload=contentStr, error="Not a JSON response")

        self.assertEqual(got, exp)

    @mock.patch('routerscraper.basescraper.requests.get')
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
        exp = resultValue(resultState.Completed, payload=contentStr)

        self.assertEqual(got, exp)
