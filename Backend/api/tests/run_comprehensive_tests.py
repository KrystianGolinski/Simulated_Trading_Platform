#!/usr/bin/env python3

# This script runs the comprehensive API test suite from comprehensive_API_testing.py.
#
# It provides a command-line interface to:
# - Check for dependencies and correct API file structure.
# - Execute the test suite.
# - Print a summary of the results.
# - Optionally save the results to a JSON file.

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Add the API directory to Python path for imports
api_dir = Path(__file__).parent.parent
sys.path.insert(0, str(api_dir))

# Import our test suite
from tests.comprehensive_API_testing import ComprehensiveAPITestSuite


class APITestRunner:
    """
    Orchestrates the test execution process.

    This class is responsible for checking dependencies, validating the API structure,
    running the test suite, and reporting the results.
    """

    def __init__(self, verbose: bool = False, include_integration: bool = True):
        """Initializes the test runner."""
        self.verbose = verbose
        self.include_integration = include_integration

        self.test_results = {
            "total_execution_time": 0,
            "test_suites_run": 0,
            "individual_tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "coverage_report": {},
            "performance_metrics": {},
            "error_summary": [],
        }

    def run_comprehensive_tests(self) -> bool:
        """
        Executes the main test suite and collects the results.

        Returns:
            bool: True if all tests pass, False otherwise.
        """
        if self.verbose:
            print("Executing API test suite:")
            print(f"Verbose mode: {'ON' if self.verbose else 'OFF'}")
            print(
                f"Integration tests: {'INCLUDED' if self.include_integration else 'EXCLUDED'}"
            )
            print()

        start_time = time.time()

        try:
            test_suite = ComprehensiveAPITestSuite()

            if self.verbose:
                print("Initializing test suite...")
            test_suite.run_all_tests()

            # Collect results from the test suite
            self.test_results.update(
                {
                    "total_execution_time": time.time() - start_time,
                    "test_suites_run": 1,
                    "individual_tests_run": test_suite.test_results["total_tests"],
                    "tests_passed": test_suite.test_results["passed_tests"],
                    "tests_failed": test_suite.test_results["failed_tests"],
                    "error_summary": test_suite.test_results["failed_test_details"],
                }
            )

            success = test_suite.test_results["failed_tests"] == 0

        except Exception as e:
            print(f"CRITICAL ERROR: Failed to execute test suite: {str(e)}")
            self.test_results["error_summary"].append(
                {"category": "Test Suite Execution", "error": str(e)}
            )
            success = False

        self.test_results["total_execution_time"] = time.time() - start_time
        return success

    def check_api_dependencies(self) -> bool:
        """
        Verifies that required Python packages for testing are installed.

        Returns:
            bool: True if all dependencies are available, False otherwise.
        """
        if self.verbose:
            print("\nChecking API dependencies...")

        required_modules = [
            "fastapi",
            "uvicorn",
            "pydantic",
            "asyncpg",
            "pytest",
            "httpx",
        ]

        missing_modules = []

        for module in required_modules:
            try:
                __import__(module)
                if self.verbose:
                    print(f"  PASS: {module}")
            except ImportError:
                missing_modules.append(module)
                if self.verbose:
                    print(f"  FAIL: {module} - NOT FOUND")

        if missing_modules:
            if self.verbose:
                print(
                    f"\nERROR: Missing required modules: {', '.join(missing_modules)}"
                )
                print("Please install missing dependencies with:")
                print(f"pip install {' '.join(missing_modules)}")
            return False

        if self.verbose:
            print("All required dependencies are available.")
        return True

    def check_api_structure(self) -> bool:
        """
        Verifies that key API files and directories exist.

        Returns:
            bool: True if the structure seems correct, False otherwise.
        """
        if self.verbose:
            print("\nChecking API file structure...")

        required_files = [
            "main.py",
            "models.py",
            "database.py",
            "validation.py",
            "routers/health.py",
            "routers/simulation.py",
            "routers/stocks.py",
            "services/execution_service.py",
            "services/result_processor.py",
            "services/error_handler.py",
        ]

        missing_files = []

        for file_path in required_files:
            full_path = api_dir / file_path
            if full_path.exists():
                if self.verbose:
                    print(f"  PASS: {file_path}")
            else:
                missing_files.append(file_path)
                if self.verbose:
                    print(f"  FAIL: {file_path} - NOT FOUND")

        if missing_files:
            if self.verbose:
                print(f"\nWARNING: Missing API files: {', '.join(missing_files)}")
                print("Some tests may fail due to missing components.")
            return False

        if self.verbose:
            print("API structure is complete.")
        return True

    def generate_test_report(self) -> None:
        """Prints a summary of the test results to the console."""
        if not self.verbose:
            return

        print("\nAPI Test Report:")

        execution_time = self.test_results["total_execution_time"]
        total_tests = self.test_results["individual_tests_run"]
        passed_tests = self.test_results["tests_passed"]
        failed_tests = self.test_results["tests_failed"]

        print(f"Execution Time: {execution_time:.2f} seconds")
        print(f"Total Tests Run: {total_tests}")
        print(f"Tests Passed: {passed_tests}")
        print(f"Tests Failed: {failed_tests}")

        if total_tests > 0:
            pass_rate = (passed_tests / total_tests) * 100
            print(f"Pass Rate: {pass_rate:.1f}%")

        print(f"\nTest Suites Executed: {self.test_results['test_suites_run']}")

        if self.test_results["error_summary"]:
            print(f"\nErrors Encountered: {len(self.test_results['error_summary'])}")
            for i, error in enumerate(self.test_results["error_summary"], 1):
                if isinstance(error, dict):
                    print(
                        f"  {i}. {error.get('category', 'Unknown')}: {error.get('error', 'Unknown error')}"
                    )
                else:
                    print(f"  {i}. {error}")

        if execution_time > 0 and total_tests > 0:
            avg_time_per_test = execution_time / total_tests
            print(f"\nPerformance Metrics:")
            print(f"  Average time per test: {avg_time_per_test:.3f} seconds")

            if avg_time_per_test > 1.0:
                print(
                    f"  WARNING: Tests are running slowly (>{avg_time_per_test:.1f}s per test)"
                )

            if execution_time > 60:
                print(
                    f"  WARNING: Total execution time is high ({execution_time:.1f}s)"
                )

        print("\nFINAL RESULTS:")
        if failed_tests == 0 and not self.test_results["error_summary"]:
            print("SUCCESS: API is functioning correctly.")
        elif failed_tests == 0 and self.test_results["error_summary"]:
            print("WARNING: Tests passed but some issues were encountered.")
        else:
            print(f"FAILURE: {failed_tests} tests failed. API needs attention.")

    def save_test_results(self, output_file: str = None) -> None:
        """
        Saves test results to a JSON file.

        Args:
            output_file: Optional custom filename for result export.
        """
        if output_file is None:
            output_file = f"api_test_results_{int(time.time())}.json"

        try:
            with open(output_file, "w") as f:
                json.dump(self.test_results, f, indent=2, default=str)
            print(f"\nTest results saved to: {output_file}")
        except Exception as e:
            print(f"Failed to save test results: {str(e)}")


def main():
    """Parses command-line arguments and runs the API test runner."""
    parser = argparse.ArgumentParser(description="Runs the API test suite.")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "--no-integration", action="store_true", help="Skip integration tests"
    )
    parser.add_argument(
        "--save-results", type=str, help="Save results to specified file"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check dependencies and structure",
    )

    args = parser.parse_args()

    runner = APITestRunner(
        verbose=args.verbose, include_integration=not args.no_integration
    )

    deps_ok = runner.check_api_dependencies()
    structure_ok = runner.check_api_structure()

    if args.check_only:
        if deps_ok and structure_ok:
            print("\n[PASS] API is ready for testing.")
            return 0
        else:
            print("\n[FAIL] API setup issues found.")
            return 1

    if not deps_ok:
        print("\nCannot execute tests due to missing dependencies.")
        return 1

    overall_success = runner.run_comprehensive_tests()

    runner.generate_test_report()

    if args.save_results:
        runner.save_test_results(args.save_results)

    return 0 if overall_success else 1


if __name__ == "__main__":
    sys.exit(main())
