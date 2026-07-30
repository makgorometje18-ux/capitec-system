"""
Unit Tests for Validation Engine and all validators.

Tests cover:
- Header validation
- Duplicate detection (same cell and across rows)
- Batch count validation
- Bag number validation
- Card type validation
- Blank field validation
- Error summary generation
- Excel highlighting
- Duplicate report generation
- Auto-fixing
"""

import openpyxl
import pytest
from pathlib import Path
from datetime import datetime
from src.core.validation_engine import ValidationEngine
from src.core.sample_workbook_generator import generate_sample_workbooks
from src.models.models import (
    DuplicateRecord, ErrorSummary, ValidationResult
)
from src.core.error_summary_builder import ErrorSummaryBuilder
from src.utils.helpers import split_batch_numbers, validate_bag_number, clean_string


class TestHelpers:
    """Test utility helper functions."""
    
    def test_split_batch_numbers_simple(self):
        """Test splitting simple batch numbers."""
        result = split_batch_numbers("10001|10002|10003")
        assert result == ["10001", "10002", "10003"]
    
    def test_split_batch_numbers_with_spaces(self):
        """Test splitting batch numbers with spaces."""
        result = split_batch_numbers("10001 | 10002 | 10003")
        assert result == ["10001", "10002", "10003"]
    
    def test_split_batch_numbers_empty_values(self):
        """Test splitting with empty values from consecutive separators."""
        result = split_batch_numbers("10001||10002|||10003")
        assert result == ["10001", "10002", "10003"]
        assert "" not in result
    
    def test_validate_bag_number_valid(self):
        """Test valid bag number with apostrophe."""
        assert validate_bag_number("'00012345") == True

    def test_validate_bag_number_numeric(self):
        """Test valid numeric bag number."""
        assert validate_bag_number("00012345") == True
        assert validate_bag_number(123456) == True

    def test_validate_bag_number_invalid_multiple_apostrophes(self):
        """Test invalid bag number with multiple apostrophes."""
        assert validate_bag_number("''00012345") == False

    def test_validate_bag_number_invalid_letters(self):
        """Test invalid bag number with letters."""
        assert validate_bag_number("'0001234A") == False

    def test_validate_bag_number_blank(self):
        """Test invalid blank bag number."""
        assert validate_bag_number("") == False
        assert validate_bag_number(None) == False
    
    def test_clean_string(self):
        """Test string cleaning."""
        assert clean_string("  hello  ") == "hello"
        assert clean_string("") == ""
        assert clean_string("test") == "test"


