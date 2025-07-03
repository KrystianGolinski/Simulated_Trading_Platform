#!/usr/bin/env python3

# API Test Runner Script
# Similar to the C++ engine testing script
# Runs all API tests with detailed reporting and metrics

import sys
import os
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, Any, List
import argparse

# Add the API directory to Python path for imports
api_dir = Path(__file__).parent.parent
sys.path.insert(0, str(api_dir))

# Import our test suite
from tests.comprehensive_API_testing import ComprehensiveAPITestSuite

class APITestRunner:
    # Test runner for the API
    # Provides detailed test execution, reporting, and metrics collection
    
    def __init__(self, verbose: bool = False, include_integration: bool = True):
        self.verbose = verbose
        self.include_integration = include_integration
        self.test_results = {
            'total_execution_time': 0,
            'test_suites_run': 0,
            'individual_tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'coverage_report': {},
            'performance_metrics': {},
            'error_summary': []
        }
        
    def run_comprehensive_tests(self) -> bool:
        # Run the test suite and return success status
        if self.verbose:
            print("Running API test suite with detailed reporting:")
            print(f"Verbose mode: {'ON' if self.verbose else 'OFF'}")
            print(f"Integration tests: {'INCLUDED' if self.include_integration else 'EXCLUDED'}")
            print()
        
        start_time = time.time()
        
        try:
            # Initialize and run the test suite
            test_suite = ComprehensiveAPITestSuite()
            
            if self.verbose:
                print("Initializing test suite:")
            test_suite.run_all_tests()
            
            # Collect results from the test suite
            self.test_results.update({
                'total_execution_time': time.time() - start_time,
                'test_suites_run': 1,
                'individual_tests_run': test_suite.test_results['total_tests'],
                'tests_passed': test_suite.test_results['passed_tests'],
                'tests_failed': test_suite.test_results['failed_tests'],
                'error_summary': test_suite.test_results['failed_test_details']
            })
            
            success = test_suite.test_results['failed_tests'] == 0
            
        except Exception as e:
            print(f"CRITICAL ERROR: Failed to run test suite: {str(e)}")
            self.test_results['error_summary'].append({
                'category': 'Test Suite Execution',
                'error': str(e)
            })
            success = False
            
        self.test_results['total_execution_time'] = time.time() - start_time
        return success
    
    def run_pytest_tests(self) -> bool:
        # Run individual pytest tests for additional coverage
        if self.verbose:
            print("\nRunning Individual PyTest Tests")
        
        try:
            # Run pytest on the test file
            test_file = Path(__file__).parent / "comprehensive_API_testing.py"
            
            cmd = [
                sys.executable, "-m", "pytest", 
                str(test_file),
                "-v" if self.verbose else "-q",
                "--tb=short",
                "--disable-warnings"
            ]
            
            if self.verbose:
                print(f"Running command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(api_dir),
                timeout=300  # 5 minute timeout
            )
            
            if self.verbose:
                print("PyTest STDOUT:")
                print(result.stdout)
                if result.stderr:
                    print("PyTest STDERR:")
                    print(result.stderr)
            
            # Parse pytest output for test counts
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if 'passed' in line and 'failed' in line:
                    # Try to extract test counts from pytest summary
                    pass
            
            success = result.returncode == 0
            if self.verbose:
                print(f"PyTest execution: {'SUCCESS' if success else 'FAILED'}")
            
            if not success:
                self.test_results['error_summary'].append({
                    'category': 'PyTest Execution',
                    'error': f"Return code: {result.returncode}, stderr: {result.stderr}"
                })
            
            return success
            
        except subprocess.TimeoutExpired:
            print("ERROR: PyTest execution timed out after 5 minutes")
            self.test_results['error_summary'].append({
                'category': 'PyTest Execution',
                'error': 'Test execution timeout'
            })
            return False
        except Exception as e:
            print(f"ERROR: Failed to run PyTest tests: {str(e)}")
            self.test_results['error_summary'].append({
                'category': 'PyTest Execution', 
                'error': str(e)
            })
            return False
    
    
    def check_api_dependencies(self) -> bool:
        # Check that required API dependencies are available
        if self.verbose:
            print("\nChecking API Dependencies")
        
        required_modules = [
            'fastapi',
            'uvicorn', 
            'pydantic',
            'asyncpg',
            'pytest',
            'httpx'
        ]
        
        missing_modules = []
        
        for module in required_modules:
            try:
                __import__(module)
                if self.verbose:
                    print(f"  PASS {module}")
            except ImportError:
                missing_modules.append(module)
                if self.verbose:
                    print(f"  FAIL {module} - NOT FOUND")
        
        if missing_modules:
            if self.verbose:
                print(f"\nERROR: Missing required modules: {', '.join(missing_modules)}")
                print("Please install missing dependencies with:")
                print(f"pip install {' '.join(missing_modules)}")
            return False
        
        if self.verbose:
            print("All required dependencies are available")
        return True
    
    def check_api_structure(self) -> bool:
        # Check that the API structure is complete
        if self.verbose:
            print("\nChecking API Structure")
        
        required_files = [
            'main.py',
            'models.py',
            'database.py', 
            'validation.py',
            'routers/health.py',
            'routers/simulation.py',
            'routers/stocks.py',
            'services/execution_service.py',
            'services/result_processor.py',
            'services/error_handler.py'
        ]
        
        missing_files = []
        
        for file_path in required_files:
            full_path = api_dir / file_path
            if full_path.exists():
                if self.verbose:
                    print(f"  PASS {file_path}")
            else:
                missing_files.append(file_path)
                if self.verbose:
                    print(f"  FAIL {file_path} - NOT FOUND")
        
        if missing_files:
            if self.verbose:
                print(f"\nWARNING: Missing API files: {', '.join(missing_files)}")
                print("Some tests may fail due to missing components")
            return False
        
        if self.verbose:
            print("API structure is complete")
        return True
    
    def generate_test_report(self) -> None:
        # Generate test report
        if not self.verbose:
            return
        
        print("\n API Test Report:")
        
        execution_time = self.test_results['total_execution_time']
        total_tests = self.test_results['individual_tests_run']
        passed_tests = self.test_results['tests_passed']
        failed_tests = self.test_results['tests_failed']
        
        print(f"Execution Time: {execution_time:.2f} seconds")
        print(f"Total Tests Run: {total_tests}")
        print(f"Tests Passed: {passed_tests}")
        print(f"Tests Failed: {failed_tests}")
        
        if total_tests > 0:
            pass_rate = (passed_tests / total_tests) * 100
            print(f"Pass Rate: {pass_rate:.1f}%")
        
        # Test categories breakdown
        print(f"\nTest Suites Executed: {self.test_results['test_suites_run']}")
        
        # Error summary
        if self.test_results['error_summary']:
            print(f"\nErrors Encountered: {len(self.test_results['error_summary'])}")
            for i, error in enumerate(self.test_results['error_summary'], 1):
                if isinstance(error, dict):
                    print(f"  {i}. {error.get('category', 'Unknown')}: {error.get('error', 'Unknown error')}")
                else:
                    print(f"  {i}. {error}")
        
        # Performance analysis
        if execution_time > 0 and total_tests > 0:
            avg_time_per_test = execution_time / total_tests
            print(f"\nPerformance Metrics:")
            print(f"  Average time per test: {avg_time_per_test:.3f} seconds")
            
            if avg_time_per_test > 1.0:
                print(f"  WARNING: Tests are running slowly (>{avg_time_per_test:.1f}s per test)")
            
            if execution_time > 60:
                print(f"  WARNING: Total execution time is high ({execution_time:.1f}s)")
        
        # Final status
        print("\nFINAL RESULTS:")
        if failed_tests == 0 and not self.test_results['error_summary']:
            print("SUCCESS: API is functioning correctly.")
        elif failed_tests == 0 and self.test_results['error_summary']:
            print("WARNING: Tests passed but some issues were encountered.")
        else:
            print(f"FAILURE: {failed_tests} tests failed. API needs attention.")
    
    def save_test_results(self, output_file: str = None) -> None:
        # Save test results to JSON file
        if output_file is None:
            output_file = f"api_test_results_{int(time.time())}.json"
        
        try:
            with open(output_file, 'w') as f:
                json.dump(self.test_results, f, indent=2, default=str)
            print(f"\nTest results saved to: {output_file}")
        except Exception as e:
            print(f"Failed to save test results: {str(e)}")

