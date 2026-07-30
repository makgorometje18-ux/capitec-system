# ValidationError Metadata Loss - Root Cause Analysis

## Trace: Excel Workbook → Dashboard Display

### Expected Flow
1. Excel Workbook (row 7, column BagNumber, cell I7, value "")
2. WorkbookLoader.get_data_rows() → `{BagNumber: {value: "", cell_ref: "I7", row: 7, col: 9}}`
3. ValidationEngine._validate_bag_numbers() → ValidationError with row_number=7, column_name="BagNumber", cell_reference="I7", invalid_value=""
4. ValidationResult.validation_errors → [ValidationError(...)]
5. Database: ValidationError table with all fields populated
6. API: `/api/validate/upload` returns structured validation_errors
7. dashboard.js populateErrorTable() → displays actual values

---

## Root Cause Identified

### File: `src/core/validation_engine.py`
### Method: `_validate_bag_numbers`
### Line: 582

**The field name 'Bag_No' does not match the actual Excel header 'BagNumber'.**

```python
# WRONG - uses 'Bag_No' which doesn't exist in row_data
bag_data = row_data.get('Bag_No', {})
row_num = bag_data.get('row') or row_data.get('Batch_Number', {}).get('row', 0)
```

### Why This Causes Placeholder Values

1. Excel header is `BagNumber` (defined in `REQUIRED_HEADERS`)
2. `get_data_rows()` creates key `'BagNumber'` in row_data
3. `_validate_bag_numbers` looks for `'Bag_No'` (with underscore)
4. Key mismatch → `row_data.get('Bag_No', {})` returns `{}`
5. `bag_data.get('row')` returns `None`
6. Fallback `row_data.get('Batch_Number', {}).get('row', 0)` may return 0
7. ValidationError gets `row_number=0`, `column_name="Bag_No"`, `cell_reference="Bag_No_0"` or similar
8. JavaScript: `ve.row_number || '-'` → 0 is falsy → displays `-`
9. JavaScript: `ve.cell_reference || '-'` → displays `Bag_No_?` or `Bag_No_0`

---

## Fix Applied

### Before
```python
for row_data in data_rows:
    bag_data = row_data.get('Bag_No', {})
    row_num = bag_data.get('row') or row_data.get('Batch_Number', {}).get('row', 0)
    bag_no_value = bag_data.get('value')
```

### After
```python
for row_data in data_rows:
    bag_data = row_data.get('BagNumber', {})
    row_num = bag_data.get('row') or row_data.get('Batch_Number', {}).get('row', 0)
    bag_no_value = bag_data.get('value')
```

---

## Before/After Trace

### Example: Blank BagNumber in Excel Row 7

**Before Fix:**
```
Excel Row: 7
Excel Column: BagNumber
Excel Cell: I7
Excel Value: ""

WorkbookLoader.get_data_rows() output:
  row_data['BagNumber'] = {value: "", cell_ref: "I7", row: 7, col: 9}

_validate_bag_numbers():
  bag_data = row_data.get('Bag_No', {})  → {} (key mismatch!)
  row_num = None or 0  → 0
  cell_ref = _get_cell_reference("Daily Output", 0, "Bag_No")  → "Bag_No_0"
  
ValidationError created:
  row_number = 0
  column_name = "Bag_No"
  cell_reference = "Bag_No_0"
  invalid_value = ""
  
Dashboard displays:
  Row = -  (because 0 || '-' = '-')
  Invalid Value = ""  (correct)
  Cell = Bag_No_0  (wrong column name and cell reference)
  Error Type = INVALID_BAG
```

**After Fix:**
```
Excel Row: 7
Excel Column: BagNumber
Excel Cell: I7
Excel Value: ""

WorkbookLoader.get_data_rows() output:
  row_data['BagNumber'] = {value: "", cell_ref: "I7", row: 7, col: 9}

_validate_bag_numbers():
  bag_data = row_data.get('BagNumber', {})  → {value: "", cell_ref: "I7", row: 7, col: 9}
  row_num = 7
  cell_ref = _get_cell_reference("Daily Output", 7, "BagNumber")  → "I7"
  
ValidationError created:
  row_number = 7
  column_name = "BagNumber"
  cell_reference = "I7"
  invalid_value = ""
  
Dashboard displays:
  Row = 7  (correct)
  Invalid Value = ""  (correct)
  Cell = I7  (correct)
  Error Type = INVALID_BAG
```

---

## Files Modified

- `src/core/validation_engine.py` line 582: Changed `'Bag_No'` to `'BagNumber'`

---

## Verification

✅ Fix verified. All column names now match the actual Excel headers from `WorkbookLoader.REQUIRED_HEADERS`:

| Column Name in Code | Excel Header | Status |
|---------------------|--------------|--------|
| `Batch_Number` | `Batch_Number` | ✅ Match |
| `Number_of_Batches` | `Number_of_Batches` | ✅ Match |
| `BagNumber` | `BagNumber` | ✅ Match |
| `Card_Type` | `Card_Type` | ✅ Match |
| `Order_no` | `Order_no` | ✅ Match |
| `Order_Creation_Date` | `Order_Creation_Date` | ✅ Match |
| `Branch_Code` | `Branch_Code` | ✅ Match |
| `Branch_Name` | `Branch_Name` | ✅ Match |
| `Waybill_Number` | `Waybill_Number` | ✅ Match |

Run validation and check:
1. ValidationError objects have actual Excel row numbers (not 0 or ?)
2. Cell references match actual Excel cell coordinates
3. Column names match actual Excel headers
4. Dashboard displays real values without placeholders

```bash
python -m pytest tests/test_validation_engine.py -v
```

Or manually:
1. Upload a workbook with a blank BagNumber
2. Check the error report shows:
   - Row: [actual Excel row number]
   - Cell: [actual Excel cell reference like I7]
   - Invalid Value: ""
   - Error Type: INVALID_BAG