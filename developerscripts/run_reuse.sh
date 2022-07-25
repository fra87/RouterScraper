#!/bin/bash
# Script to run REUSE tools to verify compliance to the licensing standard
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2022 fra87
#

if [[ $EUID -eq 0 ]]; then
    echo "This script must NOT be run as root"
    exit 1
fi

# Move to the root of the repository
cd "$(dirname "$0")"/..

# If there is a virtual environment, activate it
VIRTUALENV_PATH=".venv"
[ -d "$VIRTUALENV_PATH" ] && source "$VIRTUALENV_PATH"/bin/activate

reuse lint
