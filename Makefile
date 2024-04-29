create-app:
	@rm -rf dist build
	@pyinstaller -n DevTools -w --clean main.py