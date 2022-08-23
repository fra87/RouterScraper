#
# Makefile for the project
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2022 fra87
#

VENV ?= .venv

.PHONY: all clean dist deploy
.PHONY: create_venv clean_venv
.PHONY: code_review tests
.PHONY: release-tests release-major release-minor release-patch
.PHONY: check-git-clean check-git-on-main

###################################
# Generic recipes

all: dist

clean:
	@find -iname "*.pyc" -not -path "./$(VENV)/*" -delete
	@echo "Removed script compiled files"
	@rm -rf dist
	@echo "Removed distribution files"

dist: $(VENV)/bin/activate check-git-clean check-git-on-main
	@$(VENV)/bin/python3 -m build
	@$(VENV)/bin/twine check dist/*
	@echo Built distribution files; check them and then, eventually, run make deploy to upload to PyPI

deploy: $(VENV)/bin/activate
	@[ "$(ls -A dist 2>/dev/null)" ] || { echo "No dist files; run make dist before"; false; }
	@echo Uploading packages on PyPI. This operation cannot be undone.
	@( read -p "Are you sure? [y/N]: " sure && case "$$sure" in [yY]) true;; *) echo "Aborting"; false;; esac )
	@$(VENV)/bin/twine upload dist/*

###################################
# Recipes for virtual environment

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

###################################
# Recipes for testing the code

code_review: $(VENV)/bin/activate
	@echo "Running flake8"
	@$(VENV)/bin/flake8 src examples tests && echo "Script is flake8 compliant"
	@echo "Running reuse"
	@$(VENV)/bin/reuse lint

tests: $(VENV)/bin/activate
	@echo "Running unit tests"
	@$(VENV)/bin/python3 -m unittest discover tests

###################################
# Recipes for the release process

release-tests:
	@make tests --no-print-directory
	@make code_review --no-print-directory

release-major: $(VENV)/bin/activate check-git-clean check-git-on-main release-tests
	@$(VENV)/bin/bumpver update --major
	@make dist --no-print-directory

release-minor: $(VENV)/bin/activate check-git-clean check-git-on-main release-tests
	@$(VENV)/bin/bumpver update --minor
	@make dist --no-print-directory

release-patch: $(VENV)/bin/activate check-git-clean check-git-on-main release-tests
	@$(VENV)/bin/bumpver update --patch
	@make dist --no-print-directory

###################################
# Recipes for automatic checking

check-git-clean:
	@[ -z "$$(git status --porcelain=v1 2>/dev/null)" ] || { echo "GIT is not clean; aborting"; false; }

check-git-on-main:
	@[ "$$(git symbolic-ref --short -q HEAD)" = "main" ] || { echo "Not on main branch; aborting"; false; }
