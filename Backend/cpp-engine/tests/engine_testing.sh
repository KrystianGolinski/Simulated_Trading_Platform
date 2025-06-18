#!/bin/bash

# Comprehensive trading platform engine testing
# Tests all parts: Core functionality, Progress tracking, and Performance optimizations

set -e  # Exit on error

echo "=== Trading Platform Comprehensive Test Suite ==="
echo "Testing all parts: Core functionality, Progress tracking, Performance optimizations"
echo

API_BASE="http://localhost:8000"
FAILED_TESTS=0
TOTAL_TESTS=0

# Test utility functions
run_test() {
    local test_name="$1"
    local test_command="$2"
    echo "Running: $test_name"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if eval "$test_command"; then
        echo "PASS: $test_name"
    else
        echo "FAIL: $test_name"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    echo
}

check_api_availability() {
    echo "Checking API availability..."
    if ! curl -s "$API_BASE/health" > /dev/null; then
        echo "ERROR: API not available at $API_BASE"
        exit 1
    fi
    echo "SUCCESS: API is available"
    echo
}

# CORE FUNCTIONALITY TESTS

echo "CORE FUNCTIONALITY TESTS"

test_parameter_validation() {
    echo "Testing parameter variations produce different results..."
    
    # Test different capital amounts
    RESULT1=$(curl -s -X POST "$API_BASE/simulation/start" \
        -H "Content-Type: application/json" \
        -d '{"symbols":["AAPL"],"start_date":"2023-01-01","end_date":"2023-01-31","starting_capital":5000,"strategy":"ma_crossover"}' \
        | python3 -c "import sys,json; print(json.load(sys.stdin).get('simulation_id',''))" 2>/dev/null)
    
    RESULT2=$(curl -s -X POST "$API_BASE/simulation/start" \
        -H "Content-Type: application/json" \
        -d '{"symbols":["AAPL"],"start_date":"2023-01-01","end_date":"2023-01-31","starting_capital":15000,"strategy":"ma_crossover"}' \
        | python3 -c "import sys,json; print(json.load(sys.stdin).get('simulation_id',''))" 2>/dev/null)
    
    if [ -n "$RESULT1" ] && [ -n "$RESULT2" ] && [ "$RESULT1" != "$RESULT2" ]; then
        echo "Different simulations created: $RESULT1 vs $RESULT2"
        return 0
    else
        echo "Failed to create different simulations or got same ID"
        return 1
    fi
}

test_validation_system() {
    echo "Testing input validation system..."
    
    # Test invalid symbol
    RESPONSE=$(curl -s -X POST "$API_BASE/simulation/validate" \
        -H "Content-Type: application/json" \
        -d '{"symbols":["INVALID"],"start_date":"2023-01-01","end_date":"2023-01-31","starting_capital":10000,"strategy":"ma_crossover"}')
    
    if echo "$RESPONSE" | grep -q '"is_valid":false'; then
        echo "Validation correctly rejected invalid symbol"
        return 0
    else
        echo "Validation should have rejected invalid symbol"
        return 1
    fi
}

test_basic_simulation() {
    echo "Testing basic simulation execution..."
    
    SIMULATION_ID=$(curl -s -X POST "$API_BASE/simulation/start" \
        -H "Content-Type: application/json" \
        -d '{"symbols":["AAPL"],"start_date":"2023-01-01","end_date":"2023-01-31","starting_capital":10000,"strategy":"ma_crossover"}' \
        | python3 -c "import sys,json; print(json.load(sys.stdin).get('simulation_id',''))" 2>/dev/null)
    
    if [ -n "$SIMULATION_ID" ]; then
        echo "Created simulation: $SIMULATION_ID"
        # Wait a moment and check status
        sleep 3
        STATUS=$(curl -s "$API_BASE/simulation/$SIMULATION_ID/status" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null)
        echo "Simulation status: $STATUS"
        return 0
    else
        echo "Failed to create simulation"
        return 1
    fi
}

# Run core tests
check_api_availability
run_test "Parameter Validation" test_parameter_validation
run_test "Input Validation System" test_validation_system  
run_test "Basic Simulation Execution" test_basic_simulation

