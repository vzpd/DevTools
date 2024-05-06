PYTHON = python3
VENV_PATH = .venv
VENV_PYTHON = ${VENV_PATH}/bin/python3
DEV_TOOLS_PATH = ./dist/DevTools.app

init: pyproject.toml
	@${PYTHON} -m virtualenv ${VENV_PATH}
	@${VENV_PYTHON}/python3 -m pip install poetry
	@${VENV_PYTHON}/python3 -m poetry env use ${VENV_PATH}/bin/python3
	@${VENV_PYTHON}/python3 -m poetry lock
	@${VENV_PYTHON}/python3 -m poetry install

install:
	$(VENV_PYTHON)/pip install charset-normalizer==2.1.1
	$(VENV_PYTHON)/pip install poetry==1.2.2
	$(VENV_PYTHON)/poetry config virtualenvs.path $(VENV_PATH)
	$(VENV_PYTHON)/poetry config virtualenvs.create false
	$(VENV_PYTHON)/poetry config --list
	$(VENV_PYTHON)/poetry config experimental.new-installer false
	$(VENV_PYTHON)/poetry show
	$(VENV_PYTHON)/poetry install


create-app:
	@rm -rf dist build
	@pyinstaller -n DevTools -w --clean main.py
	@open $(DEV_TOOLS_PATH)


fmt:
	${VENV_PYTHON} -m isort ./app
	${VENV_PYTHON} -m black ./app


check:
	${VENV_PYTHON} -m mypy ./app
	${VENV_PYTHON} -m isort ./app
	${VENV_PYTHON} -m black ./app
	${VENV_PYTHON} -m flake8 ./app

test:
	${VENV_PYTHON} -m pytest --cov-config=.coveragerc --cov

coverage:
	${VENV_PYTHON} -m coverage xml


test-report:
	${VENV_PYTHON} -m pytest --cov-config=.coveragerc --cov-report=html --cov
ifeq ($(OS),Windows_NT)
    ifeq ($(open),true)
        ifeq ($(COMSPEC),)
			cmd.exe /c start .cov_report/index.html
        else
			start .cov_report/index.html
        endif
    endif
endif
