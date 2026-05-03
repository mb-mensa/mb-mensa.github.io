#!/bin/bash
set -e

if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
fi

pip install -q -r requirements_lint.txt

black --check .
isort --check .
flake8 .
mypy .
