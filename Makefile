lint:
	pylint *.py modules/*.py
	flake8 --exclude=./modules/__init__.py,modules/tests,.tox
	pydocstyle *
test: lint
	tox
