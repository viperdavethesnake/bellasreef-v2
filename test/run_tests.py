#!/usr/bin/env python3
"""
Bella's Reef Backend Test Runner

This script provides a comprehensive test execution interface for the Bella's Reef backend.
It supports running different types of tests, generating reports, and managing test environments.

Usage:
    python backend/tests/run_tests.py                    # Run all tests
    python backend/tests/run_tests.py --system           # Run system tests only
    python backend/tests/run_tests.py --scheduler        # Run scheduler tests only
    python backend/tests/run_tests.py --poller           # Run poller tests only
    python backend/tests/run_tests.py --history          # Run history tests only
    python backend/tests/run_tests.py --coverage         # Run with coverage report
    python backend/tests/run_tests.py --parallel         # Run tests in parallel
    python backend/tests/run_tests.py --html-report      # Generate HTML report
    python backend/tests/run_tests.py --help             # Show help

Features:
- Selective test execution by subsystem
- Coverage reporting
- Parallel test execution
- HTML test reports
- Performance benchmarking
- Environment validation
- Test result summaries
"""

import argparse
import os
import sys
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

class TestRunner:
    """Comprehensive test runner for Bella's Reef backend."""
    
    def __init__(self):
        self.backend_dir = Path(__file__).parent.parent
        self.tests_dir = Path(__file__).parent
        self.results_dir = self.tests_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        # Test categories and their corresponding test files
        self.test_categories = {
            "system": ["test_system.py"],
            "scheduler": ["test_scheduler.py"],
            "poller": ["test_poller.py"],
            "history": ["test_history.py"],
            "all": ["test_system.py", "test_scheduler.py", "test_poller.py", "test_history.py"]
        }
    
    def validate_environment(self) -> bool:
        """Validate that the test environment is properly set up."""
        print("🔍 Validating test environment...")
        
        # Check if we're in the right directory
        if not (self.backend_dir / "app").exists():
            print("❌ Error: app directory not found. Please run from backend directory.")
            return False
        
        # Check if pytest is available
        try:
            subprocess.run([sys.executable, "-m", "pytest", "--version"], 
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Error: pytest not found. Please install test requirements:")
            print("   pip install -r backend/tests/requirements-test.txt")
            return False
        
        # Check if .env file exists
        env_file = self.backend_dir / ".env"
        if not env_file.exists():
            print("⚠️  Warning: .env file not found. Tests may use default configuration.")
        
        print("✅ Test environment validation passed")
        return True
    
    def run_tests(self, category: str, options: Dict[str, Any]) -> bool:
        """Run tests for a specific category."""
        if category not in self.test_categories:
            print(f"❌ Error: Unknown test category '{category}'")
            return False
        
        test_files = self.test_categories[category]
        print(f"🚀 Running {category} tests...")
        
        # Build pytest command
        cmd = [sys.executable, "-m", "pytest"]
        
        # Add test files
        for test_file in test_files:
            cmd.append(str(self.tests_dir / test_file))
        
        # Add options
        if options.get("verbose"):
            cmd.append("-v")
        
        if options.get("coverage"):
            cmd.extend(["--cov=app", "--cov-report=term-missing"])
            if options.get("html_report"):
                cmd.extend(["--cov-report=html:" + str(self.results_dir / "coverage")])
        
        if options.get("parallel"):
            cmd.extend(["-n", "auto"])
        
        if options.get("html_report"):
            cmd.extend(["--html=" + str(self.results_dir / "test_report.html")])
        
        if options.get("benchmark"):
            cmd.append("--benchmark-only")
        
        # Add markers if specified
        if category != "all":
            cmd.extend(["-m", category])
        
        # Run tests
        start_time = time.time()
        try:
            result = subprocess.run(cmd, cwd=self.backend_dir, check=False)
            end_time = time.time()
            
            duration = end_time - start_time
            print(f"⏱️  Tests completed in {duration:.2f} seconds")
            
            if result.returncode == 0:
                print(f"✅ {category.title()} tests passed")
                return True
            else:
                print(f"❌ {category.title()} tests failed")
                return False
                
        except Exception as e:
            print(f"❌ Error running tests: {e}")
            return False
    
    def run_all_tests(self, options: Dict[str, Any]) -> bool:
        """Run all tests."""
        print("🚀 Running all tests...")
        
        all_passed = True
        start_time = time.time()
        
        for category in ["system", "scheduler", "poller", "history"]:
            print(f"\n{'='*50}")
            print(f"Testing {category.upper()} subsystem")
            print(f"{'='*50}")
            
            if not self.run_tests(category, options):
                all_passed = False
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        print(f"\n{'='*50}")
        print("TEST SUMMARY")
        print(f"{'='*50}")
        print(f"Total duration: {total_duration:.2f} seconds")
        
        if all_passed:
            print("🎉 All tests passed!")
        else:
            print("❌ Some tests failed")
        
        return all_passed
    
    def generate_report(self, options: Dict[str, Any]):
        """Generate test reports."""
        if not options.get("coverage") and not options.get("html_report"):
            return
        
        print("📊 Generating reports...")
        
        # Coverage report
        if options.get("coverage"):
            coverage_dir = self.results_dir / "coverage"
            if coverage_dir.exists():
                print(f"📈 Coverage report available at: {coverage_dir}")
        
        # HTML report
        if options.get("html_report"):
            html_file = self.results_dir / "test_report.html"
            if html_file.exists():
                print(f"📄 HTML report available at: {html_file}")
    
    def cleanup(self):
        """Clean up test artifacts."""
        print("🧹 Cleaning up test artifacts...")
        
        # Remove .pyc files
        for pyc_file in self.backend_dir.rglob("*.pyc"):
            pyc_file.unlink()
        
        # Remove __pycache__ directories
        for cache_dir in self.backend_dir.rglob("__pycache__"):
            import shutil
            shutil.rmtree(cache_dir)
        
        print("✅ Cleanup completed")

def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(
        description="Bella's Reef Backend Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python backend/tests/run_tests.py                    # Run all tests
  python backend/tests/run_tests.py --system           # Run system tests only
  python backend/tests/run_tests.py --coverage         # Run with coverage
  python backend/tests/run_tests.py --parallel         # Run in parallel
  python backend/tests/run_tests.py --html-report      # Generate HTML report
  python backend/tests/run_tests.py --cleanup          # Clean up artifacts
        """
    )
    
    # Test category options
    parser.add_argument("--system", action="store_true", help="Run system tests only")
    parser.add_argument("--scheduler", action="store_true", help="Run scheduler tests only")
    parser.add_argument("--poller", action="store_true", help="Run poller tests only")
    parser.add_argument("--history", action="store_true", help="Run history tests only")
    
    # Test execution options
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--parallel", "-n", action="store_true", help="Run tests in parallel")
    parser.add_argument("--html-report", action="store_true", help="Generate HTML report")
    parser.add_argument("--benchmark", action="store_true", help="Run performance benchmarks")
    
    # Utility options
    parser.add_argument("--cleanup", action="store_true", help="Clean up test artifacts")
    parser.add_argument("--validate", action="store_true", help="Validate test environment only")
    
    args = parser.parse_args()
    
    # Initialize test runner
    runner = TestRunner()
    
    # Validate environment
    if not runner.validate_environment():
        sys.exit(1)
    
    # Handle cleanup
    if args.cleanup:
        runner.cleanup()
        return
    
    # Handle validation only
    if args.validate:
        print("✅ Environment validation completed")
        return
    
    # Determine test category
    category = "all"
    if args.system:
        category = "system"
    elif args.scheduler:
        category = "scheduler"
    elif args.poller:
        category = "poller"
    elif args.history:
        category = "history"
    
    # Build options dictionary
    options = {
        "verbose": args.verbose,
        "coverage": args.coverage,
        "parallel": args.parallel,
        "html_report": args.html_report,
        "benchmark": args.benchmark
    }
    
    # Run tests
    if category == "all":
        success = runner.run_all_tests(options)
    else:
        success = runner.run_tests(category, options)
    
    # Generate reports
    runner.generate_report(options)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 