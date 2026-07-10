"""
Validation Engine Example - Demonstrates the complete validation workflow.

This example shows how to use the Validation Engine to validate a complete
Excel workbook with all validation checks working together.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.validation_engine import ValidationEngine
from src.utils.logger import get_logger


def print_validation_results(validation_result):
    """
    Pretty-print validation results.
    
    Args:
        validation_result: ValidationResult object from the engine.
    """
    print("\n" + "=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    
    # Overall status
    status = "✓ PASSED" if validation_result.passed else "✗ FAILED"
    print(f"\nStatus: {status}")
    print(f"Duration: {validation_result.duration_seconds:.2f} seconds")
    print(f"Errors: {validation_result.error_count}")
    print(f"Warnings: {validation_result.warning_count}")
    print(f"Duplicates Found: {validation_result.duplicates_found}")
    
    # Error details
    if validation_result.errors:
        print(f"\n--- ERRORS ({len(validation_result.errors)}) ---")
        for i, error in enumerate(validation_result.errors, 1):
            print(f"  {i}. {error}")
    
    # Warning details
    if validation_result.warnings:
        print(f"\n--- WARNINGS ({len(validation_result.warnings)}) ---")
        for i, warning in enumerate(validation_result.warnings, 1):
            print(f"  {i}. {warning}")
    
    print("\n" + "=" * 80)


def example_validate_workbook(workbook_path: str):
    """
    Example: Validate a complete workbook.
    
    Args:
        workbook_path: Path to the Excel workbook to validate.
    """
    logger = get_logger()
    logger.info(f"Example: Validating workbook: {workbook_path}")
    
    # Create validation engine
    engine = ValidationEngine()
    
    # Validate the workbook
    result = engine.validate_complete_workbook(workbook_path)
    
    # Print results
    print_validation_results(result)
    
    # Show duplicates if any
    duplicates = engine.get_duplicates()
    if duplicates:
        print("\n--- DUPLICATE BATCH NUMBERS ---")
        for dup in duplicates:
            print(f"  • {dup.batch_number} - Row {dup.row_number} - "
                  f"Occurrences: {dup.occurrences} ({dup.duplicate_type})")
    else:
        print("\nNo duplicate batch numbers found.")
    
    return result


def example_validate_without_file():
    """
    Example: Demonstrate error handling when workbook doesn't exist.
    """
    logger = get_logger()
    logger.info("Example: Validating non-existent workbook")
    
    engine = ValidationEngine()
    result = engine.validate_complete_workbook("nonexistent_file.xlsx")
    
    print_validation_results(result)


if __name__ == "__main__":
    logger = get_logger()
    logger.info("=" * 80)
    logger.info("Validation Engine Example")
    logger.info("=" * 80)
    
    # Example 1: Validate with non-existent file (demonstrates error handling)
    print("\n\nExample 1: Error Handling - Non-existent File")
    print("-" * 80)
    example_validate_without_file()
    
    # Example 2: Validate with actual workbook (if sample exists)
    sample_file = Path("sample_files") / "sample_daily_output.xlsx"
    if sample_file.exists():
        print("\n\nExample 2: Validation with Sample File")
        print("-" * 80)
        example_validate_workbook(str(sample_file))
    else:
        print(f"\n\nNote: Sample file not found at {sample_file}")
        print("To test with an actual workbook, place it at: sample_files/sample_daily_output.xlsx")
    
    logger.info("=" * 80)
    logger.info("Example Complete")
    logger.info("=" * 80)
