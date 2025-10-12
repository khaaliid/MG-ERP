#!/bin/bash

# MG-ERP Test Runner Script for Linux/macOS
# Author: MG-ERP Development Team
# Description: Comprehensive test execution script with multiple options

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "MG-ERP Test Runner"
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -a, --all           Run all tests (default)"
    echo "  -e, --endpoints     Run only API endpoint tests"
    echo "  -b, --business      Run only business logic tests"
    echo "  -i, --integration   Run only integration tests"
    echo "  -c, --coverage      Run tests with coverage report"
    echo "  -v, --verbose       Run tests in verbose mode"
    echo "  -f, --fast          Run tests in parallel (faster)"
    echo "  --continue-on-failure Continue running tests after first failure (default: stop on first failure)"
    echo "  -s, --specific      Run specific test (requires test name)"
    echo ""
    echo "Examples:"
    echo "  $0                  # Run all tests (stop on first failure)"
    echo "  $0 -c               # Run all tests with coverage"
    echo "  $0 -e -v            # Run endpoint tests verbosely"
    echo "  $0 -f -c            # Run all tests fast with coverage"
    echo "  $0 --continue-on-failure  # Run all tests without stopping on failures"
    echo "  $0 -s test_health   # Run specific test"
}

# Default values
TEST_TYPE="all"
VERBOSE=false
COVERAGE=false
FAST=false
CONTINUE_ON_FAILURE=false
SPECIFIC_TEST=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -a|--all)
            TEST_TYPE="all"
            shift
            ;;
        -e|--endpoints)
            TEST_TYPE="endpoints"
            shift
            ;;
        -b|--business)
            TEST_TYPE="business"
            shift
            ;;
        -i|--integration)
            TEST_TYPE="integration"
            shift
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -f|--fast)
            FAST=true
            shift
            ;;
        --continue-on-failure)
            CONTINUE_ON_FAILURE=true
            shift
            ;;
        -s|--specific)
            if [[ -n "$2" && "$2" != -* ]]; then
                SPECIFIC_TEST="$2"
                shift 2
            else
                print_error "Specific test name required after -s/--specific"
                exit 1
            fi
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Check if we're in the right directory
if [[ ! -f "requirements.txt" ]] || [[ ! -d "tests" ]]; then
    print_error "Please run this script from the backend directory containing requirements.txt and tests/"
    exit 1
fi

# Set Python path to current directory so tests can import 'app' module
export PYTHONPATH="$(pwd):$PYTHONPATH"
print_status "PYTHONPATH set to: $PYTHONPATH"

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    print_error "pytest is not installed. Please install it first:"
    echo "pip install pytest pytest-asyncio httpx pytest-cov"
    exit 1
fi

print_status "Starting MG-ERP Test Suite..."
print_status "Test Type: $TEST_TYPE"
print_status "Verbose: $VERBOSE"
print_status "Coverage: $COVERAGE"
print_status "Fast Mode: $FAST"
print_status "Stop on First Failure: $(if [[ "$CONTINUE_ON_FAILURE" == true ]]; then echo "No"; else echo "Yes"; fi)"

# Build pytest command
PYTEST_CMD="pytest"

# Add test files based on type
case $TEST_TYPE in
    "endpoints")
        PYTEST_CMD="$PYTEST_CMD tests/test_api_endpoints.py"
        ;;
    "business")
        PYTEST_CMD="$PYTEST_CMD tests/test_business_logic.py"
        ;;
    "integration")
        PYTEST_CMD="$PYTEST_CMD tests/test_integration.py"
        ;;
    "all")
        PYTEST_CMD="$PYTEST_CMD tests/"
        ;;
esac

# Add specific test if provided
if [[ -n "$SPECIFIC_TEST" ]]; then
    PYTEST_CMD="$PYTEST_CMD -k $SPECIFIC_TEST"
fi

# Add verbose flag
if [[ "$VERBOSE" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# Add stop on first failure (default behavior unless continue-on-failure is specified)
if [[ "$CONTINUE_ON_FAILURE" != true ]]; then
    PYTEST_CMD="$PYTEST_CMD -x"  # Stop after first failure
fi

# Add coverage
if [[ "$COVERAGE" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD --cov=app --cov-report=html --cov-report=term"
fi

# Add parallel execution
if [[ "$FAST" == true ]]; then
    # Check if pytest-xdist is available
    if python -c "import xdist" 2>/dev/null; then
        PYTEST_CMD="$PYTEST_CMD -n auto"
    else
        print_warning "pytest-xdist not installed, running tests sequentially"
        print_warning "Install with: pip install pytest-xdist"
    fi
fi

# Add asyncio mode
PYTEST_CMD="$PYTEST_CMD --asyncio-mode=auto"

print_status "Executing: $PYTEST_CMD"
echo ""

# Run the tests
start_time=$(date +%s)

if eval $PYTEST_CMD; then
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    print_success "All tests completed successfully in ${duration}s!"
    
    if [[ "$COVERAGE" == true ]]; then
        print_status "Coverage report generated in htmlcov/index.html"
    fi
    
    echo ""
    print_status "Test Summary:"
    echo "  - Test Type: $TEST_TYPE"
    echo "  - Duration: ${duration}s"
    echo "  - Coverage: $([ "$COVERAGE" == true ] && echo "Yes" || echo "No")"
    echo "  - Mode: $([ "$FAST" == true ] && echo "Parallel" || echo "Sequential")"
else
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    print_error "Tests failed after ${duration}s"
    exit 1
fi