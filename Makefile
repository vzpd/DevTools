PYTHON ?= .venv/bin/python

.PHONY: run fmt check app

run:
	$(PYTHON) main.py

fmt:
	$(PYTHON) -m isort main.py app
	$(PYTHON) -m black main.py app

check:
	$(PYTHON) -m isort --check-only main.py app
	$(PYTHON) -m black --check main.py app
	$(PYTHON) -m compileall -q main.py app

app: check
	$(PYTHON) -m PyInstaller --noconfirm DevTools.spec
