# Makefile for PiTunnel project

.PHONY: install dev test lint build deploy clean

install:
	pip install -e .

dev: install
	pip install -e ".[dev]"

test:
	pytest tests/

lint:
	ruff check src/
	mypy src/

build:
	python -m build

deploy:
	# Add deployment logic here

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete