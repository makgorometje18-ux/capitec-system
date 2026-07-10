"""
Reconciliation Engine - Implements Phase 3 business logic and reconciliation.

Responsibilities:
- Workbook detection (find all DAILY OUTPUT FILE sheets and select newest)
- Card counting (SIM / Bank calculations)
- Summary Report updates (bank and SIM updates)
- Reconciliation history logging to DB
- Transaction safety via BackupManager and Database
"""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import shutil

from src.core.workbook_loader import WorkbookLoader
from src.core.card_counter import CardCounter
from src.core.backup_manager import BackupManager
from src.core.validation_engine import ValidationEngine
from src.database.database import get_database
from src.models.models import CardStatistics
from src.utils.logger import get_logger
from src.utils.helpers import clean_string

logger = get_logger()

CARD_QUANTITY_RULES = {
    'DMCCLS': 300,
    'SIM': 100,
}

MISMATCH_FIELDS = ['card_type']


def _normalize_value(value: Optional[Any]) -> str:
    if value is None:
        return ''
    return str(value).strip()


def _field_mismatch(field: str, commercial: Any, daily: Any) -> Optional[str]:
    if not hasattr(commercial, field) or not hasattr(daily, field):
        return None

    commercial_value = _normalize_value(getattr(commercial, field, None))
    daily_value = _normalize_value(getattr(daily, field, None))
    if commercial_value == '' and daily_value == '':
        return None
    if commercial_value != daily_value:
        return f"{field} mismatch: commercial='{commercial_value}' daily='{daily_value}'"
    return None


@dataclass
class BatchResult:
    batch_number: str
    status: str
    issues: List[str]


@dataclass
class ReconciliationAnalysis:
    matched: List[BatchResult]
    missing: List[BatchResult]
    extra: List[BatchResult]
    duplicates: List[BatchResult]
    mismatches: List[BatchResult]