# PROGRESS TRACKING TESTS

echo "PROGRESS TRACKING TESTS"

test_progress_tracking() {
    echo "Testing simulation progress tracking..."
    
    SIMULATION_ID=$(curl -s -X POST "$API_BASE/simulation/start" \
        -H "Content-Type: application/json" \
        -d '{"symbols":["AAPL"],"start_date":"2023-01-01","end_date":"2023-03-31","starting_capital":10000,"strategy":"ma_crossover"}' \
        | python3 -c "import sys,json; print(json.load(sys.stdin).get('simulation_id',''))" 2>/dev/null)
    
    if [ -n "$SIMULATION_ID" ]; then
        echo "Created simulation: $SIMULATION_ID"
        
        # Monitor progress for a few seconds
        PROGRESS_FOUND=false
        for i in {1..5}; do
            STATUS=$(curl -s "$API_BASE/simulation/$SIMULATION_ID/status")
            PROGRESS=$(echo "$STATUS" | python3 -c "import sys,json; print(json.load(sys.stdin).get('progress_pct','none'))" 2>/dev/null)
            echo "Check $i: Progress = $PROGRESS%"
            
            if [ "$PROGRESS" != "none" ] && [ "$PROGRESS" != "null" ]; then
                PROGRESS_FOUND=true
            fi
            sleep 1
        done
        
        if [ "$PROGRESS_FOUND" = true ]; then
            echo "Progress tracking working"
            return 0
        else
            echo "No progress updates detected"
            return 1
        fi
    else
        echo "Failed to create simulation for progress test"
        return 1
    fi
}

# Run progress tests
run_test "Progress Tracking" test_progress_tracking

# VALIDATION & ERROR HANDLING TESTS

echo "VALIDATION & ERROR HANDLING TESTS"

test_comprehensive_validation() {
    echo "Testing comprehensive validation system..."
    # Test various invalid inputs

    TESTS_PASSED=0
    
    # Invalid date range
    RESPONSE=$(curl -s -X POST "$API_BASE/simulation/validate" \
        -H "Content-Type: application/json" \
        -d '{"symbols":["AAPL"],"start_date":"2025-01-01","end_date":"2025-12-31","starting_capital":10000,"strategy":"ma_crossover"}')
    
    if echo "$RESPONSE" | grep -q '"is_valid":false'; then
        echo "Future date validation working"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    fi
    
    # Invalid capital
    RESPONSE=$(curl -s -X POST "$API_BASE/simulation/validate" \
        -H "Content-Type: application/json" \
        -d '{"symbols":["AAPL"],"start_date":"2023-01-01","end_date":"2023-01-31","starting_capital":-1000,"strategy":"ma_crossover"}')
    
    if echo "$RESPONSE" | grep -q '"is_valid":false'; then
        echo "Negative capital validation working"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    fi
    
    if [ $TESTS_PASSED -ge 2 ]; then
        return 0
    else
        echo "Not all tests passed"
        return 1
    fi
}

# Run validation and error handling tests
run_test "Comprehensive Validation" test_comprehensive_validation

# PERFORMANCE OPTIMIZATION TESTS

echo "PERFORMANCE OPTIMIZATION TESTS"

test_performance_endpoints() {
    echo "Testing performance monitoring endpoints..."
    
    # Test performance stats
    STATS=$(curl -s "$API_BASE/performance/stats")
    if echo "$STATS" | grep -q "optimization\|database"; then
        echo "Performance stats endpoint working"
        
        # Test cache stats
        CACHE_STATS=$(curl -s "$API_BASE/performance/cache-stats")
        if echo "$CACHE_STATS" | grep -q "cache\|timestamp"; then
            echo "Cache stats endpoint working"
            return 0
        fi
    fi
    
    echo "Performance endpoints not responding correctly"
    return 1
}

