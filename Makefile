PYTHON = python3
VENV_PATH = .venv
VENV_PYTHON = ${VENV_PATH}/bin/python3
DEV_TOOLS_PATH = ./dist/DevTools.app

.PHONY: app
app: fmt
	@rm -rf dist build
	@pyinstaller DevTools.spec
	@open $(DEV_TOOLS_PATH)


fmt:
	${VENV_PYTHON} -m isort ./app
	${VENV_PYTHON} -m black ./app
