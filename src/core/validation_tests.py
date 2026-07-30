"""
Validation Engine Test - Tests with sample workbooks.

This script tests the Validation Engine with both valid and invalid
sample workbooks to demonstrate all validation features.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.validation_engine import ValidationEngine
from src.core.sample_workbook_generator import generate_sample_workbooks
from src.utils.logger import get_logger


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(title.center(80))
    print("=" * 80 + "\n")


def print_validation_results(workbook_path: str, result):
    """Print formatted validation results."""
    print(f"Workbook: {workbook_path}")
    print(f"Status: {'✓ PASSED' if result.passed else '✗ FAILED'}")
    print(f"Duration: {result.duration_seconds:.3f} seconds")
    print(f"Errors: {result.error_count}")
    print(f"Warnings: {result.warning_count}")
    print(f"Duplicates: {result.duplicates_found}\n")
    
    if result.errors:
        print("ERRORS:")
        for i, error in enumerate(result.errors, 1):
            print(f"  {i}. {error}")
        print()


def test_valid_workbook():
    """Test validation with a valid workbook."""
    print_header("TEST 1: Valid Workbook")
    
    engine = ValidationEngine()
    result = engine.validate_complete_workbook("sample_files/sample_valid.xlsx")
    
    print_validation_results("sample_valid.xlsx", result)
    
    if result.errors:
        print("ERROR: Expected no errors in valid workbook!")
        return False
    
    print("✓ TEST PASSED: Valid workbook validated successfully\n")
    return True


def test_invalid_workbook():
    """Test validation with an invalid workbook."""
    print_header("TEST 2: Invalid Workbook")
    
    engine = ValidationEngine()
    result = engine.validate_complete_workbook("sample_files/sample_invalid.xlsx")
    
    print_validation_results("sample_invalid.xlsx", result)
    
    if result.passed:
        print("ERROR: Expected validation to fail for invalid workbook!")
        return False
    
    # Check for expected errors
    expected_error_types = [
        "Blank field",
        "Duplicate batch",
        "Number_of_Batches mismatch",
        "Invalid BagNumber format"
    ]
    
    print("Expected error types found:")
    for error_type in expected_error_types:
        found = any(error_type.lower() in str(err).lower() for err in result.errors)
        status = "✓" if found else "✗"
        print(f"  {status} {error_type}")
    
    print("\n✓ TEST PASSED: Invalid workbook detected correctly\n")
    return True


def test_duplicate_detection():
    """Test duplicate batch detection."""
    print_header("TEST 3: Duplicate Batch Detection")
    
    engine = ValidationEngine()
    result = engine.validate_complete_workbook("sample_files/sample_invalid.xlsx")
    
    duplicates = engine.get_duplicates()
    
    print(f"Total Duplicates Found: {len(duplicates)}\n")
    
    if duplicates:
        print("Duplicate Details:")
        for dup in duplicates:
            print(f"  • Batch: {dup.batch_number}")
            print(f"    Worksheet: {dup.worksheet}")
            print(f"    Row: {dup.row_number}")
            print(f"    Occurrences: {dup.occurrences}")
            print(f"    Type: {dup.duplicate_type}\n")
    
    print("✓ TEST PASSED: Duplicate detection working\n")
    return True


def main():
    """Run all validation engine tests."""
    logger = get_logger()
    
    print_header("VALIDATION ENGINE TEST SUITE")
    
    # Ensure sample workbooks exist
    sample_dir = Path("sample_files")
    if not (sample_dir / "sample_valid.xlsx").exists():
        print("Generating sample workbooks...\n")
        generate_sample_workbooks()
    
    # Run tests
    results = []
    
    try:
        results.append(("Valid Workbook", test_valid_workbook()))
        results.append(("Invalid Workbook", test_invalid_workbook()))
        results.append(("Duplicate Detection", test_duplicate_detection()))
    except Exception as e:
        logger.error(f"Test error: {e}")
        print(f"\n✗ TEST FAILED: {e}\n")
        return 1
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓✓✓ ALL TESTS PASSED ✓✓✓\n")
        return 0
    else:
        print(f"\n✗✗✗ {total - passed} TEST(S) FAILED ✗✗✗\n")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
