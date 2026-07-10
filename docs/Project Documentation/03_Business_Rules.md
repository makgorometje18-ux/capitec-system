# 03 Business Rules

## BR-001 Worksheet Detection
- Detect DAILY OUTPUT FILE sheet
- Detect CAPITEC SUMMARY FILE REPORT sheet

## BR-002 Required Headers
Creation_Date, Branch_Code, Branch_Name, Card_Type, No_of_Batches, Waybill_No, Batch_No, Bag_No.

## BR-003 Duplicate Batch Numbers
- Detect duplicates inside the same Batch_No cell.
- Detect duplicates across all rows.
- Report Batch Number, Worksheet, Row, Cell and Occurrences.
- Highlight affected rows red.

## BR-004 Batch Parsing
Split Batch_No by '|', trim spaces and ignore empty values.

## BR-005 No_of_Batches
Compare No_of_Batches with the number of values found in Batch_No.

## BR-006 Batch Format
Batch numbers must be numeric only.

## BR-007 Bag_No
Accept one leading apostrophe only. Auto-fix multiple apostrophes.

## BR-008 Mandatory Fields
Branch_Code, Branch_Name, Card_Type, No_of_Batches, Waybill_No, Batch_No and Bag_No cannot be blank.

## BR-009 Card Types
Only SIM and DMCCLS are valid.

## BR-010 Card Calculations
SIM = Orders x 200.
DMCCLS = Orders x 300.

## BR-011 Summary Update
Update summary only if every validation passes.

## BR-012 Backup
Create a timestamped backup before making changes.

## BR-013 Duplicate Report
Create a worksheet named Duplicate Report listing every duplicate.

## BR-014 Audit Log
Record workbook, date, time, validation result, errors, warnings and update status.

## BR-015 PASS/FAIL
PASS only when all business rules pass. Otherwise FAIL.
