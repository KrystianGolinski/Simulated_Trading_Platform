#!/bin/bash

# Test Database Isolation and Cleanup Script
# Ensures clean test environments for reproducible integration testing

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

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

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_DB_PATH="$SCRIPT_DIR/test_database.db"
BACKUP_DB_PATH="$SCRIPT_DIR/test_database_backup.db"
MAIN_DB_PATH="$PROJECT_ROOT/Backend/api/trading_data.db"

# Function to create isolated test database
create_test_database() {
    print_status "Creating isolated test database..."
    
    # Remove existing test database
    if [ -f "$TEST_DB_PATH" ]; then
        rm "$TEST_DB_PATH"
        print_status "Removed existing test database"
    fi
    
    # Create new test database using seeding script
    python3 "$SCRIPT_DIR/db_seed.py" --db-path "$TEST_DB_PATH"
    
    if [ -f "$TEST_DB_PATH" ]; then
        print_success "Test database created at: $TEST_DB_PATH"
        return 0
    else
        print_error "Failed to create test database"
        return 1
    fi
}

# Function to backup production database
backup_production_database() {
    if [ -f "$MAIN_DB_PATH" ]; then
        print_status "Backing up production database..."
        cp "$MAIN_DB_PATH" "$BACKUP_DB_PATH"
        print_success "Production database backed up to: $BACKUP_DB_PATH"
        return 0
    else
        print_warning "No production database found at: $MAIN_DB_PATH"
        return 1
    fi
}

# Function to restore production database
restore_production_database() {
    if [ -f "$BACKUP_DB_PATH" ]; then
        print_status "Restoring production database..."
        cp "$BACKUP_DB_PATH" "$MAIN_DB_PATH"
        print_success "Production database restored from backup"
        return 0
    else
        print_warning "No backup database found to restore"
        return 1
    fi
}

# Function to switch to test database
switch_to_test_database() {
    print_status "Switching to test database environment..."
    
    # Backup production database first
    backup_production_database
    
    # Copy test database to production location
    if [ -f "$TEST_DB_PATH" ]; then
        cp "$TEST_DB_PATH" "$MAIN_DB_PATH"
        print_success "Switched to test database environment"
        return 0
    else
        print_error "Test database not found. Run create-test-db first."
        return 1
    fi
}

# Function to cleanup test environment
cleanup_test_environment() {
    print_status "Cleaning up test environment..."
    
    # Remove test database
    if [ -f "$TEST_DB_PATH" ]; then
        rm "$TEST_DB_PATH"
        print_status "Removed test database"
    fi
    
    # Restore production database if backup exists
    restore_production_database
    
    # Remove backup
    if [ -f "$BACKUP_DB_PATH" ]; then
        rm "$BACKUP_DB_PATH"
        print_status "Removed database backup"
    fi
    
    print_success "Test environment cleanup completed"
}

# Function to verify database isolation
verify_database_isolation() {
    print_status "Verifying database isolation..."
    
    local issues_found=0
    
    # Check if test database exists
    if [ ! -f "$TEST_DB_PATH" ]; then
        print_warning "Test database not found"
        issues_found=$((issues_found + 1))
    else
        print_success "Test database exists"
    fi
    
    # Check if production database is backed up
    if [ ! -f "$BACKUP_DB_PATH" ] && [ -f "$MAIN_DB_PATH" ]; then
        print_warning "Production database not backed up"
        issues_found=$((issues_found + 1))
    else
        print_success "Production database backup verified"
    fi
    
    # Verify test database content using Python
    if [ -f "$TEST_DB_PATH" ]; then
        python3 "$SCRIPT_DIR/db_seed.py" --db-path "$TEST_DB_PATH" --verify-only > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            print_success "Test database content verified"
        else
            print_error "Test database content verification failed"
            issues_found=$((issues_found + 1))
        fi
    fi
    
    if [ $issues_found -eq 0 ]; then
        print_success "Database isolation verification passed"
        return 0
    else
        print_error "Database isolation verification failed ($issues_found issues)"
        return 1
    fi
}

# Function to run isolated integration tests
run_isolated_tests() {
    print_status "Running integration tests in isolated environment..."
    
    # Create and switch to test environment
    create_test_database
    switch_to_test_database
    
    # Run integration tests
    local test_results=0
    
    print_status "Running enhanced integration tests..."
    
    # Run main integration test script
    if [ -f "$PROJECT_ROOT/test_integration.sh" ]; then
        cd "$PROJECT_ROOT"
        bash test_integration.sh
        test_results=$?
    else
        print_warning "Main integration test script not found"
        test_results=1
    fi
    
    # Cleanup regardless of test results
    cleanup_test_environment
    
    if [ $test_results -eq 0 ]; then
        print_success "Isolated integration tests completed successfully"
    else
        print_error "Isolated integration tests failed"
    fi
    
    return $test_results
}

# Function to display usage information
show_usage() {
    cat << EOF
Usage: $0 [COMMAND]

Test Database Isolation and Cleanup Commands:

  create-test-db      Create isolated test database with seeded data
  backup-prod-db      Backup production database
  restore-prod-db     Restore production database from backup
  switch-to-test      Switch to test database environment
  cleanup             Clean up test environment and restore production
  verify              Verify database isolation setup
  run-isolated        Run complete isolated integration test cycle
  help                Show this help message

Examples:
  $0 create-test-db   # Create new test database
  $0 run-isolated     # Full isolated test cycle
  $0 cleanup          # Clean up after tests

Database Paths:
  Test DB:        $TEST_DB_PATH
  Production DB:  $MAIN_DB_PATH
  Backup DB:      $BACKUP_DB_PATH

EOF
}

# Main command processing
case "${1:-help}" in
    "create-test-db")
        create_test_database
        ;;
    "backup-prod-db")
        backup_production_database
        ;;
    "restore-prod-db")
        restore_production_database
        ;;
    "switch-to-test")
        switch_to_test_database
        ;;
    "cleanup")
        cleanup_test_environment
        ;;
    "verify")
        verify_database_isolation
        ;;
    "run-isolated")
        run_isolated_tests
        ;;
    "help"|*)
        show_usage
        ;;
esac

exit $?