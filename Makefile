#
# Makefile for the project
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2022 fra87
#

VENV ?= .venv

.PHONY: all clean
.PHONY: create_venv clean_venv
.PHONY: code_review tests
.PHONY: release-tests release-major

all: $(VENV)/bin/activate

clean:
	@find -iname "*.pyc" -not -path "./$(VENV)/*" -delete
	@echo "Removed script compiled files"

$(VENV)/bin/activate: pyproject.toml
# Clean before reinstalling (not to be put in dependencies otherwise it will
# always be executed)
	@make clean_venv --no-print-directory
# Install python3-venv if it is not yet installed
	@dpkg -l python3-venv | grep -q ^ii || sudo apt install python3-venv

	@echo "Creating new virtual environment"
	@python3 -m venv $(VENV)
	@echo "Upgrading pip and setuptools"
	@$(VENV)/bin/python3 -m pip install --upgrade pip setuptools wheel
	@echo "Installing library dependencies"
	@$(VENV)/bin/python3 -m pip install --upgrade -e ".[dev]"

create_venv: $(VENV)/bin/activate

clean_venv:
	@rm -rf $(VENV)
	@echo "Removed virtual environment"

code_review: $(VENV)/bin/activate
	@echo "Running flake8"
	@$(VENV)/bin/flake8 src examples tests && echo "Script is flake8 compliant"
	@echo "Running reuse"
	@$(VENV)/bin/reuse lint

tests: $(VENV)/bin/activate
	@echo "Running unit tests"
	@$(VENV)/bin/python3 -m unittest discover tests

release-tests:
	@make tests --no-print-directory
	@make code_review --no-print-directory

release-major:
	@echo "Not implemented yet"
	@false
	@[ -z "$$(git status --porcelain=v1 2>/dev/null)" ] || { echo "GIT is not clean; please commit before releasing"; false; }
	@make release-tests --no-print-directory

release-minor:
	@echo "Not implemented yet"
	@false
	@[ -z "$$(git status --porcelain=v1 2>/dev/null)" ] || { echo "GIT is not clean; please commit before releasing"; false; }
	@make release-tests --no-print-directory

release-patch:
	@echo "Not implemented yet"
	@false
	@[ -z "$$(git status --porcelain=v1 2>/dev/null)" ] || { echo "GIT is not clean; please commit before releasing"; false; }
	@make release-tests --no-print-directory
