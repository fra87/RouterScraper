#!/usr/bin/env python3
###############################################################################
#
# seleniumScraper - Base class for Scraper classes using Selenium.
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2023 fra87
#
from __future__ import annotations

from abc import abstractmethod
import selenium
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.remote.webelement import WebElement
import time
from os import devnull
from typing import Callable, Any
from dataclasses import dataclass
from pathlib import Path

from .basescraper import baseScraper
from .dataTypes import (
        dataService,
        loginResult,
    )


class seleniumScraper(baseScraper):
    '''Base class for router scraper classes that use Selenium
    '''

    def __init__(self, host: str, user: str, password: str,
                 seeWindow: bool = False, geckoLogPath: Path = None):
        '''Initialize the object

        The path for the gecko log can be either:
        - None -> No file will be created (so redirected to os.devnull)
        - A DIR path -> file geckodrivers.log will be created inside that dir
        - A FILE path -> that file will be used for the logs

        Args:
            host (str): The host address of the router
            user (str): The username for the connection
            password (str): The password for the connection
            seeWindow (bool, optional): If True, open the browser window so you
                                        can see the operations, and leave it
                                        open at the end of the program.
                                        Defaults to False.
            geckoLogPath (Path, optional): The path for the gecko log. Defaults
                                           to None.
        '''
        super().__init__(host, user, password)
        self._seeWindow = seeWindow

        self._geckoLogPath = geckoLogPath

        # Management of the gecko path
        # If none was passed, redirect to os.devnull
        if self._geckoLogPath is None:
            self._geckoLogPath = devnull
        # If it was not a path, try to convert it
        if not isinstance(self._geckoLogPath, Path):
            self._geckoLogPath = Path(self._geckoLogPath)
        # If it was a dir, use file geckodrivers.log inside it
        if self._geckoLogPath.is_dir():
            self._geckoLogPath = self._geckoLogPath / 'geckodrivers.log'

    def __enter__(self):
        # Create the window
        options = Options()
        options.headless = not self._seeWindow
        service = Service(log_path=self._geckoLogPath)

        self._driver = Firefox(options=options, service=service)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self._seeWindow:
            # Close the window
            self._driver.close()

    @abstractmethod
    def _isLoggedIn(self) -> bool:
        '''Check if the current webpage is logged in

        Returns:
            bool: True if the webpage is logged in
        '''
        pass

    def goToPage(self, service: dataService, ensureLoggedIn: bool = True,
                 loginCheckTimeout: float = 2) -> bool:
        '''Move the browser to the webpage associated to service

        Args:
            service (dataService): The service
            ensureLoggedIn (bool, optional): If True, the page checks if the
                                             destination page is logged in, and
                                             if not tries to perform a login.
                                             Defaults to True.
            loginCheckTimeout (float, optional): Time after which the login
                                                 check times out, in seconds.
                                                 Defaults to 2.

        Returns:
            bool: True if the page was set correctly (meaningful in case of
                  login)
        '''
        self._driver.get(self._getUrl(service))

        if ensureLoggedIn:
            st = time.time()
            while not (loggedIn := self._isLoggedIn()):
                if (time.time() - st) >= loginCheckTimeout:
                    break

            if not loggedIn:
                if self.login() != loginResult.Success:
                    return False

                self._driver.get(self._getUrl(service))

        return True

    def _getUrl(self, service: dataService) -> str:
        '''Get the URL associated to a service

        Args:
            service (dataService): The service

        Raises:
            ValueError: The service is not valid

        Returns:
            str: The URL associated to the service
        '''
        if service not in self._dataServicesUrl:
            raise ValueError(f'Service {service} not supported')
        return f'http://{self._host}/{self._dataServicesUrl[service]}'

    @dataclass(frozen=True)
    class ExecuteResult:
        success: bool
        '''True if the execute function was successful'''
        result: Any
        '''The value returned by the function'''

    class ExecuteFuncException(Exception):
        pass

    def _executeJs(self, jsScript: str, timeout: int = 10
                   ) -> seleniumScraper.ExecuteResult:
        '''Execute a Javascript script ignoring exceptions

        In order to signal a failure and schedule a retry of the operation, the
        javascript script shall return `false`. If another value (`true` or no
        value) is returned, the script is considered successful.

        Args:
            jsScript (str): The script to execute
            timeout (int, optional): The time (in seconds) to pass before
                                     considering the operation failed, or None
                                     to never time out. Defaults to 10.

        Returns:
            executeResult: The result of the operation
        '''

        # Start the timeout timer
        st = time.time()

        # Implicit wait is necessary to wait for the element to be rendered
        self._driver.implicitly_wait(10)

        done = False
        res = None
        while not done:
            try:
                res = self._driver.execute_script(jsScript)
                if res is True:
                    done = True
            except selenium.common.exceptions.JavascriptException:
                # Maybe not all elements were ready; retry again
                pass
            if (timeout is not None) and ((time.time() - st) >= timeout):
                # If operation timed out, exit
                break
            # If we did not complete the function, let's wait for some time
            if not done:
                time.sleep(0.5)

        return seleniumScraper.ExecuteResult(done, res)

    def _executeOnElem(self, elemBy, elemValue: str,
                       func: Callable[[WebElement, Any], Any],
                       params: Any = None, timeout: int = 10
                       ) -> seleniumScraper.ExecuteResult:
        '''Execute an action on an element in the current page.

        When the element is available the function will be executed. The
        function shall accept the `WebElement` on which the action is to be
        applied, alongside with the parameter(s) passed to the main function.
        The value it returned will be returned in the `result` field of the
        executeResult.

        In order to signal a failure and schedule a retry of the operation, the
        function shall raise `ExecuteFuncException`.

        Args:
            elemBy: What is the element descriptor (e.g. By.ID)
            elemValue (str): The element descriptor
            func (Callable[[WebElement, Any],Any]): The function to apply
            params (Any, optional): The parameters to pass to the function.
                                    Defaults to None.
            timeout (int, optional): The time (in seconds) to pass before
                                     considering the operation failed, or None
                                     to never time out. Defaults to 10.

        Returns:
            executeResult: The result of the operation
        '''

        # Start the timeout timer
        st = time.time()

        # Implicit wait is necessary to wait for the element to be rendered
        self._driver.implicitly_wait(10)

        elem = None
        done = False
        res = None
        while not done:
            try:
                if elem is None:
                    elem = self._driver.find_element(elemBy, elemValue)
                if elem is not None:
                    res = func(elem, params)
                    # If function completes, we arrived to the end
                    done = True
            except (selenium.common.exceptions.ElementNotInteractableException,
                    selenium.common.exceptions.NoSuchElementException,
                    seleniumScraper.ExecuteFuncException):
                # Element is not ready yet; wait and retry
                pass
            except selenium.common.exceptions.StaleElementReferenceException:
                # Elem is no longer connected to the DOM, so the page was
                # changed. Exit immediately
                break
            if (timeout is not None) and ((time.time() - st) >= timeout):
                # If operation timed out, exit
                break
            # If we did not complete the function, let's wait for some time
            if not done:
                time.sleep(0.5)

        return seleniumScraper.ExecuteResult(done, res)

    # Helper functions
    def createDiv(self, divId: str, parentId: str = None, attributes: dict = {}
                  ):
        '''Create a DIV in the webpage.

        The DIV will have ID `divId` and will be put as child of element with
        ID `parentId`. If None is passed as parent, the div will be appended to
        the body

        Args:
            divId (str): The ID of the DIV to create
            parentId (str, optional): ID of the parent element, or None if
                                      parent will be body. Defaults to None.
            attributes (dict, optional): Dictionary with attributes to apply to
                                         the div. Defaults to {}.
        '''
        # Force at least the ID as attributes
        attributes['id'] = divId

        if parentId is not None:
            parent = f"document.getElementById('{parentId}')"
        else:
            parent = 'document.body'
        jsScriptLines = [
                "resultDiv = document.createElement('div');",
                f'{parent}.appendChild(resultDiv);'
            ]
        for key, val in attributes.items():
            jsScriptLines.append(f"resultDiv.setAttribute('{key}', '{val}');")

        self._driver.execute_script('\n'.join(jsScriptLines))

    def removeDiv(self, divId: str):
        '''Remove a DIV from the webpage

        Args:
            divId (str): The ID of the DIV to remove
        '''
        jsScript = f"document.getElementById('{divId}').remove()"

        self._driver.execute_script(jsScript)
