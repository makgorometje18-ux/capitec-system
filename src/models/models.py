"""
Models package - Data classes for the application.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class Workbook:
    """
    Represents an Excel workbook being processed.
    
    Attributes:
        file_path: Full path to the workbook file.
        file_name: Name of the workbook file.
        file_size: Size of the workbook in bytes.
        created_date: Date the workbook was created.
        modified_date: Date the workbook was last modified.
        worksheets: List of worksheet names in the workbook.
        is_valid: Whether the workbook is valid.
    """
    file_path: str
    file_name: str
    file_size: int = 0
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    worksheets: List[str] = field(default_factory=list)
    is_valid: bool = False


@dataclass
class ValidationResult:
    """
    Contains the results of validation for a workbook.
    
    Attributes:
        passed: Whether validation passed.
        error_count: Number of errors found.
        warning_count: Number of warnings found.
        duration_seconds: Time taken for validation.
        rows_processed: Number of Daily Output data rows processed.
        errors: List of validation error messages.
        warnings: List of validation warning messages.
        timestamp: When the validation occurred.
        steps: List of validation steps completed.
        summary: Summary statistics from the validation run.
        duplicates_found: Number of duplicate batch numbers found.
        validation_errors: List of structured ValidationError objects.
    """
    passed: bool = False
    error_count: int = 0
    warning_count: int = 0
    duration_seconds: float = 0.0
    rows_processed: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    steps: List['ValidationStep'] = field(default_factory=list)
    summary: Optional['ValidationSummary'] = None
    duplicates_found: int = 0
    validation_errors: List['ValidationError'] = field(default_factory=list)
    
    def add_error(self, error_message: str) -> None:
        """
        Add an error message to the validation result.
        
        Args:
            error_message: The error message to add.
        """
        self.errors.append(error_message)
        self.error_count = len(self.errors)
    
    def add_warning(self, warning_message: str) -> None:
        """
        Add a warning message to the validation result.
        
        Args:
            warning_message: The warning message to add.
        """
        self.warnings.append(warning_message)
        self.warning_count = len(self.warnings)
    
    def add_step(self, step: 'ValidationStep') -> None:
        """
        Add a completed validation step.
        
        Args:
            step: The ValidationStep to add.
        """
        self.steps.append(step)


@dataclass
class DuplicateRecord:
    """
    Represents a duplicate batch number found in the workbook.
    
    Attributes:
        batch_number: The duplicate batch number.
        worksheet: Name of the worksheet containing the duplicate.
        row_number: Row number where the duplicate appears.
        cell_reference: Excel cell reference (e.g., 'A1').
        occurrences: Number of times the batch appears.
        duplicate_type: Type of duplicate ('Same Cell' or 'Different Rows').
    """
    batch_number: str
    worksheet: str
    row_number: int
    cell_reference: str
    occurrences: int = 1
    duplicate_type: str = "Different Rows"


@dataclass
class CardStatistics:
    """
    Contains card counting statistics from validation.
    
    Attributes:
        sim_orders: Total SIM orders.
        sim_cards: Total SIM cards calculated.
        bank_orders: Total bank card orders.
        bank_cards: Total bank cards calculated.
        total_orders: Total orders.
        total_cards: Total cards.
    """
    sim_orders: int = 0
    sim_cards: int = 0
    bank_orders: int = 0
    bank_cards: int = 0
    total_orders: int = 0
    total_cards: int = 0


@dataclass
class SummaryRow:
    """
    Represents a row in the CAPITEC SUMMARY FILE REPORT worksheet.
    """
    row_number: int
    item_name: str
    total_quantity_received: Optional[int] = None
    quantity_in_stock: Optional[int] = None
    quantity_dispatched: Optional[int] = None
    comment: Optional[str] = None
    row_type: str = 'UNKNOWN'
    calculated_card_change: Optional[int] = None
    new_quantity_in_stock: Optional[int] = None
    new_quantity_dispatched: Optional[int] = None
    changes_required: bool = False
    raw_values: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CommercialBatch:
    """
    Represents a row in the Commercial Batch worksheet.
    """
    batch_number: str
    card_type: str
    quantity: int
    order_number: Optional[str] = None
    raw_row_index: Optional[int] = None


@dataclass
class SummaryDifference:
    """
    Represents a difference between calculated and existing summary values.
    """
    metric_name: str
    existing_value: Optional[int]
    calculated_value: int
    difference: Optional[int]
    status: str


@dataclass
class SummaryAnalysis:
    """
    Analysis result for the Summary Reconciliation Engine.
    """
    summary_worksheet_name: Optional[str]
    latest_daily_worksheet_name: Optional[str]
    sim_orders: int = 0
    sim_cards: int = 0
    dmcc_orders: int = 0
    dmcc_cards: int = 0
    total_orders: int = 0
    total_cards: int = 0
    summary_rows: List[SummaryRow] = field(default_factory=list)
    files_received_rows: List[SummaryRow] = field(default_factory=list)
    bank_card_rows: List[SummaryRow] = field(default_factory=list)
    sim_rows: List[SummaryRow] = field(default_factory=list)
    cconnect_rows: List[SummaryRow] = field(default_factory=list)
    existing_summary_values: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    current_summary_values: Dict[str, Optional[int]] = field(default_factory=dict)
    calculated_summary_values: Dict[str, int] = field(default_factory=dict)
    differences: List[SummaryDifference] = field(default_factory=list)
    has_changes: bool = False
    changes_count: int = 0
    preview_ready: bool = False
    validation_status: bool = False


@dataclass
class ValidationError:
    """
    Represents a validation error in the workbook.
    
    Attributes:
        rule_id: The business rule ID that failed.
        error_type: Categorized error type (e.g., DUPLICATE_BATCH, BLANK_FIELD).
        worksheet: Name of the worksheet with the error.
        row_number: Row number of the error.
        column_name: Name of the column with the error.
        cell_reference: Excel cell reference.
        error_message: Description of the error.
        invalid_value: The actual value that failed validation.
        suggested_fix: Suggested action to fix the error.
    """
    rule_id: str
    error_type: str = "UNKNOWN"
    worksheet: str = ""
    row_number: int = 0
    column_name: str = ""
    cell_reference: str = ""
    error_message: str = ""
    invalid_value: str = ""
    suggested_fix: Optional[str] = None


@dataclass
class SummaryUpdate:
    """
    Represents an update to the Summary Report.
    
    Attributes:
        item_name: Name of the item being updated.
        previous_dispatch: Previous dispatch quantity.
        new_dispatch: New dispatch quantity.
        previous_stock: Previous stock quantity.
        new_stock: New stock quantity.
        updated_time: When the update occurred.
    """
    item_name: str
    previous_dispatch: int
    new_dispatch: int
    previous_stock: int
    new_stock: int
    updated_time: datetime = field(default_factory=datetime.now)


@dataclass
class UpdateResult:
    """
    Represents the result of a summary worksheet update operation.
    """
    updated_fields: List[str] = field(default_factory=list)
    skipped_fields: List[str] = field(default_factory=list)
    failed_fields: List[str] = field(default_factory=list)
    elapsed_time: float = 0.0
    success: bool = False


@dataclass
class AuditLogEntry:
    """
    Represents an entry in the audit log.
    
    Attributes:
        action: Description of the action.
        user: User who performed the action.
        result: Result of the action (Success, Failure, etc.).
        description: Detailed description.
        timestamp: When the action occurred.
    """
    action: str
    user: Optional[str] = None
    result: str = "Success"
    description: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ValidationStep:
    """
    Represents a single validation step in the validation process.
    
    Attributes:
        step_name: Name of the validation step.
        passed: Whether this step passed.
        error_count: Number of errors in this step.
        errors: List of error messages.
        duration_ms: Time taken for this step in milliseconds.
    """
    step_name: str
    passed: bool = True
    error_count: int = 0
    errors: List[str] = field(default_factory=list)
    duration_ms: float = 0.0


@dataclass
class ValidationSummary:
    """
    Summary statistics from a complete validation run.
    
    Attributes:
        total_rows: Total data rows processed.
        duplicate_count: Number of duplicate batches found.
        error_rows: Number of rows with errors.
        header_errors: Number of header validation errors.
        batch_errors: Number of batch count errors.
        bag_errors: Number of bag format errors.
        blank_errors: Number of blank field errors.
    """
    total_rows: int = 0
    duplicate_count: int = 0
    error_rows: int = 0
    header_errors: int = 0
    batch_errors: int = 0
    bag_errors: int = 0
    blank_errors: int = 0


@dataclass
class ErrorSummary:
    """
    Detailed error summary with categorized error counts.
    
    Tracks counts of different error types for the Error Summary Panel.
    
    Attributes:
        duplicate_batch_numbers: Total duplicate batch numbers.
        duplicate_in_same_cell: Duplicates within same cell.
        duplicate_across_rows: Duplicates across different rows.
        incorrect_no_of_batches: Batch count mismatches.
        invalid_bag_numbers: Invalid bag number formats.
        blank_fields: Blank mandatory fields.
        missing_headers: Missing required headers.
        invalid_card_types: Invalid Card_Type values.
        warnings: Total warning count.
        validation_passed: Whether validation passed overall.
    """
    duplicate_batch_numbers: int = 0
    duplicate_in_same_cell: int = 0
    duplicate_across_rows: int = 0
    duplicate_in_previous: int = 0
    incorrect_no_of_batches: int = 0
    invalid_bag_numbers: int = 0
    blank_fields: int = 0
    missing_headers: int = 0
    invalid_card_types: int = 0
    warnings: int = 0
    validation_passed: bool = True
    
    def get_total_errors(self) -> int:
        """Get total error count across all categories."""
        return (self.duplicate_batch_numbers + 
                self.incorrect_no_of_batches + 
                self.invalid_bag_numbers + 
                self.blank_fields + 
                self.missing_headers + 
                self.invalid_card_types)
    
    def to_dict(self) -> dict:
        """
        Convert error summary to dictionary format.
        
        Returns:
            Dictionary representation of the error summary.
        """
        return {
            "duplicate_batch_numbers": self.duplicate_batch_numbers,
            "duplicate_in_same_cell": self.duplicate_in_same_cell,
            "duplicate_across_rows": self.duplicate_across_rows,
            "incorrect_no_of_batches": self.incorrect_no_of_batches,
            "invalid_bag_numbers": self.invalid_bag_numbers,
            "blank_fields": self.blank_fields,
            "missing_headers": self.missing_headers,
            "invalid_card_types": self.invalid_card_types,
            "warnings": self.warnings,
            "validation_passed": self.validation_passed,
            "total_errors": self.get_total_errors()
        }