class ReconciliationEngine:
    def __init__(self) -> None:
        self.logger = get_logger()
        self.loader = WorkbookLoader()
        self.card_counter = CardCounter()
        self.backup_manager = BackupManager()
        self.validator = ValidationEngine()
        self.db = get_database()

    def load_workbook(self, file_path: str) -> bool:
        wb = self.loader.load_workbook(file_path)
        return wb is not None

    def list_daily_output_sheets(self) -> List[Tuple[str, Optional[datetime]]]:
        """Return list of (sheet_name, parsed_date_or_none) for sheets starting with prefix."""
        if not self.loader.workbook:
            return []
        return self.loader.list_daily_output_sheets()

    def select_active_sheet(self) -> Optional[str]:
        """Select the newest Daily Output sheet (by parsed date)."""
        sheets = self.list_daily_output_sheets()
        if not sheets:
            return None
        return sheets[-1][0]

    def _classify_card_type(self, card_type_value: str) -> str:
        normalized = clean_string(str(card_type_value)).upper()
        if normalized == 'SIM':
            return 'SIM'
        if normalized == 'DMCCLS':
            return 'BANK'
        return 'UNKNOWN'

    def compute_card_statistics(self, active_sheet: str) -> CardStatistics:
        """Compute SIM and Bank card statistics from the active sheet."""
        stats = CardStatistics()
        try:
            rows = self.loader.get_data_rows(active_sheet)
            if not rows:
                return stats

            sim_orders = 0
            bank_orders = 0
            distinct_types: Dict[str, int] = {}

            for row in rows:
                raw_card_type = row.get('Card_Type', {}).get('value') or ''
                card_type = str(raw_card_type).strip().upper()
                no_of_batches = row.get('No_of_Batches', {}).get('value')
                try:
                    orders = int(no_of_batches)
                except Exception:
                    if no_of_batches is None or str(no_of_batches).strip() == '':
                        orders = 0
                    else:
                        self.logger.warning(
                            "Invalid No_of_Batches '%s' on row %s; treating as 0",
                            no_of_batches,
                            row.get('No_of_Batches', {}).get('row')
                        )
                        orders = 0

                distinct_types[card_type] = distinct_types.get(card_type, 0) + 1
                if card_type == 'SIM':
                    sim_orders += orders
                elif card_type == 'DMCCLS':
                    bank_orders += orders
                else:
                    self.logger.warning(
                        "Unrecognized Card_Type '%s' on row %s; ignoring for summary counts",
                        raw_card_type,
                        row.get('Card_Type', {}).get('row')
                    )

            stats.sim_orders = sim_orders
            # Use CardCounter implementation (configurable multipliers)
            stats.sim_cards = self.card_counter.calculate_sim_cards(sim_orders)
            stats.bank_orders = bank_orders
            stats.bank_cards = self.card_counter.calculate_bank_cards(bank_orders)
            stats.total_orders = stats.sim_orders + stats.bank_orders
            stats.total_cards = stats.sim_cards + stats.bank_cards

            self.logger.info("SIM Orders count: %d", stats.sim_orders)
            self.logger.info("Bank Orders count: %d", stats.bank_orders)
            # Log totals per request
            self.logger.info("Total SIM Orders (sum of No_of_Batches): %d", stats.sim_orders)
            self.logger.info("Total Bank Orders (sum of No_of_Batches): %d", stats.bank_orders)

            self.logger.info("Distinct Card_Type values found: %s", distinct_types)
            self.logger.info("Card_Type classifications: %s", {
                card_type: 'SIM' if card_type == 'SIM' else 'DMCCLS' if card_type == 'DMCCLS' else 'UNKNOWN'
                for card_type in distinct_types
            })

            return stats

        except Exception as e:
            self.logger.error(f"Error computing card statistics: {e}")
            return stats

    def update_summary_report(self, active_sheet: str, stats: CardStatistics) -> Tuple[bool, List[str]]:
        """Update the CAPITEC SUMMARY FILE REPORT worksheet.

        Returns (success, messages).
        """
        messages = []
        try:
            summary_sheet = self.loader.detect_capitec_summary_sheet()
            if not summary_sheet:
                msg = "Capitec Summary sheet not found"
                self.logger.warning(msg)
                messages.append(msg)
                return False, messages

            ws = self.loader.get_worksheet(summary_sheet)
            if not ws:
                messages.append("Failed to access summary worksheet")
                return False, messages

            # Find headers from first row
            headers = self.loader.get_headers(summary_sheet)
            if not headers:
                messages.append("Summary headers not found")
                return False, messages

            # Map header names to column indices
            header_map = {h: idx + 1 for idx, h in enumerate(headers) if h}

            # Columns of interest (if present)
            col_files = header_map.get('Files received')
            col_total_qty = header_map.get('Total quantity received')
            col_qty_in_stock = header_map.get('Quantity in stock')
            col_qty_dispatched = header_map.get('Quantity dispatched')

            # Update bank lines: for each unique waybill in active_sheet, find matching row
            data_rows = self.loader.get_data_rows(active_sheet)
            if not data_rows:
                messages.append("No data rows in active sheet")
                return False, messages

            # Build waybill sums
            waybill_sums = {}
            for row in data_rows:
                wb_no = row.get('Waybill_No', {}).get('value')
                card_type = clean_string(str(row.get('Card_Type', {}).get('value') or ''))
                no_of_batches = row.get('No_of_Batches', {}).get('value')
                try:
                    orders = int(no_of_batches)
                except Exception:
                    orders = 0

                if card_type == 'DMCCLS':
                    waybill_sums.setdefault(wb_no, 0)
                    waybill_sums[wb_no] += self.card_counter.calculate_bank_cards(orders)

            # For each waybill, search summary sheet for matching cell
            for waybill, cards in waybill_sums.items():
                if waybill is None:
                    continue
                found = False
                for r in ws.iter_rows(min_row=2):
                    for cidx, cell in enumerate(r, start=1):
                        if cell.value == waybill:
                            # Found matching row; update Quantity dispatched and Quantity in stock if columns exist
                            row_idx = cell.row
                            prev_disp = None
                            prev_stock = None
                            if col_qty_dispatched:
                                prev_disp_cell = ws.cell(row=row_idx, column=col_qty_dispatched)
                                prev_disp = int(prev_disp_cell.value or 0)
                                new_disp = prev_disp + cards
                                prev_disp_cell.value = new_disp
                            if col_qty_in_stock:
                                prev_stock_cell = ws.cell(row=row_idx, column=col_qty_in_stock)
                                prev_stock = int(prev_stock_cell.value or 0)
                                new_stock = prev_stock - cards
                                if new_stock < 0:
                                    msg = f"Negative stock would occur for waybill {waybill}; aborting update"
                                    self.logger.error(msg)
                                    return False, [msg]
                                prev_stock_cell.value = new_stock

                            # Record SummaryUpdate in DB
                            try:
                                self.db.insert('SummaryUpdate', {
                                    'RunID': 0,
                                    'ItemName': str(waybill),
                                    'PreviousDispatch': prev_disp if prev_disp is not None else 0,
                                    'NewDispatch': prev_disp + cards if prev_disp is not None else cards,
                                    'PreviousStock': prev_stock if prev_stock is not None else 0,
                                    'NewStock': (prev_stock - cards) if prev_stock is not None else 0,
                                    'UpdatedTime': datetime.now().isoformat()
                                })
                            except Exception:
                                # Non-fatal for DB write
                                pass

                            messages.append(f"Updated waybill {waybill}: +{cards} dispatched")
                            found = True
                            break
                    if found:
                        break

            # SIM updates: find all rows in "Files received" column that start with "C-Connect"
            sim_cards = stats.sim_cards
            if sim_cards > 0:
                # Determine which column to scan for C-Connect items
                # First column is "Files received" or we scan the first column if not found
                files_col_idx = 1  # default to first column
                if header_map.get('Files received'):
                    files_col_idx = header_map['Files received']

                # Find all rows with C-Connect items
                candidates = []
                for r in ws.iter_rows(min_row=2):
                    if len(r) >= files_col_idx:
                        cell_value = r[files_col_idx - 1].value
                        if cell_value and str(cell_value).strip().startswith('C-Connect'):
                            candidates.append((r[files_col_idx - 1].row, r, str(cell_value).strip()))

                remaining = sim_cards
                for row_idx, row_cells, item_name in candidates:
                    # Quantity dispatched and Quantity in stock cols must exist
                    if not col_qty_dispatched or not col_qty_in_stock:
                        continue
                    disp_cell = ws.cell(row=row_idx, column=col_qty_dispatched)
                    stock_cell = ws.cell(row=row_idx, column=col_qty_in_stock)
                    prev_disp = int(disp_cell.value or 0)
                    prev_stock = int(stock_cell.value or 0)
                    if remaining <= 0:
                        messages.append(f"SIM update {item_name}: no dispatch needed")
                        continue
                    take = min(prev_stock, remaining)
                    if take <= 0:
                        messages.append(f"SIM update {item_name}: no stock available")
                        continue
                    disp_cell.value = prev_disp + take
                    stock_cell.value = prev_stock - take
                    remaining -= take
                    messages.append(f"SIM update {item_name}: dispatched +{take}")
                    # Log SummaryUpdate
                    try:
                        self.db.insert('SummaryUpdate', {
                            'RunID': 0,
                            'ItemName': item_name,
                            'PreviousDispatch': prev_disp,
                            'NewDispatch': prev_disp + take,
                            'PreviousStock': prev_stock,
                            'NewStock': prev_stock - take,
                            'UpdatedTime': datetime.now().isoformat()
                        })
                    except Exception:
                        pass

                if remaining > 0:
                    msg = f"Not enough SIM stock across C-Connect batches; {remaining} cards remain to allocate"
                    self.logger.error(msg)
                    return False, [msg]

            # Save workbook after updates
            try:
                self.loader.workbook.save(self.loader.current_file_path)
                messages.append("Summary workbook updated and saved")
            except Exception as e:
                self.logger.error(f"Failed to save updated workbook: {e}")
                return False, [str(e)]

            return True, messages

        except Exception as e:
            self.logger.error(f"Error updating summary report: {e}")
            return False, [str(e)]


