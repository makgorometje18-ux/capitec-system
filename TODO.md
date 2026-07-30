# Capitec Reconciliation System - Web Dashboard Fixes (No UI Redesign)

## Step 1 — Analyze current state
- [x] Identify navigation + SPA switching issues
- [x] Identify duplicate JS implementations (`formatDate`, `displayValidationResults`)
- [x] Identify fake validation progress + validation/upload/result flow issues (flagged)
- [x] Identify chart duplication/memory-leak risk (flagged)
- [x] Identify auto-refresh performance issues (flagged)

## Step 2 — Navigation + JS production cleanup (now implementing)
- [ ] Update `web_dashboard/templates/index.html` navigation links:
  - [ ] Remove every `onclick="loadPage('...')"`
  - [ ] Add `data-page="..."` to every nav link
  - [ ] Ensure no navigation reloads (use `href="#"`)
- [ ] Update `web_dashboard/static/dashboard.js`:
  - [ ] Replace `setupNavigation()` logic to use ONLY `this.dataset.page`
  - [ ] Never parse/inspect `onclick`
  - [ ] Consolidate the two `DOMContentLoaded` listeners into one init routine
  - [ ] Remove duplicate function definitions:
    - [ ] keep only one `formatDate()`
    - [ ] keep only one `displayValidationResults()`
  - [ ] Ensure `initValidationWorkspace()` is called in the consolidated init

## Step 3 — Validation workflow correctness
- [ ] Fix upload flow issues:
  - [ ] drag & drop works
  - [ ] browse button works
  - [ ] file info panel updates
  - [ ] Validate button appears
  - [ ] upload uses `/api/validate/upload`
  - [ ] upload errors display correctly
  - [ ] no JS errors
- [ ] Fix validation results rendering:
  - [ ] Only one function displays validation results
  - [ ] Populate Passed/Failed/Warnings/Duplicates/Processing Time/Cards Processed/Error Count
  - [ ] Completion card + Error table

## Step 4 — Error table fixes
- [ ] Fix filtering (search, dropdown)
- [ ] Fix collapse behavior
- [ ] Fix sorting behavior
- [ ] Ensure clearing filters restores rows and removes “No matching errors” bug

## Step 5 — Dashboard performance + refresh policy
- [ ] Refresh KPI cards every 5s
- [ ] Refresh charts every 60s
- [ ] Audit loads only when opened
- [ ] Validation never refreshes while validation is running

## Step 6 — Chart.js lifecycle + memory safety
- [ ] Prevent duplicate chart creation
- [ ] Destroy chart before recreating if necessary

## Step 7 — Download buttons wiring
- [ ] Connect PDF/CSV/Highlighted Workbook/Audit Log/Duplicate Report to Flask routes
- [ ] Show success/error toasts

## Step 8 — API consistency + production cleanup
- [ ] Verify every frontend fetch matches Flask routes and JSON fields
- [ ] Remove dead code/unused vars/duplicate timers/listeners

## Step 9 — Verification (after code changes)
- [ ] No JS console errors
- [ ] No 404 API errors
- [ ] No navigation reloads
- [ ] Dashboard/Validation/Analytics/Audit/Settings/About all work end-to-end
