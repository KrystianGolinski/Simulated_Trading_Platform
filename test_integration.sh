#!/bin/bash

echo "Integration Test"

cd "$(dirname "$0")"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

# Test 1: C++ Engine Build
print_test "Testing C++ engine build..."
if [ -f "Backend/cpp-engine/build/trading_engine" ]; then
    print_pass "C++ executable exists"
else
    print_fail "C++ executable not found"
    exit 1
fi

# Test 2: C++ Unit Tests
print_test "Running C++ unit tests..."
cd Backend/cpp-engine
if ./build/test_basic > /dev/null 2>&1; then
    print_pass "All C++ unit tests pass"
else
    print_fail "C++ unit tests failed"
    exit 1
fi

# Test 3: JSON Output Format
print_test "Testing JSON output format..."
json_output=$(./build/trading_engine --simulate 2>/dev/null | tail -n +2)
if echo "$json_output" | python3 -m json.tool > /dev/null 2>&1; then
    print_pass "JSON output is valid"
else
    print_fail "JSON output is invalid"
    echo "Output was: $json_output"
    exit 1
fi

# Test 4: Required JSON Fields
print_test "Checking required JSON fields..."
required_fields=("simulation_id" "starting_capital" "final_portfolio_value" "total_return_percentage" "equity_curve" "config")
missing_fields=()

for field in "${required_fields[@]}"; do
    if ! echo "$json_output" | grep -q "\"$field\""; then
        missing_fields+=("$field")
    fi
done

if [ ${#missing_fields[@]} -eq 0 ]; then
    print_pass "All required JSON fields present"
else
    print_fail "Missing JSON fields: ${missing_fields[*]}"
    exit 1
fi

# Test 5: Frontend Dependencies
cd ../../Frontend/trading-platform-ui
print_test "Checking frontend dependencies..."
if [ -d "node_modules" ] && [ -f "package.json" ]; then
    print_pass "Frontend dependencies installed"
else
    print_fail "Frontend dependencies missing"
    exit 1
fi

# Test 6: Frontend Build (quick check)
print_test "Testing frontend TypeScript compilation..."
if npm run build > /dev/null 2>&1; then
    print_pass "Frontend builds successfully"
else
    print_fail "Frontend build failed"
    exit 1
fi

cd ../..

echo ""
echo "All Integration Tests Passed!"
echo ""
echo "C++ core classes implemented and tested"
echo "Frontend optimized and building"
echo "JSON integration working"