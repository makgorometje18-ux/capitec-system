from time import perf_counter
from typing import Dict, List, Optional

from src.core.audit_manager import AuditManager
from src.core.workbook_loader import WorkbookLoader
from src.models.models import SummaryAnalysis, SummaryRow, UpdateResult
from src.utils.logger import get_logger


class SummaryWorksheetUpdater:
    """Safely apply summary worksheet updates using analysis results only."""

    REQUIRED_METRIC_NAMES = [
        'SIM Orders',
        'SIM Cards',
        'DMCCLS Orders',
        'DMCCLS Cards',
        'Total Orders',
        'Total Cards',
    ]

    NUMERIC_HEADERS = [
    'Total quantity received',
    'Quantity In stock',
    'Quantity dispatched',
    ]

    def __init__(self) -> None:
        self.logger = get_logger()
        self.audit_manager = AuditManager()

    def update_summary_worksheet(self, analysis: SummaryAnalysis, loader: WorkbookLoader) -> UpdateResult:
        result = UpdateResult()
        start_time = perf_counter()

        try:
            if not analysis.summary_worksheet_name:
                self.logger.error('Summary worksheet name missing from analysis')
                result.failed_fields.append('Summary worksheet name missing')
                return self._finalize_result(result, start_time)

            worksheet = loader.get_worksheet(analysis.summary_worksheet_name)
            if worksheet is None:
                self.logger.error('Unable to access summary worksheet from loader')
                result.failed_fields.append('Summary worksheet access failed')
                return self._finalize_result(result, start_time)

            headers = loader.get_headers(analysis.summary_worksheet_name)
            if not headers:
                self.logger.error('Summary worksheet headers not found')
                result.failed_fields.append('Summary headers missing')
                return self._finalize_result(result, start_time)

            header_map = {header: idx + 1 for idx, header in enumerate(headers) if header}

             #
            # Update every summary row (P_ files and C-Connect rows)
            #
            for summary_row in analysis.summary_rows:

                excel_row = summary_row.row_number

                #
                # Total quantity received
                #
                if "Total quantity received" in header_map:
                    column = header_map["Total quantity received"]

                    worksheet.cell(
                        row=excel_row,
                        column=column
                    ).value = summary_row.total_quantity_received

                #
                # Quantity In stock
                #
                if "Quantity In stock" in header_map:
                    column = header_map["Quantity In stock"]

                    if summary_row.new_quantity_in_stock is not None:
                        worksheet.cell(
                            row=excel_row,
                            column=column
                        ).value = summary_row.new_quantity_in_stock

                #
                # Quantity dispatched
                #
                if "Quantity dispatched" in header_map:
                    column = header_map["Quantity dispatched"]

                    if summary_row.new_quantity_dispatched is not None:
                        worksheet.cell(
                            row=excel_row,
                            column=column
                        ).value = summary_row.new_quantity_dispatched

                result.updated_fields.append(summary_row.item_name)

                self.logger.info(
                    f"Updated summary row: {summary_row.item_name}"
                )

            try:
                loader.workbook.save(loader.current_file_path)
                self.logger.info(f'Saved updated summary workbook: {loader.current_file_path}')
            except Exception as save_error:
                self.logger.error(f'Failed to save updated workbook: {save_error}')
                result.failed_fields.append(f'save_error:{save_error}')
                return self._finalize_result(result, start_time)

            return self._finalize_result(result, start_time, success=len(result.failed_fields) == 0)

        except Exception as exc:
            self.logger.error(f'Error updating summary worksheet: {exc}')
            result.failed_fields.append(str(exc))
            return self._finalize_result(result, start_time)

    def _find_metric_row(self, analysis: SummaryAnalysis, metric_name: str) -> Optional[SummaryRow]:
        for row in analysis.files_received_rows:
            if row.item_name == metric_name:
                return row
        return None

    def _select_target_header(self, summary_row: SummaryRow, header_map: Dict[str, int]) -> Optional[str]:
        for header in self.NUMERIC_HEADERS:
            if header in header_map and summary_row.raw_values.get(header) is not None:
                return header

        for header in self.NUMERIC_HEADERS:
            if header in header_map:
                return header
        return None

    def _parse_int(self, raw_value: Optional[object]) -> Optional[int]:
        if raw_value is None:
            return None
        try:
            return int(raw_value)
        except Exception:
            try:
                return int(str(raw_value).strip())
            except Exception:
                return None

    def _finalize_result(self, result: UpdateResult, start_time: float, success: bool = False) -> UpdateResult:
        result.elapsed_time = perf_counter() - start_time
        result.success = success
        return result
