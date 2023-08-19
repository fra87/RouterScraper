# README

Router Scraper

# Details

This project aims at providing a python package to interact with different
routers.

# Getting started

Import the required class from the `routerscraper` package:

- `fastgate_dn8245f2.py` for the Fastgate Huawei DN8245f2
- `technicolor_tg789vacv2.py` for the Technicolor TG789vac v2
- `tplink_m7000.py` for the TP-Link M7000

The constructor needs the following parameters
- `host`: the hostname (or IP address) of the router
- `user`: the username to log in the router
- `password`: the password to log in the router

Then you can get relevant information with:
- `listDevices()`: get the list of connected devices
- `getSmsList()`: get the list of SMS present on the device

The functions automatically issue a login request if necessary.


## Supported functions

Not all functions are supported by all devices. See table below for supported
functions:

| Function                 | `listDevices()` | `getSmsList()` |
| :----------------------- | :-------------: | :------------: |
| Fastgate Huawei DN8245f2 |        X        |                |
| Technicolor TG789vac v2  |        X        |                |
| TP-Link M7000            |                 |        X       |

## Saving and restoring sessions

It is possible to export the sessions to later restore them; this can be used
to avoid having to login every time.

To do this, you can export the current status through `exportSessionStatus`,
which returns a string (base64 encoded JSON dict) that can be saved. The
`restoreSessionStatus` function restores the status from that string.

# Supported routers

At present the package was tested with the following routers firmwares

- Fastgate Huawei DN8245f2 - software 1.0.1b
- Technicolor TG789vac v2 - software 16.3.7636
- TP-Link M7000 - software 1.0.10 Build 211230 Rel.1026n

# Developer notes

Here are some additional notes for developing the library (not just using it).

## Project layout

- `README.md`: This file
- `README.md.license`: License information for this file
- `pyproject.toml`: Configuration file for build environment
- `setup.py`: Fallback file for editable installs
- `Makefile`: Makefile to help running development scripts
- **src/routerscraper**: Folder with the scraping package
    - `basescraper.py`: Contains the base class implementation
    - `requestscraper.py`: Contains the base class for scrapers using requests
    - `seleniumscraper.py`: Contains the base class for scrapers using Selenium
    - `dataTypes.py`: Module to group data types used in the functions
    - `fastgate_dn8245f2.py`: Contains the implementation for the Fastgate
                              Huawei DN8245f2
    - `technicolor_tg789vacv2.py`: Contains the implementation for the
                                   Technicolor TG789vac v2
    - `tplink_m7000.py`: Contains the implementation for the TP-Link M7000
- **tests**: Folder with the unit tests. Each test file in this folder
             implements tests linked to the corresponding file in the
             **routerscraper** folder; if necessary, helper files group
             functions needed by the corresponding test file. **files_\***
             folder contains files needed by the test files.
             `helpers_common.py` implements some classes useful for all the
             tests.
- **examples**: Folder with example code
    - `fastgate_dn8245f2.py`: Contains an example implementation for the
                              Fastgate Huawei DN8245f2
    - `technicolor_tg789vacv2.py`: Contains an example implementation for the
                                   Technicolor TG789vac v2
    - `tplink_m7000.py`: Contains an example implementation for the TP-Link
                         M7000
- **LICENSES**: Folder with the licenses statements

## Examples

All example scripts behave in the same way. They will connect to the router and
print the list of connected devices (or the received SMS, in the case of the
TP-Link).

Call the script with three parameters:

1. URL of the router
2. USERNAME
3. PASSWORD

## Makefile

For development purposes there is a Makefile to automate the different actions.

The available targets are:

- **all**: Build the package (equal to make dist); this is the goal (i.e.
           target executed when calling make without targets)
- **clean**: Clean the project (removing all the .pyc files)
- **dist**: Build the package (both .tar.gz and .whl archives)
- **deploy**: Upload the package on PyPI
- *.venv/bin/activate*: Target to create the virtual environment
- **create_venv**: Easier to remember PHONY to create the virtual environment
- **clean_venv**: Remove the virtual environment
- **code_review**: Run the commands to review the code (flake8 and reuse)
- **tests**: Run the tests on the library
- **release-tests**: Execute all the checks for a release; this target is
                     automatically executed by the other **release-** targets.
- **release-major**: Release the current version bumping the major index. This
                     target needs that the GIT has no uncommitted changes and
                     must be run from the main branch only.
- **release-minor**: Release the current version bumping the minor index. This
                     target needs that the GIT has no uncommitted changes and
                     must be run from the main branch only.
- **release-patch**: Release the current version bumping the patch index. This
                     target needs that the GIT has no uncommitted changes and
                     must be run from the main branch only.
- **check-git-clean**: Helper recipe that tests if GIT repo is clean
- **check-git-on-main**: Helper recipe that tests if GIT repo is on main branch

Note: **bold** targets are PHONY, *italic* ones are files.

All the operations will happen in a virtual environment. The virtual
environment folder is set in environment variable VENV, which defaults to
*.venv*.

NOTE: if you change the prerequisites in the pyproject.toml, remember to run
`make clean_venv` to recreate the virtual environment with the new data.

## Release procedure

In order to release a new version, everything shall be already committed to the
GIT repo (since the process requires a clean GIT repo); in addition, the repo
shall be on main branch. If this is not true, the process will fail.

After having committed the last modifications, issue the following commands:

    make clean
    make release-XXX

The release target shall be `release-major`, `release-minor` or `release-patch`,
according to which part of the software version shall be increased.

If everything is correct, run `make deploy` to upload the files to PyPI.

## Setup the repository

Clone the repository from
[git@github.com:fra87/RouterScraper.git](git@github.com:fra87/RouterScraper.git)
