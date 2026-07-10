# Validation Engine Documentation

## Overview

The Validation Engine is a comprehensive system for validating Excel workbooks against business rules. It implements all validation requirements from the Capitec Daily Reconciliation System specification.

## Components

### 1. Workbook Loader (workbook_loader.py)

Handles loading and accessing Excel workbooks using `openpyxl`.

**Key Features:**
- Load Excel files (.xlsx, .xls, .xlsm)
- Detect Daily Output File and Capitec Summary worksheets
- Extract headers and data rows
- Get column values with row numbers and cell references

**Key Methods:**
```python
# Load workbook
workbook = loader.load_workbook("file.xlsx")

# Detect sheets
daily_output_sheet = loader.detect_daily_output_sheet()
capitec_summary_sheet = loader.detect_capitec_summary_sheet()

# Get data
headers = loader.get_headers(sheet_name)
data_rows = loader.get_data_rows(sheet_name)
column_values = loader.get_column_values(sheet_name, "Batch_No")
```

### 2. Validation Engine (validation_engine.py)

Orchestrates all validation checks.

**Key Features:**
- Validates complete workbooks end-to-end
- Implements all business rules (BR001-BR010)
- Tracks validation steps and errors
- Returns detailed ValidationResult

**Business Rules Implemented:**

| Rule | Description | Implementation |
|------|-------------|-----------------|
| BR001 | Batch numbers must be unique across worksheet | `_validate_duplicates()` |
| BR002 | Batch numbers must not repeat in same cell | `_validate_duplicates()` |
| BR003 | Batch_No separated by '\|' character | `split_batch_numbers()` helper |
| BR004 | No_of_Batches equals count of values in Batch_No | `_validate_batch_counts()` |
| BR005 | Bag_No starts with exactly one apostrophe | `validate_bag_number()` helper |
| BR006 | SIM card count = Orders × 200 | Implemented in CardCounter |
| BR007 | Bank card count = Orders × 300 | Implemented in CardCounter |
| BR008 | Summary updates only if validation passes | Implemented in core controller |
| BR009 | Backup created before modifications | Implemented in BackupManager |
| BR010 | Every reconciliation logged | Implemented in AuditManager |

**Validation Workflow:**

```
Workbook → Load → Detect Daily Output Sheet → Validate Headers
     ↓
  Validate Duplicates (BR001, BR002)
     ↓
  Validate Batch Counts (BR004)
     ↓
  Validate Bag Numbers (BR005)
     ↓
  Validate Blank Fields
     ↓
  Generate ValidationResult
```

**Key Methods:**

```python
# Main validation
result = engine.validate_complete_workbook("file.xlsx")

# Get results
duplicates = engine.get_duplicates()
errors = engine.get_validation_errors()
```

### 3. Helper Functions (helpers.py)

**Utility Functions:**

```python
# Clean whitespace
clean_string("  text  ") → "text"

# Split batch numbers
split_batch_numbers("100|200|300") → ["100", "200", "300"]

# Validate bag format
validate_bag_number("'00012345") → True
validate_bag_number("''00012345") → False

# Format values
format_duration(123.45) → "2m 3s"
format_datetime(datetime.now()) → "2026-07-03 10:30:45"
```

### 4. Data Models (models.py)

**Key Classes:**

- `Workbook` - Represents an Excel workbook
- `ValidationResult` - Contains validation outcomes
- `DuplicateRecord` - Duplicate batch number details
- `ValidationError` - Validation error details
- `CardStatistics` - Card counting totals
- `ValidationStep` - Individual validation step
- `ValidationSummary` - Summary statistics

## Usage Examples

### Example 1: Validate a Workbook

```python
from src.core.validation_engine import ValidationEngine

# Create engine
engine = ValidationEngine()

# Validate
result = engine.validate_complete_workbook("daily_output.xlsx")

# Check results
if result.passed:
    print("✓ Validation PASSED")
else:
    print("✗ Validation FAILED")
    for error in result.errors:
        print(f"  • {error}")

# Get duplicates
duplicates = engine.get_duplicates()
for dup in duplicates:
    print(f"Duplicate: {dup.batch_number} in row {dup.row_number}")
```

### Example 2: Generate Sample Data

```python
from src.core.sample_workbook_generator import generate_sample_workbooks

# Generate valid and invalid sample workbooks
generate_sample_workbooks()
```

### Example 3: Run Validation Example

```bash
cd src/core
python validation_example.py
```

## Validation Output

### ValidationResult Structure

