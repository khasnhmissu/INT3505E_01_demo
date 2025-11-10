#!/usr/bin/env python
"""
Script chạy tất cả tests
Usage:
    python run_tests.py              # Chạy tất cả tests
    python run_tests.py unit         # Chỉ chạy unit tests
    python run_tests.py integration  # Chỉ chạy integration tests
"""

import sys
import unittest
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_unit_tests():
    """Chạy unit tests"""
    loader = unittest.TestLoader()
    suite = loader.discover('tests', pattern='unit_*.py')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

def run_integration_tests():
    """Chạy integration tests"""
    loader = unittest.TestLoader()
    suite = loader.discover('tests', pattern='integration_*.py')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

def run_all_tests():
    """Chạy tất cả tests"""
    loader = unittest.TestLoader()
    suite = loader.discover('tests', pattern='*_tests.py')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == '__main__':
    test_type = sys.argv[1] if len(sys.argv) > 1 else 'all'
    
    print(f"\n{'='*60}")
    print(f"  Running {test_type.upper()} tests")
    print(f"{'='*60}\n")
    
    if test_type == 'unit':
        success = run_unit_tests()
    elif test_type == 'integration':
        success = run_integration_tests()
    else:
        success = run_all_tests()
    
    print(f"\n{'='*60}")
    if success:
        print("  ✓ All tests passed!")
    else:
        print("  ✗ Some tests failed")
    print(f"{'='*60}\n")
    
    sys.exit(0 if success else 1)