def reconcile(commercial_batches, daily_output_records) -> ReconciliationAnalysis:
    commercial_map: Dict[str, Any] = {
        batch.batch_number: batch for batch in commercial_batches
    }

    daily_map: Dict[str, List[Any]] = {}
    for record in daily_output_records:
        batch_number = getattr(record, 'batch_number', None)
        if batch_number is None:
            continue
        daily_map.setdefault(batch_number, []).append(record)

    matched: List[BatchResult] = []
    missing: List[BatchResult] = []
    extra: List[BatchResult] = []
    duplicates: List[BatchResult] = []
    mismatches: List[BatchResult] = []

    for batch_number, records in daily_map.items():
        if len(records) > 1:
            duplicates.append(
                BatchResult(
                    batch_number=batch_number,
                    status='DUPLICATE',
                    issues=['duplicate daily output entries'],
                )
            )
            continue

        record = records[0]
        commercial = commercial_map.get(batch_number)
        if commercial is None:
            extra.append(
                BatchResult(
                    batch_number=batch_number,
                    status='EXTRA',
                    issues=[],
                )
            )
            continue

        issues: List[str] = []
        for field in MISMATCH_FIELDS:
            mismatch = _field_mismatch(field, commercial, record)
            if mismatch:
                issues.append(mismatch)

        card_type = _normalize_value(getattr(record, 'card_type', None)).upper()
        expected_quantity = CARD_QUANTITY_RULES.get(card_type)
        if expected_quantity is not None:
            commercial_quantity = getattr(commercial, 'quantity', None)
            if commercial_quantity != expected_quantity:
                issues.append(
                    f"quantity mismatch: commercial={commercial_quantity} expected={expected_quantity}"
                )

        if issues:
            mismatches.append(
                BatchResult(
                    batch_number=batch_number,
                    status='MISMATCH',
                    issues=issues,
                )
            )
        else:
            matched.append(
                BatchResult(
                    batch_number=batch_number,
                    status='MATCHED',
                    issues=[],
                )
            )

    for batch_number in commercial_map:
        if batch_number not in daily_map:
            missing.append(
                BatchResult(
                    batch_number=batch_number,
                    status='MISSING',
                    issues=[],
                )
            )

    logger.info(
        "Reconcile summary: total commercial batches=%d, total daily batches=%d, matched=%d, missing=%d, extra=%d, duplicates=%d, mismatches=%d",
        len(commercial_batches),
        len(daily_output_records),
        len(matched),
        len(missing),
        len(extra),
        len(duplicates),
        len(mismatches),
    )

    def _batch_sample(batch_results: List[BatchResult]) -> str:
        return ", ".join([result.batch_number for result in batch_results[:5]])

    logger.info("Matched batch samples: %s", _batch_sample(matched) or "None")
    logger.info("Missing batch samples: %s", _batch_sample(missing) or "None")
    logger.info("Extra batch samples: %s", _batch_sample(extra) or "None")
    logger.info("Duplicate batch samples: %s", _batch_sample(duplicates) or "None")
    logger.info("Mismatch batch samples: %s", _batch_sample(mismatches) or "None")

    return ReconciliationAnalysis(
        matched=matched,
        missing=missing,
        extra=extra,
        duplicates=duplicates,
        mismatches=mismatches,
    )

    def perform_reconciliation(self, file_path: str, user: Optional[str] = None, previous_folder: Optional[str] = None) -> dict:
        """High-level reconciliation flow.

        Returns a dict with validation result, stats, messages.
        """
        result = {
            'success': False,
            'messages': []
        }

        # Create backup
        try:
            self.loader.load_workbook(file_path)
        except Exception:
            pass

        if self.backup_manager.create_backup(self.loader.workbook if self.loader.workbook else Path(file_path)):
            result['messages'].append('Backup created')

        # Validate workbook
        validation = self.validator.validate_complete_workbook(file_path, previous_folder=previous_folder)
        result['validation'] = validation

        # If validation failed, do not proceed to update
        if not validation.passed:
            result['messages'].append('Validation failed; aborting summary update')
            return result

        # Select active sheet
        active = self.select_active_sheet()
        if not active:
            result['messages'].append('Active daily sheet not found')
            return result

        # Compute card stats
        stats = self.compute_card_statistics(active)
        result['stats'] = stats

        # Update summary
        ok, msgs = self.update_summary_report(active, stats)
        result['success'] = ok
        result['messages'].extend(msgs)

        # Record reconciliation history
        try:
            self.db.insert('ReconciliationHistory', {
                'Workbook': Path(file_path).name,
                'ActiveWorksheet': active,
                'Date': datetime.now().isoformat(),
                'SIMOrders': stats.sim_orders,
                'SIMCards': stats.sim_cards,
                'BankOrders': stats.bank_orders,
                'BankCards': stats.bank_cards,
                'PreviousStock': 0,
                'NewStock': 0,
                'ValidationResult': 'PASSED' if validation.passed else 'FAILED',
                'SummaryUpdated': 1 if ok else 0,
                'User': user or 'SYSTEM',
                'Timestamp': datetime.now().isoformat()
            })
        except Exception:
            pass

        return result
