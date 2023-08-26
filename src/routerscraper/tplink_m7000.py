#!/usr/bin/env python3
###############################################################################
#
# tplink_m7000 - Class for scraping data from TP-Link M7000
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2023 fra87
#
from __future__ import annotations

import selenium
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
from typing import Any
from uuid import uuid4
import json
from datetime import datetime

from .seleniumscraper import seleniumScraper
from .dataTypes import (
        dataService,
        loginResult,
        connectedDevice,
        sms
    )


class tplink_m7000(seleniumScraper):
    '''Class for scraping data from TP-Link M7000
    '''

    # List of services URLs
    _dataServicesUrl = {
        dataService.Home: 'settings.html',
        dataService.Login: '',
    }

    def _isLoggedIn(self) -> bool:
        '''Check if the current webpage is logged in

        Returns:
            bool: True if the webpage is logged in
        '''
        # Page is logged in if there is any content in the container
        try:
            result = bool(self._driver.find_element(By.ID, 'container').text)
        except selenium.common.exceptions.NoSuchElementException:
            # If there is no container, this is login page (so not logged in)
            result = False
        return result

    def _internal_login(self, cleanStart: bool = True) -> loginResult:
        '''Perform a login action

        Note: this function must not be used directly, but only through the
        wrapping login(cleanStart) function.

        Args:
            cleanStart (bool, optional): Remove cookies and start from scratch.
                                         Defaults to True.

        Returns:
            loginResult: The login outcome
        '''
        # Navigate to the login page
        self.goToPage(dataService.Login, ensureLoggedIn=False)

        def execInputPass(el: WebElement, par: Any) -> Any:
            # Clear the field
            el.clear()
            # Send the password
            el.send_keys(self._password)
            # Confirm input
            el.send_keys(Keys.RETURN)

        inputPassRes = self._executeOnElem(By.ID, "password", execInputPass)

        if not inputPassRes.success:
            return loginResult.ConnectionError

        def execWrongPass(el: WebElement, par: Any) -> Any:
            if not el.text.startswith('Incorrect password,please try again'):
                raise seleniumScraper.ExecuteFuncException
            # If we arrived here, the password was wrong

        wrongPassRes = self._executeOnElem(By.ID, "noteDiv", execWrongPass)
        if wrongPassRes.success:
            return loginResult.WrongPass

        # Check login status (up to 2 seconds)
        st = time.time()
        while not (loggedIn := self._isLoggedIn()):
            if (time.time() - st) >= 2:
                break

        if not loggedIn:
            return loginResult.NotLoggedIn

        return loginResult.Success

    def listDevices(self) -> list[connectedDevice]:
        '''Get the list of connected devices

        If there was a connection error the function returns None

        Returns:
            list[connectedDevice]: The list of connected devices
        '''
        raise NotImplementedError()

    @staticmethod
    def _smsListScript(divId: str, pageNum: int, smsPerPage: int) -> str:

        '''Get the JS script to collect the SMS from the router

        Args:
            divId (str): The ID of the DIV where the result will be appended
            pageNum (int): The page number to fetch
            smsPerPage (int): The number of SMS per page to fetch

        Returns:
            str: The JS script
        '''
        result = '''
if (typeof callJSON === 'undefined')
    return false

callJSON({
    module: Globals.MODULES.message,
    action: 2, // readMsg
    data: { pageNumber: %%pageNum%%, amountPerPage: %%smsPerPage%%, box: 0 },
    success: function(a) {
        el = document.getElementById('%%divId%%')
        if (0 === a.result) {
            res = {totalNumber: a.totalNumber, messageList: a.messageList }
            el.textContent = JSON.stringify(res)
            el.setAttribute('status', 'Ready')
        } else {
            el.setAttribute('status', 'Error')
        }
    },
    error: function(err) {
        document.getElementById('%%divId%%').setAttribute('status', 'Error')
    }
})

return true
'''
        result = result.replace('%%divId%%', divId)
        result = result.replace('%%pageNum%%', str(pageNum))
        result = result.replace('%%smsPerPage%%', str(smsPerPage))
        return result

    def _getSmsPage(self, page: int, smsPerPage: int) -> tuple[int, list]:
        '''Get the SMS listed in a single page

        Args:
            page (int): The page number to be fetched
            smsPerPage (int): The number of SMS per page to fetch

        Returns:
            tuple[int, list]: A tuple with the total number of SMS and the list
                              of SMS, or None if there was a connection error
        '''
        # Create a random divId
        divId = str(uuid4())

        # Function to convert from dictionary to sms
        def jsonToSms(j: dict) -> sms:
            number = j['from']
            timest = datetime.strptime(j['receivedTime'], '%Y-%m-%d %H:%M:%S')
            content = j['content']
            additionalInfo = {'index': j['index'], 'unread': j['unread']}
            return sms(number=number, timestamp=timest, content=content,
                       additionalInfo=additionalInfo)

        # Function to get the results
        def execCheckSms(el: WebElement, par: Any) -> Any:
            match el.get_attribute('status'):
                case 'Ready':
                    # Success; el.text now has the result
                    res = json.loads(el.text)
                    smsList = [jsonToSms(sms) for sms in res['messageList']]
                    return (res['totalNumber'], smsList)
                case 'Error':
                    return None
                case _:
                    # Still processing; test again later
                    raise seleniumScraper.ExecuteFuncException

        # Create the DIV required for results storing
        self.createDiv(divId, attributes={'status': 'Processing'})

        # Retry a couple of times; the script does not seem too stable
        for _ in range(3):
            # Call the function to get the page data
            self._executeJs(self._smsListScript(divId, page, smsPerPage),
                            timeout=5)

            # Parse the results
            checkSmsRes = self._executeOnElem(By.ID, divId, execCheckSms)

            if checkSmsRes.success:
                break

        self.removeDiv(divId)

        if not checkSmsRes.success:
            return None

        return checkSmsRes.result

    def getSmsList(self) -> list[sms]:
        '''Get the list of connected devices

        If there was a connection error the function returns None

        Returns:
            list[connectedDevice]: The list of connected devices, or None if
                                   there was a connection error
        '''
        self.goToPage(dataService.Home, ensureLoggedIn=True)

        smsPerPage = 8  # Other values did not work

        # Get the first SMS page
        res = self._getSmsPage(1, smsPerPage)

        def smsResToDict(r):
            return {int(s.additionalInfo['index']): s for s in r[1]}

        if res is None:
            return None

        # res[0] has the number of messages
        totalNum = res[0]
        totalPages = (totalNum + smsPerPage - 1) // smsPerPage

        # Convert the received sms in a dict
        resultDict = smsResToDict(res)

        # Get SMS from page 2 to totalPages (included)
        for page in range(2, totalPages + 1):
            # Receive SMSs
            res = self._getSmsPage(page, smsPerPage)
            if res is None:
                return None

            # Add the values to the resultDict
            resultDict.update(smsResToDict(res))

        # Sort values in date reverse order (so from most recent to oldest)
        allSms = resultDict.values()
        return sorted(allSms, key=lambda d: d.timestamp, reverse=True)
