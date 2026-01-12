.PHONY: help install install-dev test test-cov lint format clean build docs

help:
	@echo "PWA-CLI Development Commands"
	@echo "============================"
	@echo "install        - Install package in production mode"
	@echo "install-dev    - Install package with development dependencies"
	@echo "test           - Run tests"
	@echo "test-cov       - Run tests with coverage report"
	@echo "lint           - Run linters (flake8, mypy)"
	@echo "format         - Format code with black and isort"
	@echo "format-check   - Check code formatting without modifying"
	@echo "clean          - Remove build artifacts and cache files"
	@echo "build          - Build distribution packages"
	@echo "docs           - Generate documentation"
	@echo "run            - Run PWA CLI"

install:
	pip install -e .

install-dev:
	pip install -e .[dev]

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=pwa --cov-report=term-missing --cov-report=html

lint:
	@echo "Running flake8..."
	flake8 pwa/ tests/ --max-line-length=100 --extend-ignore=E203,W503
	@echo "Running mypy..."
	mypy pwa/ --ignore-missing-imports

format:
	@echo "Running isort..."
	isort pwa/ tests/
	@echo "Running black..."
	black pwa/ tests/ --line-length=100

format-check:
	@echo "Checking isort..."
	isort --check-only pwa/ tests/
	@echo "Checking black..."
	black --check pwa/ tests/ --line-length=100

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .tox/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

build: clean
	python -m build

docs:
	@echo "Documentation generation not yet configured"
	@echo "TODO: Set up Sphinx documentation"

run:
	python -m pwa
