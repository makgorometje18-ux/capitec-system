from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.card_counter import CardCounter
from src.core.workbook_loader import WorkbookLoader
from src.models.models import SummaryAnalysis, SummaryDifference, SummaryRow
from src.utils.logger import get_logger


class SummaryReconciliationEngine:
    """
    Summary Reconciliation Engine - analysis-only phase.

    This class reads the workbook, locates the summary worksheet,
    identifies the newest Daily Output worksheet, computes card
    statistics, reads existing summary values, and prepares a
    structured analysis result for reconciliation.
    """

    ROW_TYPE_BANK_CARD = 'BANK_CARD'
    ROW_TYPE_SIM = 'SIM'
    ROW_TYPE_UNKNOWN = 'UNKNOWN'

    BANK_CARD_PREFIX = 'P_'
    SIM_PREFIX = 'C-Connect'

    def __init__(self) -> None:
        self.logger = get_logger()
        self.loader = WorkbookLoader()
        self.card_counter = CardCounter()

    def analyze(self, file_path: str) -> SummaryAnalysis:
        """
        Analyze the workbook and return a SummaryAnalysis object.

        Args:
            file_path: Path to the Excel workbook.

        Returns:
            SummaryAnalysis with the analysis results.
        """
        analysis = SummaryAnalysis(
            summary_worksheet_name=None,
            latest_daily_worksheet_name=None,
            validation_status=False
        )

        try:
            self.logger.info(f"Starting summary analysis for: {file_path}")
            workbook_model = self.loader.load_workbook(file_path)
            if not workbook_model:
                self.logger.error("Workbook load failed during summary analysis")
                return analysis

            summary_sheet = self.loader.detect_capitec_summary_sheet()
            analysis.summary_worksheet_name = summary_sheet
            if not summary_sheet:
                self.logger.error("CAPITEC SUMMARY FILE REPORT worksheet not found")
                return analysis

            daily_sheets = self.loader.list_daily_output_sheets()
            if not daily_sheets:
                self.logger.error("No DAILY OUTPUT FILE worksheets found")
                return analysis

            latest_daily_sheet = daily_sheets[-1][0]
            analysis.latest_daily_worksheet_name = latest_daily_sheet
            self.logger.info(f"Latest Daily Output worksheet: {latest_daily_sheet}")

            stats = self.card_counter.count_cards_from_loader(self.loader, latest_daily_sheet)
            analysis.sim_orders = stats.sim_orders
            analysis.sim_cards = stats.sim_cards
            analysis.dmcc_orders = stats.bank_orders
            analysis.dmcc_cards = stats.bank_cards
            analysis.total_orders = stats.total_orders
            analysis.total_cards = stats.total_cards
            self.logger.info(
                f"Calculated stats: SIM orders={stats.sim_orders}, SIM cards={stats.sim_cards}, "
                f"DMCCLS orders={stats.bank_orders}, DMCCLS cards={stats.bank_cards}, "
                f"Total orders={stats.total_orders}, Total cards={stats.total_cards}"
            )

            summary_rows = self._read_summary_rows(summary_sheet)
            for summary_row in summary_rows:
                summary_row.row_type = self._detect_row_type(summary_row.item_name)

            active_bank_row = self._select_active_inventory_row(summary_rows, self.ROW_TYPE_BANK_CARD)
            active_sim_row = self._select_active_inventory_row(summary_rows, self.ROW_TYPE_SIM)
            for summary_row in summary_rows:
                self._apply_row_calculations(
                    summary_row,
                    analysis.sim_cards,
                    analysis.dmcc_cards,
                    active_bank_row=active_bank_row,
                    active_sim_row=active_sim_row,
                )

            analysis.summary_rows = summary_rows
            analysis.files_received_rows = summary_rows
            analysis.bank_card_rows = [row for row in summary_rows if row.row_type == self.ROW_TYPE_BANK_CARD and row.changes_required]
            analysis.sim_rows = [row for row in summary_rows if row.row_type == self.ROW_TYPE_SIM and row.changes_required]
            analysis.cconnect_rows = [row for row in summary_rows if row.row_type == self.ROW_TYPE_SIM]
            analysis.existing_summary_values = {row.item_name: row.raw_values for row in summary_rows}
            analysis.current_summary_values = self._build_current_summary_values(summary_rows)
            # Keep calculated summary values available for compatibility, but
            # perform row-based comparison for preview/has_changes as the
            # authoritative source of truth.
            analysis.calculated_summary_values = {
                'SIM Orders': analysis.sim_orders,
                'SIM Cards': analysis.sim_cards,
                'DMCCLS Orders': analysis.dmcc_orders,
                'DMCCLS Cards': analysis.dmcc_cards,
                'Total Orders': analysis.total_orders,
                'Total Cards': analysis.total_cards,
            }

            # Build differences: include per-row differences (primary) and
            # append legacy metric diffs for backward compatibility.
            analysis.differences = self._build_summary_differences(analysis)

            # Derive has_changes and changes_count purely from SummaryRow.changes_required
            analysis.has_changes = any(row.changes_required for row in analysis.summary_rows)
            analysis.changes_count = sum(1 for row in analysis.summary_rows if row.changes_required)
            analysis.preview_ready = True
            analysis.validation_status = True

            self.logger.info(
                f"Summary preview ready: has_changes={analysis.has_changes}, changes_count={analysis.changes_count}"
            )
            return analysis

        except Exception as exc:
            self.logger.error(f"Summary analysis error: {exc}")
            return analysis

    def _normalize_header(self, header_value: Optional[Any]) -> str:
        return str(header_value).strip().lower() if header_value is not None else ''

    def _get_column(self, header_map: Dict[str, int], *aliases: str) -> Optional[int]:
        """Return first matching column index for any of the provided normalized aliases."""
        for alias in aliases:
            if alias in header_map:
                return header_map[alias]
        return None

    def _find_summary_header_row(self, worksheet) -> tuple[int, List[str]]:
        for row_idx, row in enumerate(worksheet.iter_rows(min_row=1, max_row=20, values_only=True), start=1):
            normalized_headers = [self._normalize_header(cell) for cell in row]
            if 'files received' in normalized_headers:
                headers = [str(cell).strip() if cell is not None else '' for cell in row]
                self.logger.info(f"Found summary header row at row {row_idx}")
                return row_idx, headers

        self.logger.warning("Summary header row not found; defaulting to first row")
        first_row = next(worksheet.iter_rows(min_row=1, max_row=1, values_only=True), ())
        headers = [str(cell).strip() if cell is not None else '' for cell in first_row]
        return 1, headers

    def _detect_row_type(self, item_name: str) -> str:
        normalized_name = str(item_name).strip()
        if normalized_name.upper().startswith(self.BANK_CARD_PREFIX):
            return self.ROW_TYPE_BANK_CARD
        if normalized_name.startswith(self.SIM_PREFIX):
            return self.ROW_TYPE_SIM
        return self.ROW_TYPE_UNKNOWN

    def _select_active_inventory_row(self, summary_rows: List[SummaryRow], row_type: str) -> Optional[SummaryRow]:
        candidates = [row for row in summary_rows if row.row_type == row_type]
        if not candidates:
            self.logger.info("Summary row diagnostics: no %s rows available for active selection", row_type)
            return None

        # Business rule for BANK_CARD (P_ rows) and SIM (C-Connect rows):
        # 1) Prefer the first row (in sheet order) where:
        #    - Quantity In Stock > 0
        #    - Quantity Dispatched > 0
        #    - Quantity Dispatched < Total Quantity Received
        # 2) For SIM rows only: if no row has Quantity Dispatched > 0, use
        #    the first SIM row with Quantity In Stock > 0.
        # Do NOT select based on the largest Quantity In Stock.

        # Find first qualifying row where dispatched is >0 and less than total received, and stock >0
        for row in candidates:
            if (row.quantity_in_stock or 0) > 0 and (row.quantity_dispatched or 0) > 0:
                # total_quantity_received may be None; treat None as unknown and allow selection
                if row.total_quantity_received is None:
                    self._log_active_inventory_row(
                        row_type=row_type,
                        row=row,
                        reason="selected first row with positive stock and dispatched (>0); total received unknown"
                    )
                    return row
                try:
                    if (row.quantity_dispatched or 0) < (row.total_quantity_received or 0):
                        self._log_active_inventory_row(
                            row_type=row_type,
                            row=row,
                            reason="selected first row with positive stock and dispatched >0 and dispatched < total received"
                        )
                        return row
                except Exception:
                    # Fallback: if comparison fails, skip this row
                    continue

        # If row_type is SIM, and no dispatched>0 row was found, pick first SIM row with stock>0
        if row_type == self.ROW_TYPE_SIM:
            for row in candidates:
                if (row.quantity_in_stock or 0) > 0:
                    self._log_active_inventory_row(
                        row_type=row_type,
                        row=row,
                        reason="no SIM row with dispatched>0 found; selected first row with positive stock"
                    )
                    return row

        # As a final fallback, choose the first candidate by row number (earliest in sheet)
        selected_row = min(candidates, key=lambda row: row.row_number)
        self._log_active_inventory_row(
            row_type=row_type,
            row=selected_row,
            reason="fallback: selected first available candidate by row number"
        )
        return selected_row

    def _log_active_inventory_row(self, row_type: str, row: Optional[SummaryRow], reason: str) -> None:
        if row is None:
            self.logger.info("Summary active row diagnostics: row_type=%s selected_row=None reason=%s", row_type, reason)
            return

        self.logger.info(
            "Summary active row diagnostics: row_type=%s selected_row_number=%s files_received=%s "
            "quantity_in_stock=%s quantity_dispatched=%s reason=%s",
            row_type,
            row.row_number,
            row.item_name,
            row.quantity_in_stock,
            row.quantity_dispatched,
            reason,
        )

    def _apply_row_calculations(
        self,
        row: SummaryRow,
        sim_cards: int,
        dmcc_cards: int,
        active_bank_row: Optional[SummaryRow] = None,
        active_sim_row: Optional[SummaryRow] = None,
    ) -> None:
        row.row_type = self._detect_row_type(row.item_name)
        row.calculated_card_change = None
        row.new_quantity_in_stock = None
        row.new_quantity_dispatched = None
        row.changes_required = False

        is_active_row = False
        card_change = None
        if row.row_type == self.ROW_TYPE_BANK_CARD:
            is_active_row = active_bank_row is not None and row.row_number == active_bank_row.row_number
            card_change = dmcc_cards if is_active_row else None
        elif row.row_type == self.ROW_TYPE_SIM:
            is_active_row = active_sim_row is not None and row.row_number == active_sim_row.row_number
            card_change = sim_cards if is_active_row else None

        if not is_active_row or card_change is None:
            return

        row.calculated_card_change = card_change
        if row.quantity_in_stock is not None:
            row.new_quantity_in_stock = row.quantity_in_stock - card_change
        if row.quantity_dispatched is not None:
            row.new_quantity_dispatched = row.quantity_dispatched + card_change
        row.changes_required = any(
            [
                row.new_quantity_in_stock is not None and row.new_quantity_in_stock != row.quantity_in_stock,
                row.new_quantity_dispatched is not None and row.new_quantity_dispatched != row.quantity_dispatched,
            ]
        )

    def _read_summary_rows(self, summary_sheet: str) -> List[SummaryRow]:
        """
        Read rows from the CAPITEC SUMMARY FILE REPORT worksheet.

        Args:
            summary_sheet: Summary worksheet name.

        Returns:
            List of SummaryRow objects.
        """
        rows: List[SummaryRow] = []
        worksheet = self.loader.get_worksheet(summary_sheet)
        if worksheet is None:
            self.logger.error("Unable to access summary worksheet for reading rows")
            return rows

        header_row_idx, headers = self._find_summary_header_row(worksheet)
        normalized_header_map = {
            self._normalize_header(header): idx + 1
            for idx, header in enumerate(headers) if header
        }
        files_col = normalized_header_map.get('files received', 1)
        total_qty_col = self._get_column(normalized_header_map, 'total quantity received', 'total quantity received')
        stock_col = self._get_column(normalized_header_map, 'quantity in stock', 'current quantity in stock')
        dispatched_col = self._get_column(normalized_header_map, 'quantity dispatched', 'current quantity dispatched')
        comment_col = self._get_column(normalized_header_map, 'comment')

        self.logger.info(
            "Resolved columns: stock_col=%s dispatched_col=%s",
            stock_col, dispatched_col
        )

        for row_idx, row in enumerate(worksheet.iter_rows(min_row=header_row_idx + 1), start=header_row_idx + 1):
            item_cell = row[files_col - 1] if len(row) >= files_col else None
            item_name = str(item_cell.value).strip() if item_cell and item_cell.value is not None else ''
            if not item_name:
                continue

            raw_values: Dict[str, Any] = {}
            for idx, header in enumerate(headers, start=1):
                if header:
                    if len(row) >= idx:
                        raw_values[header] = row[idx - 1].value
                    else:
                        raw_values[header] = None

            raw_quantity_in_stock = self._get_raw_cell_value(row, stock_col)
            raw_quantity_dispatched = self._get_raw_cell_value(row, dispatched_col)
            total_quantity_received = self._parse_int_cell(row, total_qty_col)
            quantity_in_stock = self._parse_int_cell(row, stock_col)
            quantity_dispatched = self._parse_int_cell(row, dispatched_col)
            comment = self._parse_string_cell(row, comment_col)
            row_type = self._detect_row_type(item_name)

            self.logger.info(
                "Summary row diagnostics: row_number=%s files_received=%s total_quantity_received=%s "
                "raw_quantity_in_stock=%s parsed_quantity_in_stock=%s raw_quantity_dispatched=%s "
                "parsed_quantity_dispatched=%s comment=%s row_type=%s",
                row_idx,
                item_name,
                total_quantity_received,
                raw_quantity_in_stock,
                quantity_in_stock,
                raw_quantity_dispatched,
                quantity_dispatched,
                comment,
                row_type,
            )

            summary_row = SummaryRow(
                row_number=row_idx,
                item_name=item_name,
                total_quantity_received=total_quantity_received,
                quantity_in_stock=quantity_in_stock,
                quantity_dispatched=quantity_dispatched,
                comment=comment,
                raw_values=raw_values
            )
            rows.append(summary_row)

        self.logger.info(f"Read {len(rows)} summary rows from {summary_sheet}")
        return rows

    def _get_raw_cell_value(self, row: List[Any], col_idx: Optional[int]) -> Any:
        if not col_idx or len(row) < col_idx:
            return None
        cell = row[col_idx - 1]
        if cell is None:
            return None

        value = cell.value
        if isinstance(value, str) and value.startswith('='):
            cached_value = getattr(cell, 'cached_value', None)
            if cached_value is not None:
                return cached_value
        return value

    def _parse_int_cell(self, row: List[Any], col_idx: Optional[int]) -> Optional[int]:
        value = self._get_raw_cell_value(row, col_idx)
        if value is None:
            return None
        # Be forgiving: handle ints, floats, formula strings, and numeric strings.
        try:
            return int(value)
        except Exception:
            try:
                s = str(value).strip()
                if s.startswith('='):
                    s = s[1:].strip()
                # Remove thousands separators
                s = s.replace(',', '')
                if s == '':
                    return None
                if '.' in s:
                    return int(float(s))
                return int(s)
            except Exception:
                return None

    def _parse_string_cell(self, row: List[Any], col_idx: Optional[int]) -> Optional[str]:
        if not col_idx or len(row) < col_idx:
            return None
        cell = row[col_idx - 1]
        return str(cell.value).strip() if cell.value is not None else None

    def _build_current_summary_values(self, summary_rows: List[SummaryRow]) -> Dict[str, Optional[int]]:
        """
        Build current summary metric values keyed by item name.

        Args:
            summary_rows: Summary rows read from the worksheet.

        Returns:
            Mapping of item_name to current integer value.
        """
        values: Dict[str, Optional[int]] = {}
        for row in summary_rows:
            # Prefer quantity dispatched, then quantity in stock, then total quantity received.
            current_value = row.quantity_dispatched
            if current_value is None:
                current_value = row.quantity_in_stock
            if current_value is None:
                current_value = row.total_quantity_received
            values[row.item_name] = current_value
        self.logger.debug(f"Current summary values: {values}")
        return values

    def _build_summary_differences(self, analysis: SummaryAnalysis) -> List[SummaryDifference]:
        """
        Build comparison differences for analyzed summary metrics.

        Args:
            analysis: SummaryAnalysis object.

        Returns:
            List of SummaryDifference values.
        """
        differences: List[SummaryDifference] = []

        

        # Then: build a per-row difference entry for every summary row.
        for row in analysis.summary_rows:
            existing_value = row.quantity_dispatched

            # Prefer to show the new dispatched value if available, otherwise
            # new stock, otherwise show calculated_card_change if present.
            if row.new_quantity_dispatched is not None:
                calculated_value = row.new_quantity_dispatched
            elif row.new_quantity_in_stock is not None:
                calculated_value = row.new_quantity_in_stock
            elif row.calculated_card_change is not None:
                calculated_value = row.calculated_card_change
            else:
                calculated_value = None

            difference = (calculated_value - existing_value) if calculated_value is not None and existing_value is not None else None
            status = 'Mismatch' if row.changes_required else (
                'Match' if existing_value is not None and calculated_value is not None and difference == 0 else 'Unknown'
            )

            differences.append(
                SummaryDifference(
                    metric_name=row.item_name,
                    existing_value=existing_value,
                    calculated_value=calculated_value if calculated_value is not None else 0,
                    difference=difference,
                    status=status,
                )
            )

        self.logger.info(f"Built {len(differences)} summary differences (metrics + rows)")
        return differences

    def _find_existing_metric_value(self, metric_name: str, analysis: SummaryAnalysis) -> Optional[int]:
        raw = analysis.existing_summary_values.get(metric_name)
        if not raw:
            return None
        for value in raw.values():
            try:
                return int(value) if value is not None else None
            except Exception:
                continue
        return None
