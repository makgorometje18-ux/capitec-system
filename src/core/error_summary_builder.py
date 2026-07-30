"""
Error Summary Builder - Extracts error information from validation results.
"""

from typing import List, Dict
from src.models.models import ErrorSummary, ValidationResult, DuplicateRecord, ValidationError
from src.utils.logger import get_logger


class ErrorSummaryBuilder:
    """
    Builds an ErrorSummary from validation results.
    
    Analyzes error messages and duplicate records to create a categorized
    error summary for display in the Error Summary Panel.
    """
    
    def __init__(self):
        """Initialize the Error Summary Builder."""
        self.logger = get_logger()
    
    def build_summary(self, validation_result: ValidationResult, 
                     duplicates: List[DuplicateRecord]) -> ErrorSummary:
        """
        Build an error summary from validation results.
        
        Args:
            validation_result: ValidationResult object from validation engine.
            duplicates: List of DuplicateRecord objects found during validation.
            
        Returns:
            ErrorSummary object with categorized error counts.
        """
        summary = ErrorSummary()
        summary.validation_passed = validation_result.passed
        summary.warnings = validation_result.warning_count
        
        # Extract error counts from structured validation errors if available
        if hasattr(validation_result, 'validation_errors') and validation_result.validation_errors:
            self._categorize_structured_errors(validation_result.validation_errors, summary)
        else:
            # Fall back to legacy string parsing
            self._categorize_errors(validation_result.errors, summary)
        
        # Extract duplicate information
        self._categorize_duplicates(duplicates, summary)
        
        self.logger.info(f"Error summary built: {summary.get_total_errors()} total errors")
        return summary
    
    def _categorize_errors(self, errors: List[str], summary: ErrorSummary) -> None:
        """
        Categorize errors from error message strings (legacy fallback).
        
        Args:
            errors: List of error message strings.
            summary: ErrorSummary object to populate.
        """
        for error in errors:
            error_lower = error.lower()
            
            # Categorize based on error message content
            if "duplicate batch" in error_lower and "same cell" in error_lower:
                summary.duplicate_batch_numbers += 1
                summary.duplicate_in_same_cell += 1
            
            elif "duplicate batch" in error_lower:
                summary.duplicate_batch_numbers += 1
                if "across" in error_lower or "rows" in error_lower:
                    summary.duplicate_across_rows += 1
            
            elif "number_of_batches" in error_lower and "mismatch" in error_lower:
                summary.incorrect_no_of_batches += 1
            
            elif "bagnumber" in error_lower and "format" in error_lower:
                summary.invalid_bag_numbers += 1
            
            elif "blank" in error_lower:
                summary.blank_fields += 1
            
            elif "missing" in error_lower and "header" in error_lower:
                summary.missing_headers += 1
            
            elif "card_type" in error_lower:
                summary.invalid_card_types += 1
            
            elif "cross-workbook" in error_lower:
                summary.cross_workbook_duplicates += 1
    
    def _categorize_structured_errors(self, validation_errors: List[ValidationError], summary: ErrorSummary) -> None:
        """
        Categorize errors from structured ValidationError objects.
        
        Args:
            validation_errors: List of ValidationError objects.
            summary: ErrorSummary object to populate.
        """
        for verr in validation_errors:
            error_type = verr.error_type.upper()
            
            if error_type == "DUPLICATE_BATCH_SAME_CELL":
                summary.duplicate_batch_numbers += 1
                summary.duplicate_in_same_cell += 1
            elif error_type == "DUPLICATE_ACROSS_ROWS":
                summary.duplicate_batch_numbers += 1
                summary.duplicate_across_rows += 1
            elif error_type == "DUPLICATE_CROSS_WORKBOOK":
                summary.duplicate_batch_numbers += 1
                summary.cross_workbook_duplicates += 1
            elif error_type == "BATCH_MISMATCH":
                summary.incorrect_no_of_batches += 1
            elif error_type == "INVALID_BAG":
                summary.invalid_bag_numbers += 1
            elif error_type == "BLANK_FIELD":
                summary.blank_fields += 1
            elif error_type == "MISSING_HEADER":
                summary.missing_headers += 1
            elif error_type == "INVALID_CARD_TYPE":
                summary.invalid_card_types += 1
    
    def _categorize_duplicates(self, duplicates: List[DuplicateRecord], 
                              summary: ErrorSummary) -> None:
        """
        Extract duplicate information.
        
        Args:
            duplicates: List of DuplicateRecord objects.
            summary: ErrorSummary object to populate.
        """
        # Count unique duplicate batch numbers by category
        same_cell_batches = set()
        across_rows_batches = set()
        previous_batches = set()

        for duplicate in duplicates:
            if duplicate.duplicate_type == "Same Cell":
                same_cell_batches.add(duplicate.batch_number)
            elif duplicate.duplicate_type == "Different Rows":
                across_rows_batches.add(duplicate.batch_number)
            elif duplicate.duplicate_type in ("Previous Workbook", "Prev Workbook", "Previous"):
                previous_batches.add(duplicate.batch_number)

        # Update summary counts
        summary.duplicate_in_same_cell = len(same_cell_batches)
        summary.duplicate_across_rows = len(across_rows_batches)
        summary.duplicate_in_previous = len(previous_batches)
        # Total duplicate batch numbers
        summary.duplicate_batch_numbers = len(same_cell_batches | across_rows_batches | previous_batches)
    
    def format_error_summary(self, summary: ErrorSummary) -> str:
        """
        Format error summary as a human-readable string.
        
        Args:
            summary: ErrorSummary object.
            
        Returns:
            Formatted error summary string.
        """
        lines = [
            "Validation Summary",
            "=" * 50,
            f"Duplicate Batch Numbers: {summary.duplicate_batch_numbers}",
            f"  • In Same Cell: {summary.duplicate_in_same_cell}",
            f"  • Across Rows: {summary.duplicate_across_rows}",
            f"Incorrect Number_of_Batches: {summary.incorrect_no_of_batches}",
            f"Invalid Bag Numbers: {summary.invalid_bag_numbers}",
            f"Blank Fields: {summary.blank_fields}",
            f"Missing Headers: {summary.missing_headers}",
            f"Invalid Card Types: {summary.invalid_card_types}",
            f"Warnings: {summary.warnings}",
            "=" * 50,
            f"Validation Result: {'✅ PASSED' if summary.validation_passed else '❌ FAILED'}",
        ]
        
        return "\n".join(lines)
    
    def print_error_summary(self, summary: ErrorSummary) -> None:
        """
        Print error summary to logger.
        
        Args:
            summary: ErrorSummary object.
        """
        formatted = self.format_error_summary(summary)
        self.logger.info(f"\n{formatted}")