def main():
    # Main function for running API tests
    parser = argparse.ArgumentParser(description="API Test Runner")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--no-integration", action="store_true", help="Skip integration tests")
    parser.add_argument("--save-results", type=str, help="Save results to specified file")
    parser.add_argument("--check-only", action="store_true", help="Only check dependencies and structure")
    
    args = parser.parse_args()
    
    # Initialize test runner
    runner = APITestRunner(
        verbose=args.verbose,
        include_integration=not args.no_integration
    )
    
    # Check dependencies and structure
    deps_ok = runner.check_api_dependencies()
    structure_ok = runner.check_api_structure()
    
    if args.check_only:
        if deps_ok and structure_ok:
            print("\n[PASS] API is ready for testing")
            return 0
        else:
            print("\n[FAIL] API setup issues found")
            return 1
    
    if not deps_ok:
        print("\nCannot run tests due to missing dependencies")
        return 1

    overall_success = True
    
    # Run main test suite
    comprehensive_success = runner.run_comprehensive_tests()
    overall_success = overall_success and comprehensive_success
    
    
    # Run pytest tests
    pytest_success = runner.run_pytest_tests()
    overall_success = overall_success and pytest_success
    
    # Generate report
    runner.generate_test_report()
    
    # Save results if requested
    if args.save_results:
        runner.save_test_results(args.save_results)
    
    # Return appropriate exit code
    return 0 if overall_success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)