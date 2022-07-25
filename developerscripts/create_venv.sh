#!/bin/bash
# Script to create the virtual environment and install dependencies
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2022 fra87
#

if [[ $EUID -eq 0 ]]; then
    echo "This script must NOT be run as root"
    exit 1
fi

# returns 1 if the package was already installed and 0 otherwise. The first
# argument is the package name to be checked (and installed if not already).
# other arguments are passed to apt install
# From https://askubuntu.com/a/98467/514586
try_install() {
    dpkg -l "$1" | grep -q ^ii && return 1
    sudo apt install "$@"
    return 0
}

# Move to the root of the repository
cd "$(dirname "$0")"/..

VIRTUALENV_PATH=".venv"

# Ensure venv is installed
try_install python3-venv

# Remove old virtual environment
rm -rf "${VIRTUALENV_PATH}"

# Create virtual environment
python3 -m venv "${VIRTUALENV_PATH}"
PYTHON_BIN="${VIRTUALENV_PATH}"/bin/python

# Upgrade pip (since the inner version is old)
${PYTHON_BIN} -m pip install --upgrade pip setuptools wheel

# Install requirements
${PYTHON_BIN} -m pip install --upgrade flake8 reuse

echo "Virtual Environment ready at ${VIRTUALENV_PATH}"
