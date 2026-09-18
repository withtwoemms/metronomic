.PHONY: clean clean-pyc clean-venv tree venv

SYSTEM_PYTHON = $(shell which python3)
PROJECT_NAME = $(shell basename $(CURDIR))
VENV = $(PROJECT_NAME)-venv
VENV_PYTHON = $(VENV)/bin/python
REQUIREMENTS = $(CURDIR)/requirements.txt


all: venv install

venv:
	@$(SYSTEM_PYTHON) -m pip install virtualenv
	@$(SYSTEM_PYTHON) -m virtualenv $(VENV) >/dev/null

venv-dir:
	@echo $(CURDIR)/$(VENV)

install: $(VENV_PYTHON)
	@$(VENV_PYTHON) -m pip install -r $(REQUIREMENTS)

shell: $(VENV_PYTHON)
	@$(VENV_PYTHON) -m bpython

tree:
	@tree $(CURDIR) -I '$(VENV)'

clean: clean-venv clean-pyc

clean-pyc:
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@find . -name '*~' -exec rm -f {} +
	@find . -name '__pycache__' -exec rm -fr {} +

clean-venv:
	@rm -rf $(VENV)
