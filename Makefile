PYTHON = python3
VENV_PATH = .venv
VENV_PYTHON = ${VENV_PATH}/bin/python3
DEV_TOOLS_PATH = ./dist/DevTools.app

.PHONY: app
app:
	@rm -rf dist build
	@pyinstaller -n DevTools -w --clean main.py
	@open $(DEV_TOOLS_PATH)


fmt:
	${VENV_PYTHON} -m isort ./app
	${VENV_PYTHON} -m black ./app
