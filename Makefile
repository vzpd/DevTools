PYTHON = python3
VENV_PATH = .venv

init: pyproject.toml
	@${PYTHON} -m virtualenv ${VENV_PATH}
	@${VENV_PATH}/bin/python3 -m pip install poetry
	@${VENV_PATH}/bin/python3 -m poetry env use ${VENV_PATH}/bin/python3
	@${VENV_PATH}/bin/python3 -m poetry lock
	@${VENV_PATH}/bin/python3 -m poetry install


create-app:
	@rm -rf dist build
	@pyinstaller -n DevTools -w --clean main.py

