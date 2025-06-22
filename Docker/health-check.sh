#!/bin/bash

# Comprehensive health check script for the trading platform
# Usage: ./health-check.sh [--verbose] [--json]

set -e

# Colours for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # None

# Configuration
VERBOSE=false
JSON_OUTPUT=false
TIMEOUT=10

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--verbose] [--json] [--timeout SECONDS]"
            exit 1
            ;;
    esac
done

# Initialize results
OVERALL_STATUS="healthy"
ISSUES=()
SERVICES_HEALTH=""
DOCKER_HEALTH=""

log() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    if [[ "$JSON_OUTPUT" != "true" ]]; then
        case $level in
            "INFO")
                echo -e "${BLUE}[INFO]${NC} $message"
                ;;
            "SUCCESS")
                echo -e "${GREEN}[SUCCESS]${NC} $message"
                ;;
            "WARNING")
                echo -e "${YELLOW}[WARNING]${NC} $message"
                ;;
            "ERROR")
                echo -e "${RED}[ERROR]${NC} $message"
                ;;
        esac
        
        if [[ "$VERBOSE" == "true" ]]; then
            echo "  [$timestamp] $message" >> /tmp/health-check.log
        fi
    fi
}

check_service() {
    local service_name=$1
    local url=$2
    local expected_status=${3:-200}
    
    log "INFO" "Checking $service_name health..."
    
    if command -v curl >/dev/null 2>&1; then
        local start_time=$(date +%s.%N)
        local response=$(curl -s -w "HTTPSTATUS:%{http_code};TIME:%{time_total}" --max-time $TIMEOUT "$url" 2>/dev/null || echo "HTTPSTATUS:000;TIME:0")
        local end_time=$(date +%s.%N)
        
        local http_status=$(echo "$response" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
        local response_time=$(echo "$response" | grep -o "TIME:[0-9.]*" | cut -d: -f2)
        local body=$(echo "$response" | sed -E 's/HTTPSTATUS:[0-9]*;TIME:[0-9.]*$//')
        
        if [[ "$http_status" == "$expected_status" ]]; then
            log "SUCCESS" "$service_name is healthy (${response_time}s response time)"
            SERVICES_HEALTH="$SERVICES_HEALTH\"$service_name\": {\"status\": \"healthy\", \"response_time\": \"${response_time}s\", \"http_status\": $http_status},"
        else
            log "ERROR" "$service_name is unhealthy (HTTP $http_status)"
            OVERALL_STATUS="unhealthy"
            ISSUES+=("$service_name: HTTP $http_status")
            SERVICES_HEALTH="$SERVICES_HEALTH\"$service_name\": {\"status\": \"unhealthy\", \"http_status\": $http_status, \"error\": \"HTTP $http_status\"},"
        fi
    else
        log "WARNING" "curl not available, skipping $service_name check"
        SERVICES_HEALTH="$SERVICES_HEALTH\"$service_name\": {\"status\": \"unknown\", \"error\": \"curl not available\"},"
    fi
}

check_docker_containers() {
    log "INFO" "Checking Docker container health..."
    
    if command -v docker >/dev/null 2>&1; then
        local containers=$(docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "")
        
        if [[ -n "$containers" ]]; then
            local healthy_count=0
            local total_count=0
            
            while IFS=$'\t' read -r name status ports; do
                if [[ "$name" != "NAMES" ]]; then
                    ((total_count++))
                    if [[ "$status" == *"healthy"* ]] || [[ "$status" == *"Up"* ]]; then
                        ((healthy_count++))
                        log "SUCCESS" "Container $name is running"
                    else
                        log "WARNING" "Container $name status: $status"
                        if [[ "$OVERALL_STATUS" == "healthy" ]]; then
                            OVERALL_STATUS="degraded"
                        fi
                        ISSUES+=("Container $name: $status")
                    fi
                fi
            done <<< "$containers"
            
            DOCKER_HEALTH="\"docker\": {\"status\": \"healthy\", \"containers_running\": $healthy_count, \"total_containers\": $total_count},"
            log "INFO" "Docker containers: $healthy_count/$total_count running"
        else
            log "WARNING" "No Docker containers found or Docker not accessible"
            DOCKER_HEALTH="\"docker\": {\"status\": \"warning\", \"error\": \"No containers found\"},"
        fi
    else
        log "WARNING" "Docker not available"
        DOCKER_HEALTH="\"docker\": {\"status\": \"unknown\", \"error\": \"Docker not available\"},"
    fi
}

check_disk_space() {
    log "INFO" "Checking disk space..."
    
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [[ $disk_usage -gt 90 ]]; then
        log "ERROR" "Disk usage is critical: ${disk_usage}%"
        OVERALL_STATUS="unhealthy"
        ISSUES+=("Disk usage: ${disk_usage}%")
    elif [[ $disk_usage -gt 80 ]]; then
        log "WARNING" "Disk usage is high: ${disk_usage}%"
        if [[ "$OVERALL_STATUS" == "healthy" ]]; then
            OVERALL_STATUS="degraded"
        fi
        ISSUES+=("High disk usage: ${disk_usage}%")
    else
        log "SUCCESS" "Disk usage is normal: ${disk_usage}%"
    fi
}

check_memory() {
    log "INFO" "Checking memory usage..."
    
    if command -v free >/dev/null 2>&1; then
        local memory_usage=$(free | awk 'NR==2{printf "%.1f", $3*100/$2 }')
        local memory_usage_int=${memory_usage%.*}
        
        if [[ $memory_usage_int -gt 90 ]]; then
            log "ERROR" "Memory usage is critical: ${memory_usage}%"
            OVERALL_STATUS="unhealthy"
            ISSUES+=("Memory usage: ${memory_usage}%")
        elif [[ $memory_usage_int -gt 80 ]]; then
            log "WARNING" "Memory usage is high: ${memory_usage}%"
            if [[ "$OVERALL_STATUS" == "healthy" ]]; then
                OVERALL_STATUS="degraded"
            fi
        else
            log "SUCCESS" "Memory usage is normal: ${memory_usage}%"
        fi
    else
        log "WARNING" "free command not available, skipping memory check"
    fi
}

main() {
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    
    if [[ "$JSON_OUTPUT" != "true" ]]; then
        echo "Trading Platform Health Check"
        echo "Started at: $timestamp"
    fi
    
    # Check services
    check_service "trading-api" "http://localhost:8000/health" 200
    check_service "trading-ui" "http://localhost:3000" 200
    
    # Check Docker containers
    check_docker_containers
    
    # Check system resources
    check_disk_space
    check_memory
    
    # Generate output
    if [[ "$JSON_OUTPUT" == "true" ]]; then
        # Remove trailing commas
        SERVICES_HEALTH=${SERVICES_HEALTH%,}
        DOCKER_HEALTH=${DOCKER_HEALTH%,}
        
        # Build issues array
        local issues_json=""
        for issue in "${ISSUES[@]}"; do
            issues_json="$issues_json\"$issue\","
        done
        issues_json=${issues_json%,}
        
        echo "{"
        echo "  \"timestamp\": \"$timestamp\","
        echo "  \"overall_status\": \"$OVERALL_STATUS\","
        echo "  \"services\": {$SERVICES_HEALTH},"
        echo "  $DOCKER_HEALTH"
        echo "  \"issues\": [$issues_json]"
        echo "}"
    else
        echo "Health Check Summary"
        echo "Overall Status: $OVERALL_STATUS"
        echo "Timestamp: $timestamp"
        
        if [[ ${#ISSUES[@]} -gt 0 ]]; then
            echo ""
            echo "Issues Found:"
            for issue in "${ISSUES[@]}"; do
                echo "  - $issue"
            done
        fi
        
        
        case $OVERALL_STATUS in
            "healthy")
                log "SUCCESS" "All systems are healthy!"
                ;;
            "degraded")
                log "WARNING" "Some systems have issues but are still functional"
                ;;
            "unhealthy")
                log "ERROR" "Critical issues detected!"
                ;;
        esac
    fi
    
    # Exit with appropriate code
    case $OVERALL_STATUS in
        "healthy")
            exit 0
            ;;
        "degraded")
            exit 1
            ;;
        "unhealthy")
            exit 2
            ;;
    esac
}

# Run main function
main "$@"