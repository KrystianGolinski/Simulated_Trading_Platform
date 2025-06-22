#!/bin/bash

# Comprehensive Test Runner for Simulated Trading Platform
# Testing automation: runs all test suites with reporting and metrics

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test result tracking
TOTAL_SUITES=0
PASSED_SUITES=0
FAILED_SUITES=0
START_TIME=$(date +%s)

# Test metrics
TOTAL_TESTS=0
TOTAL_PASSED=0
TOTAL_FAILED=0

echo "Simulated Trading Platform - Complete Test Suite Runner"
echo "Running all test suites with comprehensive reporting"
echo ""

print_header() {
    echo -e "${BLUE}[TEST SUITE]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

run_test_suite() {
    local suite_name="$1"
    local test_command="$2"
    local test_dir="$3"
    
    print_header "$suite_name"
    TOTAL_SUITES=$((TOTAL_SUITES + 1))
    
    local original_dir=$(pwd)
    
    if [ -n "$test_dir" ]; then
        cd "$test_dir" || {
            print_fail "Failed to change to directory: $test_dir"
            FAILED_SUITES=$((FAILED_SUITES + 1))
            return 1
        }
    fi
    
    # Run the test command and capture both output and exit code
    local output
    local exit_code
    output=$(eval "$test_command" 2>&1)
    exit_code=$?
    
    # Return to original directory
    cd "$original_dir"
    
    # Print some output for feedback
    echo "$output" | head -10
    if [ $(echo "$output" | wc -l) -gt 10 ]; then
        echo "... (truncated)"
    fi
    
    # Store output in a variable for metrics collection
    LAST_TEST_OUTPUT="$output"
    
    if [ $exit_code -eq 0 ]; then
        print_pass "$suite_name completed successfully"
        PASSED_SUITES=$((PASSED_SUITES + 1))
        return 0
    else
        print_fail "$suite_name failed (exit code: $exit_code)"
        FAILED_SUITES=$((FAILED_SUITES + 1))
        return 1
    fi
}

collect_test_metrics() {
    local output="$1"
    
    # Extract test counts from various test runners
    if echo "$output" | grep -q "test session starts"; then
        # pytest format
        local pytest_passed=$(echo "$output" | grep -o "[0-9]\+ passed" | grep -o "[0-9]\+" | head -1)
        local pytest_failed=$(echo "$output" | grep -o "[0-9]\+ failed" | grep -o "[0-9]\+" | head -1)
        TOTAL_PASSED=$((TOTAL_PASSED + ${pytest_passed:-0}))
        TOTAL_FAILED=$((TOTAL_FAILED + ${pytest_failed:-0}))
    elif echo "$output" | grep -q "Tests:.*passed"; then
        # Jest format
        local jest_passed=$(echo "$output" | grep -o "Tests:.*passed" | grep -o "[0-9]\+ passed" | grep -o "[0-9]\+")
        local jest_failed=$(echo "$output" | grep -o "[0-9]\+ failed" | grep -o "[0-9]\+")
        TOTAL_PASSED=$((TOTAL_PASSED + ${jest_passed:-0}))
        TOTAL_FAILED=$((TOTAL_FAILED + ${jest_failed:-0}))
    elif echo "$output" | grep -q "Tests passed:"; then
        # Custom format from engine_testing.sh
        local custom_passed=$(echo "$output" | grep "Tests passed:" | grep -o "[0-9]\+")
        local custom_failed=$(echo "$output" | grep "Tests failed:" | grep -o "[0-9]\+")
        TOTAL_PASSED=$((TOTAL_PASSED + ${custom_passed:-0}))
        TOTAL_FAILED=$((TOTAL_FAILED + ${custom_failed:-0}))
    fi
}

# C++ Engine Tests
print_info "Starting C++ engine test suite..."
if [ -f "Backend/cpp-engine/build/test_basic" ]; then
    run_test_suite "C++ Engine Unit Tests" "./build/test_basic" "Backend/cpp-engine"
    collect_test_metrics "$LAST_TEST_OUTPUT"
else
    print_info "C++ tests not built - checking if we can build..."
    if [ -f "Backend/cpp-engine/build.sh" ]; then
        print_info "Building C++ tests..."
        cd Backend/cpp-engine && ./build.sh && cd ../..
        if [ -f "Backend/cpp-engine/build/test_basic" ]; then
            run_test_suite "C++ Engine Unit Tests" "./build/test_basic" "Backend/cpp-engine"
            collect_test_metrics "$LAST_TEST_OUTPUT"
        else
            print_fail "C++ build failed - skipping C++ tests"
            FAILED_SUITES=$((FAILED_SUITES + 1))
            TOTAL_SUITES=$((TOTAL_SUITES + 1))
        fi
    else
        print_fail "C++ build script not found - skipping C++ tests"
        FAILED_SUITES=$((FAILED_SUITES + 1))
        TOTAL_SUITES=$((TOTAL_SUITES + 1))
    fi
fi

# Python Backend Tests
print_info "Starting Python backend test suite..."
if [ -d "Backend/api/tests" ]; then
    print_info "Checking Python dependencies..."
    if [ -f "Backend/api/requirements.txt" ] && [ -d "Backend/api/venv" ]; then
        print_info "Using virtual environment..."
        if [ -f "Backend/api/pytest.ini" ]; then
            run_test_suite "Python Backend Unit Tests" "source venv/bin/activate && python -m pytest tests/ -v --tb=short" "Backend/api"
            collect_test_metrics "$LAST_TEST_OUTPUT"
        else
            print_info "pytest.ini not found - attempting basic pytest run..."
            run_test_suite "Python Backend Unit Tests" "source venv/bin/activate && python -m pytest tests/ -v" "Backend/api"
            collect_test_metrics "$LAST_TEST_OUTPUT"
        fi
    else
        print_info "Virtual environment not found - trying system Python..."
        if command -v python3 >/dev/null 2>&1; then
            if [ -f "Backend/api/pytest.ini" ]; then
                run_test_suite "Python Backend Unit Tests" "python3 -m pytest tests/ -v --tb=short" "Backend/api"
                collect_test_metrics "$LAST_TEST_OUTPUT"
            else
                print_info "pytest.ini not found - attempting basic pytest run..."
                run_test_suite "Python Backend Unit Tests" "python3 -m pytest tests/ -v" "Backend/api"
                collect_test_metrics "$LAST_TEST_OUTPUT"
            fi
        else
            print_fail "Python3 not found - skipping Python tests"
            FAILED_SUITES=$((FAILED_SUITES + 1))
            TOTAL_SUITES=$((TOTAL_SUITES + 1))
        fi
    fi
else
    print_fail "Python tests directory not found - skipping Python tests"
    FAILED_SUITES=$((FAILED_SUITES + 1))
    TOTAL_SUITES=$((TOTAL_SUITES + 1))
fi

# Frontend Tests
print_info "Starting Frontend test suite..."
if [ -f "Frontend/trading-platform-ui/package.json" ]; then
    run_test_suite "Frontend Component Tests" "NODE_OPTIONS='' npm test -- --watchAll=false --coverage=false --passWithNoTests" "Frontend/trading-platform-ui"
    collect_test_metrics "$LAST_TEST_OUTPUT"
else
    print_fail "Frontend package.json not found - skipping Frontend tests"
    FAILED_SUITES=$((FAILED_SUITES + 1))
    TOTAL_SUITES=$((TOTAL_SUITES + 1))
fi

# Integration Tests
print_info "Starting integration test suite..."
if [ -f "test_integration.sh" ]; then
    run_test_suite "Integration Tests" "./test_integration.sh" "."
    collect_test_metrics "$LAST_TEST_OUTPUT"
else
    print_fail "Integration test script not found - skipping Integration tests"
    FAILED_SUITES=$((FAILED_SUITES + 1))
    TOTAL_SUITES=$((TOTAL_SUITES + 1))
fi

# API Engine Tests (only if API is running)
print_info "Checking if API is available for engine tests..."
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    print_info "API available - running comprehensive engine tests..."
    if [ -f "Backend/cpp-engine/tests/engine_testing.sh" ]; then
        chmod +x Backend/cpp-engine/tests/engine_testing.sh
        run_test_suite "API Engine Tests" "Backend/cpp-engine/tests/engine_testing.sh" "."
        collect_test_metrics "$LAST_TEST_OUTPUT"
    else
        print_info "Engine testing script not found - skipping API tests"
        TOTAL_SUITES=$((TOTAL_SUITES + 1))
    fi
else
    print_info "API not running - skipping engine API tests"
    print_info "To run API tests, start the development environment first"
    TOTAL_SUITES=$((TOTAL_SUITES + 1))
fi

# Calculate final metrics
END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))
TOTAL_TESTS=$((TOTAL_PASSED + TOTAL_FAILED))