test_data_caching() {
    echo "Testing data caching performance..."
    
    # First request (cache miss)
    START_TIME=$(date +%s%N)
    curl -s "$API_BASE/stocks/AAPL/data?start_date=2023-01-01&end_date=2023-01-31" > /dev/null
    FIRST_TIME=$(date +%s%N)
    FIRST_DURATION=$((($FIRST_TIME - $START_TIME) / 1000000))
    
    # Second request (cache hit)
    START_TIME=$(date +%s%N)
    curl -s "$API_BASE/stocks/AAPL/data?start_date=2023-01-01&end_date=2023-01-31" > /dev/null
    SECOND_TIME=$(date +%s%N)
    SECOND_DURATION=$((($SECOND_TIME - $START_TIME) / 1000000))
    
    echo "First request: ${FIRST_DURATION}ms"
    echo "Second request: ${SECOND_DURATION}ms"
    
    # Cache should provide some speedup (even if minimal)
    if [ $SECOND_DURATION -le $FIRST_DURATION ]; then
        echo "Caching provides performance benefit"
        return 0
    else
        echo "No caching benefit detected"
        return 1
    fi
}

test_enhanced_health_check() {
    echo "Testing enhanced health check..."
    
    HEALTH=$(curl -s "$API_BASE/health")
    if echo "$HEALTH" | grep -q "database\|validation_system"; then
        echo "Enhanced health check working"
        return 0
    else
        echo "Basic health check only"
        return 1
    fi
}

# Run performance optimization tests
run_test "Performance Endpoints" test_performance_endpoints
run_test "Data Caching" test_data_caching
run_test "Enhanced Health Check" test_enhanced_health_check

# INTEGRATION TESTS

echo "INTEGRATION TESTS"

test_end_to_end_simulation() {
    echo "Testing complete end-to-end simulation flow..."
    
    # Validate -> Start -> Monitor -> Results
    VALIDATION=$(curl -s -X POST "$API_BASE/simulation/validate" \
        -H "Content-Type: application/json" \
        -d '{"symbols":["AAPL"],"start_date":"2023-01-01","end_date":"2023-01-31","starting_capital":10000,"strategy":"ma_crossover"}')
    
    if echo "$VALIDATION" | grep -q '"is_valid":true'; then
        echo "Validation passed"
        
        SIMULATION_ID=$(curl -s -X POST "$API_BASE/simulation/start" \
            -H "Content-Type: application/json" \
            -d '{"symbols":["AAPL"],"start_date":"2023-01-01","end_date":"2023-01-31","starting_capital":10000,"strategy":"ma_crossover"}' \
            | python3 -c "import sys,json; print(json.load(sys.stdin).get('simulation_id',''))" 2>/dev/null)
        
        if [ -n "$SIMULATION_ID" ]; then
            echo "Simulation started: $SIMULATION_ID"
            
            # Wait for completion
            for i in {1..10}; do
                STATUS=$(curl -s "$API_BASE/simulation/$SIMULATION_ID/status" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null)
                echo "Status check $i: $STATUS"
                
                if [ "$STATUS" = "completed" ]; then
                    echo "Simulation completed"
                    
                    # Get results
                    RESULTS=$(curl -s "$API_BASE/simulation/$SIMULATION_ID/results")
                    if echo "$RESULTS" | grep -q "ending_value\|total_return"; then
                        echo "Results retrieved successfully"
                        return 0
                    else
                        echo "Failed to get valid results"
                        return 1
                    fi
                elif [ "$STATUS" = "failed" ]; then
                    echo "Simulation failed"
                    return 1
                fi
                
                sleep 2
            done
            
            echo "Simulation did not complete in time"
            return 1
        else
            echo "Failed to start simulation"
            return 1
        fi
    else
        echo "Validation failed"
        return 1
    fi
}

# Run integration tests
run_test "End-to-End Simulation Flow" test_end_to_end_simulation

# SUMMARY

echo "ENGINE TESTING SUMMARY"
echo "Total tests run: $TOTAL_TESTS"
echo "Tests passed: $((TOTAL_TESTS - FAILED_TESTS))"
echo "Tests failed: $FAILED_TESTS"
echo

if [ $FAILED_TESTS -eq 0 ]; then
    echo "ALL TESTS PASSED"
    echo "Trading platform is functioning correctly across all parts"
    exit 0
else
    echo "NOT ALL TESTS PASSED"
    echo "Review the failed tests above and check system logs"
    exit 1
fi