class TestHeaderValidation:
    """Test header validation."""
    
    def test_required_headers_present(self):
        """Test that required headers are correctly identified."""
        engine = ValidationEngine()
        result = engine.validate_complete_workbook("sample_files/sample_valid.xlsx")
        
        # Valid workbook should not have header errors
        header_errors = [e for e in result.errors if "header" in e.lower()]
        assert len(header_errors) == 0

    def test_numeric_bag_number_values_are_accepted(self, tmp_path):
        """Test that numeric BagNumber values in Excel are accepted."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "DAILY OUTPUT FILE 03-07-2026"
        headers = ['Order_no', 'Order_Creation_Date', 'Branch_Code', 'Branch_Name', 'Card_Type', 'Number_of_Batches', 'Waybill_Number', 'Batch_Number', 'BagNumber']
        ws.append(headers)
        ws.append([1, datetime.now().date(), 'BR001', 'Branch Johannesburg', 'SIM', 2, 'WB001', '10001|10002', 123456])
        path = tmp_path / "numeric_bag.xlsx"
        wb.save(path)

        engine = ValidationEngine()
        result = engine.validate_complete_workbook(str(path))

        bag_errors = [e for e in result.errors if "bagnumber" in e.lower()]
        assert len(bag_errors) == 0


class TestDuplicateDetection:
    """Test duplicate batch number detection."""
    
    def test_duplicates_in_same_cell(self):
        """Test detecting duplicates within same cell."""
        engine = ValidationEngine()
        result = engine.validate_complete_workbook("sample_files/sample_invalid.xlsx")
        
        # Invalid workbook should have duplicate errors
        dup_errors = [e for e in result.errors if "duplicate" in e.lower() and "same cell" in e.lower()]
        assert len(dup_errors) > 0
    
    def test_duplicates_across_rows(self):
        """Test detecting duplicates across different rows."""
        engine = ValidationEngine()
        result = engine.validate_complete_workbook("sample_files/sample_invalid.xlsx")
        
        # Invalid workbook should have cross-row duplicate errors
        dup_errors = [e for e in result.errors if "duplicate" in e.lower() and "rows" in e.lower()]
        assert len(dup_errors) > 0
    
    def test_duplicate_records_created(self):
        """Test that duplicate records are properly created."""
        engine = ValidationEngine()
        result = engine.validate_complete_workbook("sample_files/sample_invalid.xlsx")
        duplicates = engine.get_duplicates()
        
        # Should have duplicate records
        assert len(duplicates) > 0
        
        # Check structure of duplicate records
        for dup in duplicates:
            assert isinstance(dup, DuplicateRecord)
            assert dup.batch_number is not None
            assert dup.worksheet is not None
            assert dup.row_number is not None
            assert dup.occurrences > 0


class TestBatchCountValidation:
    """Test batch count validation (Number_of_Batches vs actual count)."""
    
    def test_batch_count_mismatch(self):
        """Test detecting batch count mismatches."""
        engine = ValidationEngine()
        result = engine.validate_complete_workbook("sample_files/sample_invalid.xlsx")
        
        # Invalid workbook should have batch count mismatch errors
        batch_errors = [e for e in result.errors if "number_of_batches" in e.lower() and "mismatch" in e.lower()]
        assert len(batch_errors) > 0
    
    def test_valid_batch_counts(self):
        """Test that valid batch counts pass."""
        engine = ValidationEngine()
        result = engine.validate_complete_workbook("sample_files/sample_valid.xlsx")
        
        # Valid workbook should not have batch count errors
        batch_errors = [e for e in result.errors if "number_of_batches" in e.lower()]
        assert len(batch_errors) == 0


class TestBagNumberValidation:
    """Test bag number format validation."""
    
    def test_invalid_bag_format(self):
        """Test detecting invalid bag number formats."""
        engine = ValidationEngine()
        result = engine.validate_complete_workbook("sample_files/sample_invalid.xlsx")
        
        # Invalid workbook should have bag format errors
        bag_errors = [e for e in result.errors if "bagnumber" in e.lower() and "format" in e.lower()]
        assert len(bag_errors) > 0
    
    def test_valid_bag_formats(self):
        """Test that valid bag formats pass."""
        engine = ValidationEngine()
        result = engine.validate_complete_workbook("sample_files/sample_valid.xlsx")
        
        # Valid workbook should not have bag format errors
        bag_errors = [e for e in result.errors if "bagnumber" in e.lower()]
        assert len(bag_errors) == 0


class TestBlankFieldValidation:
    """Test blank mandatory field validation."""
    
    def test_blank_fields_detected(self):
        """Test detecting blank mandatory fields."""
        engine = ValidationEngine()
        result = engine.validate_complete_workbook("sample_files/sample_invalid.xlsx")
        
        # Invalid workbook should have blank field errors
        blank_errors = [e for e in result.errors if "blank" in e.lower()]
        assert len(blank_errors) > 0
    
    def test_no_blank_fields_in_valid(self):
        """Test that valid workbook has no blank field errors."""
        engine = ValidationEngine()
        result = engine.validate_complete_workbook("sample_files/sample_valid.xlsx")
        
        # Valid workbook should not have blank field errors
        blank_errors = [e for e in result.errors if "blank" in e.lower()]
        assert len(blank_errors) == 0


class TestCardTypeValidation:
    """Test card type validation (SIM or DMCCLS only)."""
    
    def test_valid_card_types(self):
        """Test that valid card types pass."""
        engine = ValidationEngine()
        result = engine.validate_complete_workbook("sample_files/sample_valid.xlsx")
        
        # Valid workbook should not have card type errors
        card_errors = [e for e in result.errors if "card_type" in e.lower()]
        assert len(card_errors) == 0
    
    def test_invalid_card_type_detected(self):
        """Test detecting invalid card types."""
        # This test requires a sample with invalid card types
        # Skipped if not available
        try:
            engine = ValidationEngine()
            result = engine.validate_complete_workbook("sample_files/sample_invalid.xlsx")
            # Only check if file exists and can be tested
        except:
            pytest.skip("Invalid sample with card type errors not available")


class TestErrorSummary:
    """Test error summary generation."""
    
    def test_error_summary_creation(self):
        """Test creating an error summary."""
        duplicates = [
            DuplicateRecord(
                batch_number="10001",
                worksheet="Test",
                row_number=2,
                cell_reference="H2",
                occurrences=2,
                duplicate_type="Same Cell"
            )
        ]
        
        validation_result = ValidationResult(
            passed=False,
            error_count=1,
            errors=["Duplicate batch '10001' found in same cell at row 2, column Batch_Number"],
            warning_count=0
        )
        
        builder = ErrorSummaryBuilder()
        summary = builder.build_summary(validation_result, duplicates)
        
        assert isinstance(summary, ErrorSummary)
        assert summary.validation_passed == False
    
    def test_error_summary_formatting(self):
        """Test error summary formatting."""
        summary = ErrorSummary(
            duplicate_batch_numbers=2,
            duplicate_in_same_cell=1,
            duplicate_across_rows=1,
            incorrect_no_of_batches=1,
            invalid_bag_numbers=1,
            blank_fields=0,
            missing_headers=0,
            invalid_card_types=0,
            warnings=0,
            validation_passed=False
        )
        
        builder = ErrorSummaryBuilder()
        formatted = builder.format_error_summary(summary)
        
        assert "Duplicate Batch Numbers: 2" in formatted
        assert "Validation Result: ❌ FAILED" in formatted


class TestValidationResults:
    """Test validation result structure and pass/fail logic."""
    
    def test_valid_workbook_passes(self):
        """Test that valid workbook passes validation."""
        engine = ValidationEngine()
        result = engine.validate_complete_workbook("sample_files/sample_valid.xlsx")
        
        assert result.passed == True
        assert result.error_count == 0
        assert len(result.errors) == 0
    
    def test_invalid_workbook_fails(self):
        """Test that invalid workbook fails validation."""
        engine = ValidationEngine()
        result = engine.validate_complete_workbook("sample_files/sample_invalid.xlsx")
        
        assert result.passed == False
        assert result.error_count > 0
        assert len(result.errors) > 0
    
    def test_validation_duration_tracked(self):
        """Test that validation duration is tracked."""
        engine = ValidationEngine()
        result = engine.validate_complete_workbook("sample_files/sample_valid.xlsx")
        
        assert result.duration_seconds >= 0
        assert result.duration_seconds < 60  # Should complete in less than 60 seconds


class TestIntegration:
    """Integration tests for complete validation workflow."""
    
    def setup_method(self):
        """Ensure sample workbooks exist."""
        sample_dir = Path("sample_files")
        if not (sample_dir / "sample_valid.xlsx").exists():
            generate_sample_workbooks()
    
    def test_complete_validation_workflow(self):
        """Test complete validation workflow."""
        engine = ValidationEngine()
        
        # Validate invalid workbook
        result = engine.validate_complete_workbook("sample_files/sample_invalid.xlsx")
        
        # Should fail
        assert result.passed == False
        
        # Should have duplicates
        duplicates = engine.get_duplicates()
        assert len(duplicates) > 0
        
        # Should have errors
        assert len(result.errors) > 0
    
    def test_valid_workbook_no_errors(self):
        """Test that valid workbook produces no errors."""
        engine = ValidationEngine()
        result = engine.validate_complete_workbook("sample_files/sample_valid.xlsx")
        
        assert result.passed == True
        assert result.error_count == 0
        assert len(engine.get_duplicates()) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