# Generate report
echo ""
echo "TEST EXECUTION SUMMARY"
echo -e "Execution Time: ${YELLOW}${TOTAL_TIME}s${NC}"
echo -e "Test Suites Run: ${BLUE}${TOTAL_SUITES}${NC}"
echo -e "Suites Passed: ${GREEN}${PASSED_SUITES}${NC}"
echo -e "Suites Failed: ${RED}${FAILED_SUITES}${NC}"
echo ""
echo "DETAILED TEST METRICS"
echo -e "Individual Tests: ${BLUE}${TOTAL_TESTS}${NC}"
echo -e "Tests Passed: ${GREEN}${TOTAL_PASSED}${NC}"
echo -e "Tests Failed: ${RED}${TOTAL_FAILED}${NC}"

if [ $TOTAL_TESTS -gt 0 ]; then
    PASS_RATE=$(( (TOTAL_PASSED * 100) / TOTAL_TESTS ))
    echo -e "Pass Rate: ${YELLOW}${PASS_RATE}%${NC}"
fi

echo ""
echo "SUITE BREAKDOWN"
echo "C++ Engine Unit Tests"
echo "Python Backend Unit Tests"
echo "Frontend Component Tests"
echo "Integration Tests"
echo "API Engine Tests (if available)"

# Coverage and recommendations
echo ""
echo "RECOMMENDATIONS"

if [ $FAILED_SUITES -gt 0 ]; then
    echo -e "${RED}Some test suites failed - review output above${NC}"
fi

if [ $TOTAL_TESTS -lt 50 ]; then
    echo -e "${YELLOW}Test coverage appears low${NC}"
    echo "• Consider adding more testing"
fi

if [ $TOTAL_TIME -gt 180 ]; then
    echo -e "${YELLOW}Test execution took longer than 3 minutes${NC}"
fi

echo ""
echo "NEXT STEPS"

# Final status
echo ""
if [ $FAILED_SUITES -eq 0 ]; then
    echo -e "${GREEN}ALL TEST SUITES PASSED${NC}"
    echo "Trading platform is functioning correctly across all components"
    exit 0
else
    echo -e "${RED}$FAILED_SUITES/$TOTAL_SUITES TEST SUITES FAILED${NC}"
    echo "Review the failures above and fix issues before deployment"
    exit 1
fi