<!--
README.md file

SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: 2022 fra87
-->

# README

Router Scraper

# Details

This project aims at providing a python module to interact with different
routers.

# Project layout

- `README.md`: this file
- **routerscraper**: folder with the scraping module
    - `basescraper.py`: Contains the base class implementation
    - `dataTypes.py`: Module to group data types used in the functions
    - `fastgate_dn8245f2.py`: Contains the implementation for the Fastgate
                              Huawei DN8245f2
    - `technicolor_tg789vacv2.py`: Contains the implementation for the
                                   Technicolor TG789vac v2
- **tests**: folder with the unit tests. Each test file in this folder
             implements tests linked to the corresponding file in the
             **routerscraper** folder; if necessary, helper files group
             functions needed by the corresponding test file.
- **developerscripts**: folder with scripts for developers
    - `create_venv.sh`: Script to create the virtual environment and install
                        dependencies
    - `run_flake8.sh`: Script to run flake8 on python files to test pep8
                       compliance
    - `run_tests.sh`: Script to run test procedures to verify the library
    - `run_reuse.sh`: Script to run the REUSE compliance script
- **examples**: folder with example code
    - `fastgate_dn8245f2.py`: Contains an example implementation for the
                              Fastgate Huawei DN8245f2
    - `technicolor_tg789vacv2.py`: Contains an example implementation for the
                                   Technicolor TG789vac v2
- **LICENSES**: folder with the licenses statements

# Supported routers

At present the module was tested with the following routers firmwares

- Fastgate Huawei DN8245f2 - software 1.0.1b
- Technicolor TG789vac v2 - software 16.3.7636

# Setup the repository

Clone the repository from
[git@github.com:fra87/RouterScraper.git](git@github.com:fra87/RouterScraper.git)
