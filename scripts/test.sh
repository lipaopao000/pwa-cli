#!/bin/bash
# Test script for PWA CLI

set -e

echo "========================================="
echo "Running PWA CLI Test Suite"
echo "========================================="
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "Error: pytest is not installed"
    echo "Please install it with: pip install pytest pytest-cov"
    exit 1
fi

# Run tests with different options based on arguments
if [ "$1" == "coverage" ]; then
    echo "Running tests with coverage..."
    pytest --cov=pwa --cov-report=html --cov-report=term tests/
    echo ""
    echo "Coverage report generated in htmlcov/index.html"
elif [ "$1" == "verbose" ]; then
    echo "Running tests in verbose mode..."
    pytest -v tests/
elif [ "$1" == "quick" ]; then
    echo "Running quick tests (no integration)..."
    pytest -v -m "not integration" tests/
else
    echo "Running all tests..."
    pytest tests/
fi

echo ""
echo "========================================="
echo "Test suite completed!"
echo "========================================="