```python
{
    'passed': bool,                  # Overall pass/fail
    'error_count': int,              # Total errors
    'warning_count': int,            # Total warnings
    'duration_seconds': float,       # Validation time
    'errors': [str],                 # Error messages
    'warnings': [str],               # Warning messages
    'duplicates_found': int,         # Number of duplicates
    'steps': [ValidationStep],       # Completed steps
    'timestamp': datetime            # When validation ran
}
```

### Error Messages

Errors include detailed information:

```
Example errors:
• Missing required headers: No_of_Batches, Bag_No
• Duplicate batch number '10001' found in 2 rows
• Row 5: No_of_Batches mismatch. Expected 3, found 2
• Row 10: Invalid Bag_No format '00012345'. Must start with apostrophe
• Row 7: Blank field 'Branch_Code'
```

### Duplicate Records

Duplicates include:

```python
{
    'batch_number': str,             # The duplicate batch
    'worksheet': str,                # Sheet name
    'row_number': int,               # Row where found
    'cell_reference': str,           # Cell reference
    'occurrences': int,              # Number of times found
    'duplicate_type': str            # 'Same Cell' or 'Different Rows'
}
```

## Error Handling

The engine handles:
- Missing or inaccessible files
- Invalid Excel files
- Missing worksheets
- Missing headers
- Malformed data
- Permission errors

All errors are logged and returned in the ValidationResult.

## Performance

- Supports workbooks with 50,000+ rows
- Validates in under 60 seconds typically
- Memory efficient with openpyxl
- Handles large batch numbers efficiently

## Architecture

```
Application
    ↓
Dashboard
    ↓
ValidationEngine
    ├─ WorkbookLoader (openpyxl)
    ├─ HeaderValidator
    ├─ DuplicateChecker
    ├─ BatchValidator
    ├─ BagValidator
    └─ BlankFieldValidator
    ↓
ValidationResult
    ├─ Errors
    ├─ Warnings
    ├─ Duplicates
    └─ Timestamps
```

## Testing

### Test Valid Workbook

```bash
python src/core/validation_example.py
# Should find no errors
```

### Test Invalid Workbook

```python
from src.core.validation_engine import ValidationEngine

engine = ValidationEngine()
result = engine.validate_complete_workbook("sample_invalid.xlsx")

# Should find:
# - Blank fields
# - Duplicate batches
# - Batch count mismatches
# - Invalid bag numbers
```

## Integration with Other Modules

### With Audit Manager
```python
from src.core.audit_manager import AuditManager

audit = AuditManager()
# Log validation results
audit.log_action(
    action="Workbook Validated",
    user="user@example.com",
    result="Success" if result.passed else "Failed",
    description=f"Errors: {result.error_count}"
)
```

### With Card Counter
```python
from src.core.card_counter import CardCounter

counter = CardCounter()
# After validation passes, count cards
stats = counter.count_cards(workbook)
```

### With Report Generator
```python
from src.core.report_generator import ReportGenerator

reporter = ReportGenerator()
# Generate PDF report with validation results
reporter.generate_validation_report(workbook, result)
```

## Future Enhancements

1. **Parallel Validation** - Validate multiple sheets simultaneously
2. **Custom Rules** - Allow users to define custom validation rules
3. **Incremental Validation** - Only validate changed rows
4. **Performance Optimization** - Cache frequently accessed data
5. **Multi-language Support** - Localize error messages
6. **Advanced Reporting** - Generate detailed HTML reports
7. **Real-time Validation** - Validate as user enters data

## Files

| File | Purpose |
|------|---------|
| `workbook_loader.py` | Excel file loading and access |
| `validation_engine.py` | Main validation orchestration |
| `validation_example.py` | Usage examples and demonstration |
| `sample_workbook_generator.py` | Generate test data |
| `helpers.py` | Utility functions |
| `models.py` | Data models and dataclasses |

## Logging

All validation operations are logged. Check logs at:
```
logs/cdrs.log
```

Log levels:
- DEBUG: Detailed validation steps
- INFO: Workbook loaded, validation started/completed
- WARNING: Validation errors found
- ERROR: System errors

## Summary

The Validation Engine provides a robust, production-ready system for validating Excel workbooks against all business rules. It's designed for:

✓ Correctness - Implements all specified business rules
✓ Performance - Handles large workbooks efficiently
✓ Reliability - Comprehensive error handling
✓ Maintainability - Modular, well-documented code
✓ Extensibility - Easy to add new validation rules
✓ Usability - Simple, intuitive API
