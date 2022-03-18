venv = venv
bin = ${venv}/bin/
pysources = src example/server tests

build:
	${bin}python setup.py sdist bdist_wheel
	${bin}twine check dist/*
	rm -r build

check:
	${bin}black --check --diff --target-version=py37 ${pysources}
	${bin}flake8 ${pysources}
	${bin}mypy ${pysources}
	${bin}isort --check --diff ${pysources}

install:
	python3 -m venv ${venv}
	${bin}pip install -U pip wheel
	${bin}pip install -r requirements.txt

format:
	${bin}autoflake --in-place --recursive ${pysources}
	${bin}isort ${pysources}
	${bin}black --target-version=py37 ${pysources}

publish:
	${bin}twine upload dist/*

serve:
	${bin}uvicorn example.server:app

test:
	${bin}pytest
