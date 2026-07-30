# Capitec Daily Reconciliation System
## ID Patterns and Field Names Guide

### Purpose
This document defines all identifier schemes and field naming conventions used throughout the CDRS platform. It ensures consistency across all modules, databases, APIs, and integrations.

---

## Table of Contents
1. [Architectural Patterns](#architectural-patterns)
2. [Domain Standards](#domain-standards)
3. [Field Naming Conventions](#field-naming-conventions)
4. [Implementation Rules](#implementation-rules)
5. [Existing Macro Patterns](#existing-macro-patterns)
6. [Usage Across Modules](#usage-across-modules)

---

## Architectural Patterns

### Primary ID Format: `UID_'WTS'+4Digits`

All macro-generated records use the unified pattern:

```
UID_WTS####  (e.g., UID_WTS1001, UID_WTS2458)
```

**Structure:**
| Component | Value | Description |
|-----------|-------|-------------|
| Prefix | `UID_` | Universal identifier namespace |
| Entity Code | `WTS` | Workbook/Template/System entity |
| Sequence | `####` | 4-digit zero-padded sequence (0001-9999) |

**Examples:**
- `UID_WTS0001` — First workbook
- `UID_WTS1001` — Workbook #1001
- `UID_WTS2458` — Workbook #2458

### Scope
This pattern applies to:
- Workbook registrations
- Template definitions
- Validation runs
- Batch processing jobs
- Report generations
- System configurations

---

## Domain Standards

### 1. Workbooks
| Pattern | Example | Scope |
|---------|---------|-------|
| `UID_WTS####` | `UID_WTS1001` | Primary workbook identifier |

**Database Field:** `WorkbookID` (INTEGER PRIMARY KEY)

### 2. Templates
| Pattern | Example | Scope |
|---------|---------|-------|
| `UID_WTS####` | `UID_WTS0050` | Template definition |

**Database Field:** `TemplateID` (INTEGER PRIMARY KEY)

### 3. Validation Runs
| Pattern | Example | Scope |
|---------|---------|-------|
| `UID_WTS####` | `UID_WTS1001` | Links to parent workbook |

**Database Field:** `RunID` (INTEGER PRIMARY KEY)

---

## Field Naming Conventions

### Standard Fields (All Tables)

| Field Name | Type | Description |
|------------|------|-------------|
| `ID` | INTEGER | Auto-increment primary key |
| `CreatedAt` | TEXT (ISO8601) | Record creation timestamp |
| `UpdatedAt` | TEXT (ISO8601) | Last modification timestamp |
| `CreatedBy` | TEXT | User/system that created record |
| `Status` | TEXT | Current status (ACTIVE, INACTIVE, DELETED) |

### Workbook Field Specifics

| Field Name | Type | Constraints | Description |
|------------|------|-------------|-------------|
| `WorkbookID` | INTEGER | PK, UNIQUE | `UID_WTS####` format |
| `FileName` | TEXT(255) | NOT NULL | Original filename |
| `FilePath` | TEXT(500) | NOT NULL | Full system path |
| `FileHash` | TEXT(64) | NOT NULL | SHA-256 checksum |
| `FileSize` | INTEGER | > 0 | Bytes |
| `SheetCount` | INTEGER | >= 1 | Number of worksheets |
| `ProcessDate` | DATETIME | NOT NULL | Processing timestamp |

### Template Field Specifics

| Field Name | Type | Constraints | Description |
|------------|------|-------------|-------------|
| `TemplateID` | INTEGER | PK, UNIQUE | `UID_WTS####` format |
| `TemplateName` | TEXT(100) | NOT NULL | Human-readable name |
| `TemplateVersion` | TEXT(20) | NOT NULL | Semver string |
| `DefinitionJSON` | JSON/TEXT | NOT NULL | Template structure |
| `ActiveFlag` | BOOLEAN | DEFAULT TRUE | Soft delete flag |

---

## Implementation Rules

### ID Generation

1. **Sequential Assignment**
   - IDs assigned in order of creation
   - Never reuse deleted IDs
   - Gap-tolerant sequence

2. **Format Enforcement**
   ```python
   def generate_workbook_id(sequence: int) -> str:
       """Generate UID_WTS#### formatted identifier"""
       return f"UID_WTS{sequence:04d}"
   ```

3. **Validation Regex**
   ```
   ^UID_WTS\d{4}$
   ```

### Timestamp Standards

All timestamps use ISO 8601 format:
```
YYYY-MM-DDTHH:MM:SS.sssZ
```

Examples:
- `2026-07-23T10:30:00.000Z` — UTC
- `2026-07-23T10:30:00+02:00` — SAST

---

## Existing Macro Patterns Used

Current VBA macros reference these ID patterns:

| Pattern | Usage | Example |
|---------|-------|---------|
| `UID_WTS####` | Workbook identification | `UID_WTS1001` |
| `TMP_####` | Template references | `TMP_0001` |
| `RPT_YYYYMMDD` | Daily reports | `RPT_20260723` |

**Integration Note:** The `UID_WTS####` pattern is the master identifier. Other patterns are aliases or subsets.

---

## Usage Across Modules

### Validation Engine
```python
# Input
workbook_id = "UID_WTS1001"
run_id = "UID_WTS1001_R01"  # Append run sequence

# Database
cursor.execute("SELECT * FROM ValidationRun WHERE WorkbookID = ?", (workbook_id,))
```

### Backup Manager
```python
# File naming
backup_name = f"{workbook_id}_20260723_103000.bak"
# Result: UID_WTS1001_20260723_103000.bak
```

### Audit Logging
```python
# Log entry
audit_record = {
    "WorkbookID": "UID_WTS1001",
    "Action": "VALIDATION_RUN",
    "Timestamp": "2026-07-23T10:30:00Z"
}
```

---

## Migration Guide

### Converting Existing Data

If existing records use different ID formats:

```sql
-- Example: Convert numeric IDs to UID_WTS####
UPDATE WorkbookHistory
SET WorkbookID = 'UID_WTS' || printf('%04d', ID)
WHERE WorkbookID NOT LIKE 'UID_WTS%';
```

### Backward Compatibility

Old identifiers remain valid in:
- Historical audit logs
- Backup file names
- External references

New records only use `UID_WTS####` format.

---

## Validation Checklist

When implementing new features:

- [ ] All new workbooks use `UID_WTS####` format
- [ ] Database schemas enforce UNIQUE constraints
- [ ] Timestamps use ISO 8601 format
- [ ] Field names follow snake_case convention
- [ ] ID validation regex is applied at input layer
- [ ] Migration scripts preserve existing references

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-23 | CDRS Team | Initial release — unified ID pattern |

**Next Review:** 2026-08-23