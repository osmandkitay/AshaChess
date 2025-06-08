#!/usr/bin/env python3
import unittest
import os
import sys

# Add parent directory to path to import test modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_all_tests():
    """Run all tests for the 2HS Chess game."""
    # Discover and run all tests in the tests directory
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(os.path.dirname(__file__), pattern="test_*.py")
    
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Return non-zero exit code if tests failed
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run_all_tests()) 