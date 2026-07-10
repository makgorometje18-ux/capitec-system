# Capitec Daily Reconciliation System (CDRS)

# 04 - Excel Workbook Specification

Version: 1.0

---

# 1. Purpose

This document defines the Excel workbook structure used by the Capitec Daily Reconciliation System (CDRS).

The application shall automatically detect, validate, reconcile and update the workbook according to the rules defined in this specification.

---

# 2. Workbook Format

Supported formats

- .xlsx
- .xlsm (future support)

Unsupported

- CSV
- XLS
- Password protected workbooks

---

# 3. Workbook Structure

Each workbook shall contain the following worksheets.

## Worksheet 1

DAILY OUTPUT FILE DD-MM-YYYY

Example

DAILY OUTPUT FILE 30-06-2026

This worksheet contains all production transactions.

---

## Worksheet 2

CAPITEC SUMMARY FILE REPORT

Contains

- Stock on Hand
- Quantity Received
- Quantity Dispatched
- Remaining Stock

---

# 4. Worksheet Detection

The system shall search every worksheet.

If worksheet name starts with

DAILY OUTPUT FILE

↓

Mark as Daily Output Worksheet.

If worksheet starts with

CAPITEC SUMMARY FILE REPORT

↓

Mark as Summary Worksheet.

Dates must never be hardcoded.

---

# 5. Daily Output Worksheet Layout

| Column | Header | Required | Description |
|---------|----------|----------|-------------|
| B | Creation_Date | Yes | Production Year |
| C | Branch_Code | Yes | Branch Number |
| D | Branch_Name | Yes | Branch Name |
| E | Card_Type | Yes | SIM or DMCCLS |
| F | No_of_Batches | Yes | Number of Orders |
| G | Waybill_No | Yes | Shipment Waybill |
| H | Batch_No | Yes | Batch Numbers |
| I | Bag_No | Yes | Bag Number |

---

# 6. Column Specifications

## Creation_Date

Type

Integer

Required

Yes

Example

2026

Validation

Cannot be blank.

---

## Branch_Code

Type

Numeric

Example

4052

Validation

Cannot be blank.

---

## Branch_Name

Type

Text

Validation

Cannot be blank.

---

## Card_Type

Allowed values

SIM

DMCCLS

Everything else

FAIL

---

## No_of_Batches

Type

Integer

Minimum

1

Validation

Must equal number of Batch_No values.

---

## Waybill_No

Type

Text

Example

Y8NZT00001158

Validation

Cannot be blank.

---

## Batch_No

Contains one or more values separated by "|"

Example

0205910|0205837|0205912

Rules

No duplicates

Numeric only

Ignore spaces

Ignore empty separators

---

## Bag_No

Example

'000166980

Rules

Exactly one leading apostrophe

Multiple apostrophes are invalid

---

# 7. Summary Worksheet Layout

The system shall automatically locate the following records.

Bank Cards

Row beginning with

P_

Example

P_974868_20250613.out

SIM Cards

Rows beginning with

C-Connect

Example

C-Connect batch 1

C-Connect batch 2

---

# 8. Summary Columns

The following fields are updated automatically.

Quantity Received

Read only

Quantity In Stock

Updated

Quantity Dispatched

Updated

Comments

Read only

---

# 9. Workbook Validation

Before processing the workbook the application shall verify

Required worksheets exist

Required headers exist

Workbook is not protected

Workbook is not corrupted

Workbook is not read-only

If any validation fails

↓

Stop processing.

---

# 10. Data Relationships

Card_Type

↓

Determines multiplier.

SIM

↓

Orders × 200

DMCCLS

↓

Orders × 300

---

No_of_Batches

↓

Determines expected Batch_No count.

---

Batch_No

↓

Determines duplicate validation.

---

Bag_No

↓

Determines bag validation.

---

# 11. Processing Sequence

1.

Open Workbook

↓

2.

Create Backup

↓

3.

Locate Worksheets

↓

4.

Locate Headers

↓

5.

Read Rows

↓

6.

Validate Data

↓

7.

Highlight Errors

↓

8.

Generate Duplicate Report

↓

9.

Calculate Cards

↓

10.

Update Summary Sheet

↓

11.

Save Workbook

↓

12.

Generate Audit Log

↓

13.

Generate PDF Report

↓

14.

Display PASS / FAIL

---

# 12. Error Handling

Missing worksheet

↓

Stop

Missing headers

↓

Stop

Duplicate Batch

↓

Continue validation

Highlight error

Batch count mismatch

↓

Continue validation

Highlight error

Bag format error

↓

Offer Auto Fix

---

# 13. Performance Requirements

Support

50,000+

rows

Workbook loading

<10 seconds

Validation

<60 seconds

Summary update

<5 seconds

---

# 14. Future Workbook Support

Future versions shall support

Automatic folder monitoring

Multiple Daily Output worksheets

Multiple Summary worksheets

Barcode scanner integration

Cloud workbook storage

SharePoint integration

---

# 15. Acceptance Criteria

The system shall

✓ Detect workbook automatically

✓ Detect worksheets automatically

✓ Detect headers automatically

✓ Validate every row

✓ Preserve workbook formatting

✓ Highlight validation failures

✓ Update summary correctly

✓ Generate reports successfully

✓ Complete processing without manual intervention

---

End of Document