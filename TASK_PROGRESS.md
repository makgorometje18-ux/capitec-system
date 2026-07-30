# Task: Remove Settings table abuse for ROWS_PROCESSED

## Current Problem
The `rows_processed` metric is stored only in the in-memory `validation_progress` dict, which
is ephemeral (lost on server restart). It must be persisted in the database alongside the
validation run record.

## Implementation Plan
- [ ] Add `RowsProcessed` column to ValidationRun table (schema + migration)
- [ ] Update validation upload to store rows_processed in ValidationRun table
- [ ] Update dashboard API to read rows_processed from ValidationRun table
- [ ] Update dashboard.js to handle the persisted value
- [ ] Verify no Settings table is used for rows_processed
- [ ] Clean up temp files