#!/bin/bash
# Script to run flake8 on python files to test pep8 compliance
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2022 fra87
#

if [[ $EUID -eq 0 ]]; then
    echo "This script must NOT be run as root"
    exit 1
fi

TARGETDIR="routerscraper"

# Move to the root of the repository
cd "$(dirname "$0")"/..

# If there is a virtual environment, activate it
VIRTUALENV_PATH=".venv"
[ -d "$VIRTUALENV_PATH" ] && source "$VIRTUALENV_PATH"/bin/activate

flake8 routerscraper examples tests
