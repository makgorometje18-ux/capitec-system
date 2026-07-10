"""
Dashboard Module - Main application window.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar, QFileDialog,
    QGroupBox, QGridLayout, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QIcon

from src.core.workbook_loader import WorkbookLoader
from src.core.validation_engine import ValidationEngine
from src.core.backup_manager import BackupManager
from src.core.excel_highlighter import ExcelHighlighter
from src.core.error_summary_builder import ErrorSummaryBuilder
from src.core.summary_reconciliation_engine import SummaryReconciliationEngine

from src.gui.progress_dialog import ProgressDialog
from src.utils.logger import get_logger
from src.utils.settings_manager import get_settings

logger = get_logger()


def _build_summary_row_preview_rows(analysis):
    rows = []
    for row in getattr(analysis, 'summary_rows', []) or []:
        if not getattr(row, 'changes_required', False):
            continue

        rows.append([
            row.item_name or '',
            str(row.quantity_in_stock) if row.quantity_in_stock is not None else 'N/A',
            str(row.new_quantity_in_stock) if row.new_quantity_in_stock is not None else 'N/A',
            str(row.quantity_dispatched) if row.quantity_dispatched is not None else 'N/A',
            str(row.new_quantity_dispatched) if row.new_quantity_dispatched is not None else 'N/A',
            str(row.calculated_card_change) if row.calculated_card_change is not None else 'N/A',
        ])
    return rows


def build_summary_update_preview_text(analysis) -> str:
    headers = [
        'Files received',
        'Current Quantity In Stock',
        'New Quantity In Stock',
        'Current Quantity Dispatched',
        'New Quantity Dispatched',
        'Card Change'
    ]
    rows = _build_summary_row_preview_rows(analysis)

    if not rows:
        return 'No workbook row updates required.'

    col_widths = [len(header) for header in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            col_widths[idx] = max(col_widths[idx], len(str(cell)))

    separator = '-' * (sum(col_widths) + len(col_widths) * 3 + 1)
    preview_lines = [
        separator,
        ' | '.join(header.ljust(col_widths[idx]) for idx, header in enumerate(headers)),
        separator,
    ]

    for row in rows:
        preview_lines.append(
            ' | '.join(str(cell).rjust(col_widths[idx]) if idx > 0 else str(cell).ljust(col_widths[idx])
                       for idx, cell in enumerate(row))
        )

    preview_lines.extend([
        separator,
        '',
        'Do you want to apply these updates to the workbook?'
    ])

    return '\n'.join(preview_lines)


class Dashboard(QMainWindow):
    """
    Main application dashboard window.
    
    Displays the main interface for workbook selection,
    validation control, and status information.
    """

    def __init__(self) -> None:
        """Initialize the Dashboard window."""
        super().__init__()
        self.logger = get_logger()
        self.settings = get_settings()
        self.selected_workbook: Optional[str] = None
        self.summary_analysis: Optional['SummaryAnalysis'] = None
        self.summary_loader = None
        
        self.setWindowTitle(self.settings.get('ui.window_title', 'CDRS'))
        self.setGeometry(100, 100, 
                        self.settings.get('ui.window_width', 1024),
                        self.settings.get('ui.window_height', 768))
        
        self._create_widgets()
        self._setup_layout()
        self._connect_signals()
        
        self.logger.info("Dashboard initialized")

    def _create_widgets(self) -> None:
        """Create all GUI widgets."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Title
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title_label = QLabel("Capitec Daily Reconciliation System")
        self.title_label.setFont(title_font)

        # Workbook section
        self.workbook_group = QGroupBox("Workbook")
        self.browse_button = QPushButton("Browse Workbook")
        self.selected_workbook_label = QLabel("No workbook selected")

        # Validation status section
        self.status_group = QGroupBox("Validation Status")
        self.status_label = QLabel("Ready")
        self.progress_label = QLabel("Progress: 0%")
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        # Summary section
        self.summary_group = QGroupBox("Summary")
        self.sim_orders_label = QLabel("SIM Orders: 0")
        self.bank_orders_label = QLabel("Bank Orders: 0")
        self.sim_cards_label = QLabel("SIM Cards: 0")
        self.bank_cards_label = QLabel("Bank Cards: 0")
        self.errors_label = QLabel("Errors: 0")
        self.warnings_label = QLabel("Warnings: 0")

        # Integration results section
        self.integration_group = QGroupBox("Integration Test Results")
        self.worksheet_label = QLabel("Worksheet: None")
        self.total_rows_label = QLabel("Total rows processed: 0")
        self.headers_label = QLabel("Headers: None")
        self.headers_label.setWordWrap(True)
        self.headers_status_label = QLabel("Required headers: Unknown")
        self.pass_fail_label = QLabel("Result: N/A")
        self.duplicate_errors_label = QLabel("Duplicate errors: 0")
        self.duplicate_in_cell_label = QLabel("Duplicate-in-cell errors: 0")
        self.duplicate_between_rows_label = QLabel("Duplicate-between-rows errors: 0")
        self.cross_workbook_duplicates_label = QLabel("Cross-workbook duplicates: 0")
        self.batch_count_mismatch_label = QLabel("Batch count mismatches: 0")
        self.bag_number_errors_label = QLabel("Bag number errors: 0")
        self.blank_field_errors_label = QLabel("Blank field errors: 0")
        self.invalid_card_type_errors_label = QLabel("Invalid Card_Type errors: 0")
        self.backup_status_label = QLabel("Backup: Not created")
        self.duplicate_report_status_label = QLabel("Duplicate report: Not generated")
        self.highlight_status_label = QLabel("Highlighting: Not applied")
        self.audit_log_status_label = QLabel("Audit log: Not recorded")

        # Action buttons
        self.start_validation_button = QPushButton("Run Integration Test")
        self.start_validation_button.setEnabled(False)
        self.generate_pdf_button = QPushButton("Generate PDF")
        self.generate_pdf_button.setEnabled(False)
        self.audit_history_button = QPushButton("Audit History")
        self.settings_button = QPushButton("Settings")
        self.about_button = QPushButton("About")
        self.exit_button = QPushButton("Exit")

        # Store widgets for later access
        self.central_widget = central_widget

    def _setup_layout(self) -> None:
        """Set up the window layout."""
        main_layout = QVBoxLayout(self.central_widget)

        # Title
        main_layout.addWidget(self.title_label)

        # Workbook section
        workbook_layout = QHBoxLayout()
        workbook_layout.addWidget(self.browse_button)
        workbook_layout.addWidget(self.selected_workbook_label)
        workbook_layout.addStretch()
        self.workbook_group.setLayout(workbook_layout)
        main_layout.addWidget(self.workbook_group)

        # Status section
        status_layout = QVBoxLayout()
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.progress_label)
        status_layout.addWidget(self.progress_bar)
        self.status_group.setLayout(status_layout)
        main_layout.addWidget(self.status_group)

        # Summary section
        summary_layout = QGridLayout()
        summary_layout.addWidget(self.sim_orders_label, 0, 0)
        summary_layout.addWidget(self.bank_orders_label, 0, 1)
        summary_layout.addWidget(self.sim_cards_label, 1, 0)
        summary_layout.addWidget(self.bank_cards_label, 1, 1)
        summary_layout.addWidget(self.errors_label, 2, 0)
        summary_layout.addWidget(self.warnings_label, 2, 1)
        self.summary_group.setLayout(summary_layout)
        main_layout.addWidget(self.summary_group)

        # Integration results section
        integration_layout = QGridLayout()
        integration_layout.addWidget(self.worksheet_label, 0, 0, 1, 2)
        integration_layout.addWidget(self.total_rows_label, 1, 0, 1, 2)
        integration_layout.addWidget(self.headers_label, 2, 0, 1, 2)
        integration_layout.addWidget(self.headers_status_label, 3, 0, 1, 2)
        integration_layout.addWidget(self.pass_fail_label, 4, 0, 1, 2)
        integration_layout.addWidget(self.duplicate_errors_label, 5, 0)
        integration_layout.addWidget(self.duplicate_in_cell_label, 5, 1)
        integration_layout.addWidget(self.duplicate_between_rows_label, 6, 0)
        integration_layout.addWidget(self.cross_workbook_duplicates_label, 6, 1)
        integration_layout.addWidget(self.batch_count_mismatch_label, 7, 0)
        integration_layout.addWidget(self.bag_number_errors_label, 7, 1)
        integration_layout.addWidget(self.blank_field_errors_label, 8, 0)
        integration_layout.addWidget(self.invalid_card_type_errors_label, 8, 1)
        integration_layout.addWidget(self.backup_status_label, 9, 0, 1, 2)
        integration_layout.addWidget(self.duplicate_report_status_label, 10, 0, 1, 2)
        integration_layout.addWidget(self.highlight_status_label, 11, 0, 1, 2)
        integration_layout.addWidget(self.audit_log_status_label, 12, 0, 1, 2)
        self.integration_group.setLayout(integration_layout)
        main_layout.addWidget(self.integration_group)

        # Action buttons section
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.start_validation_button)
        buttons_layout.addWidget(self.generate_pdf_button)
        buttons_layout.addWidget(self.audit_history_button)
        buttons_layout.addWidget(self.settings_button)
        buttons_layout.addWidget(self.about_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.exit_button)
        main_layout.addLayout(buttons_layout)

        main_layout.addStretch()

    def _connect_signals(self) -> None:
        """Connect button signals to slots."""
        self.browse_button.clicked.connect(self._on_browse_workbook)
        self.start_validation_button.clicked.connect(self._on_start_validation)
        self.generate_pdf_button.clicked.connect(self._on_generate_pdf)
        self.audit_history_button.clicked.connect(self._on_audit_history)
        self.settings_button.clicked.connect(self._on_settings)
        self.about_button.clicked.connect(self._on_about)
        self.exit_button.clicked.connect(self._on_exit)

    def _on_browse_workbook(self) -> None:
        """Handle browse workbook button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Workbook",
            "",
            "Excel Workbooks (*.xlsx *.xls);;All Files (*)"
        )
        
        if file_path:
            self.selected_workbook = file_path
            self.selected_workbook_label.setText(file_path)
            self.start_validation_button.setEnabled(True)
            self.logger.info(f"Workbook selected: {file_path}")

    def _on_start_validation(self) -> None:
        """Handle start validation button click."""
        if not self.selected_workbook:
            QMessageBox.warning(self, "Warning", "Please select a workbook first")
            return
        
        self.status_label.setText("Starting integration test...")
        self.start_validation_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Progress: 0%")
        self._clear_integration_results()
        QApplication.processEvents()

        try:
            self._run_integration_test(self.selected_workbook)
        finally:
            self.start_validation_button.setEnabled(True)

    def _clear_integration_results(self) -> None:
        """Reset integration results in the UI."""
        self.worksheet_label.setText("Worksheet: None")
        self.total_rows_label.setText("Total rows processed: 0")
        self.headers_label.setText("Headers: None")
        self.headers_status_label.setText("Required headers: Unknown")
        self.pass_fail_label.setText("Result: N/A")
        self.duplicate_errors_label.setText("Duplicate errors: 0")
        self.duplicate_in_cell_label.setText("Duplicate-in-cell errors: 0")
        self.duplicate_between_rows_label.setText("Duplicate-between-rows errors: 0")
        self.cross_workbook_duplicates_label.setText("Cross-workbook duplicates: 0")
        self.batch_count_mismatch_label.setText("Batch count mismatches: 0")
        self.bag_number_errors_label.setText("Bag number errors: 0")
        self.blank_field_errors_label.setText("Blank field errors: 0")
        self.invalid_card_type_errors_label.setText("Invalid Card_Type errors: 0")
        self.backup_status_label.setText("Backup: Not created")
        self.duplicate_report_status_label.setText("Duplicate report: Not generated")
        self.highlight_status_label.setText("Highlighting: Not applied")
        self.audit_log_status_label.setText("Audit log: Not recorded")

    def _update_progress(self, value: int, status: str) -> None:
        """Update the dashboard progress bar and status text."""
        self.progress_bar.setValue(value)
        self.progress_label.setText(f"Progress: {value}%")
        self.status_label.setText(status)

    def _run_integration_test(self, file_path: str) -> None:
        """Run the integration test workflow for a selected workbook."""
        progress_dialog = ProgressDialog()
        progress_dialog.show()

        try:
            # Load workbook without formatting changes
            self._update_progress(10, "Loading workbook...")
            progress_dialog.update_progress(10, "Loading workbook...")
            QApplication.processEvents()
            loader = WorkbookLoader()
            workbook_model = loader.load_workbook(file_path)
            if not workbook_model:
                QMessageBox.critical(self, "Error", "Failed to load workbook")
                self.status_label.setText("Failed to load workbook")
                progress_dialog.close()
                return

            self.selected_workbook_label.setText(workbook_model.file_name)
            self.logger.info(f"Integration test workbook: {file_path}")

            self._update_progress(20, "Detecting Daily Output worksheet...")
            progress_dialog.update_progress(20, "Detecting Daily Output worksheet...")
            QApplication.processEvents()
            sheet_name = loader.detect_daily_output_sheet()
            self.worksheet_label.setText(f"Worksheet: {sheet_name or 'Not found'}")
            if not sheet_name:
                QMessageBox.warning(self, "Validation", "Daily Output worksheet not found")

            self._update_progress(30, "Reading headers...")
            progress_dialog.update_progress(30, "Reading headers...")
            QApplication.processEvents()
            headers = loader.get_headers(sheet_name) if sheet_name else []
            self.headers_label.setText(
                f"Headers: {', '.join(headers)}" if headers else "Headers: None"
            )

            required_headers = set(WorkbookLoader.REQUIRED_HEADERS)
            header_set = set(headers or [])
            missing_headers = sorted(required_headers - header_set)
            if missing_headers:
                self.headers_status_label.setText(
                    f"Required headers missing: {', '.join(missing_headers)}"
                )
            else:
                self.headers_status_label.setText("Required headers: All present")

            self._update_progress(40, "Counting rows...")
            progress_dialog.update_progress(40, "Counting rows...")
            QApplication.processEvents()
            data_rows = loader.get_data_rows(sheet_name) if sheet_name else []
            total_rows = len(data_rows) if data_rows is not None else 0
            self.total_rows_label.setText(f"Total rows processed: {total_rows}")

            self._update_progress(50, "Validating workbook...")
            progress_dialog.update_progress(50, "Validating workbook...")
            QApplication.processEvents()
            engine = ValidationEngine()
            validation_result = engine.validate_complete_workbook(file_path)
            engine_result_duplicates = engine.get_duplicates()
            self.errors_label.setText(f"Errors: {validation_result.error_count}")
            self.warnings_label.setText(f"Warnings: {validation_result.warning_count}")
            self.pass_fail_label.setText("Result: PASS" if validation_result.passed else "Result: FAIL")

            # Build categorized error summary
            summary_builder = ErrorSummaryBuilder()
            error_summary = summary_builder.build_summary(validation_result, engine_result_duplicates)
            self.duplicate_errors_label.setText(f"Duplicate errors: {len(engine_result_duplicates)}")
            self.duplicate_in_cell_label.setText(
                f"Duplicate-in-cell errors: {error_summary.duplicate_in_same_cell}"
            )
            self.duplicate_between_rows_label.setText(
                f"Duplicate-between-rows errors: {error_summary.duplicate_across_rows}"
            )
            self.cross_workbook_duplicates_label.setText(
                f"Cross-workbook duplicates: {error_summary.duplicate_in_previous}"
            )
            self.batch_count_mismatch_label.setText(
                f"Batch count mismatches: {error_summary.incorrect_no_of_batches}"
            )
            self.bag_number_errors_label.setText(
                f"Bag number errors: {error_summary.invalid_bag_numbers}"
            )
            self.blank_field_errors_label.setText(
                f"Blank field errors: {error_summary.blank_fields}"
            )
            self.invalid_card_type_errors_label.setText(
                f"Invalid Card_Type errors: {error_summary.invalid_card_types}"
            )

            self._update_progress(60, "Creating workbook backup...")
            progress_dialog.update_progress(60, "Creating workbook backup...")
            QApplication.processEvents()
            backup_manager = BackupManager(
                backup_folder=self.settings.get('paths.backup_folder', 'backups')
            )
            backup_ok = backup_manager.create_backup(workbook_model)
            self.backup_status_label.setText(
                "Backup: Created" if backup_ok else "Backup: Failed"
            )

            self._update_progress(70, "Generating duplicate report...")
            progress_dialog.update_progress(70, "Generating duplicate report...")
            QApplication.processEvents()
            duplicate_report_ok = False
            if engine_result_duplicates:
                duplicate_report_ok = engine.generate_duplicate_report(file_path)
                if duplicate_report_ok:
                    self.duplicate_report_status_label.setText("Duplicate report: Generated")
                else:
                    self.duplicate_report_status_label.setText("Duplicate report: Failed")
            else:
                self.duplicate_report_status_label.setText("Duplicate report: No duplicates found")

            self._update_progress(80, "Applying Excel highlighting...")
            progress_dialog.update_progress(80, "Applying Excel highlighting...")
            QApplication.processEvents()
            highlighting_ok = True
            errors_by_row = self._build_errors_by_row(validation_result, engine_result_duplicates)
            if errors_by_row and sheet_name:
                highlighter = ExcelHighlighter()
                if highlighter.load_workbook(file_path):
                    if highlighter.highlight_errors(sheet_name, errors_by_row):
                        highlighting_ok = highlighter.save_workbook()
                    else:
                        highlighting_ok = False
                    highlighter.close()
                else:
                    highlighting_ok = False
            elif errors_by_row:
                highlighting_ok = False

            if highlighting_ok:
                self.highlight_status_label.setText("Highlighting: Applied")
            else:
                self.highlight_status_label.setText("Highlighting: Not applied")

            self._update_progress(90, "Running summary analysis...")
            progress_dialog.update_progress(90, "Running summary analysis...")
            QApplication.processEvents()
            analysis_engine = SummaryReconciliationEngine()
            analysis = analysis_engine.analyze(file_path)
            self._update_progress(95, "Recording audit log...")
            progress_dialog.update_progress(95, "Recording audit log...")
            QApplication.processEvents()
            audit_ok = engine.log_validation_to_audit(file_path, validation_result)
            self.audit_log_status_label.setText(
                "Audit log: Recorded" if audit_ok else "Audit log: Failed"
            )
        except Exception as exc:
            self.logger.error(f"Integration test error: {exc}")
            QMessageBox.critical(self, "Error", f"Integration test failed: {exc}")
            self.status_label.setText("Integration test failed")
        finally:
            progress_dialog.close()

    def _build_errors_by_row(self, validation_result, duplicates):
        """Build a mapping of row numbers to errors for highlighting."""
        errors_by_row = {}
        import re
        row_pattern = re.compile(r"Row\s+(\d+)")

        for error_message in validation_result.errors:
            match = row_pattern.search(error_message)
            if match:
                row_num = int(match.group(1))
                errors_by_row.setdefault(row_num, []).append(error_message)

        for duplicate in duplicates:
            row_num = duplicate.row_number
            errors_by_row.setdefault(row_num, []).append(
                f"Duplicate batch {duplicate.batch_number}"
            )

        return errors_by_row

    

    @staticmethod
    def _build_summary_preview_rows(analysis):
        return _build_summary_row_preview_rows(analysis)

    @staticmethod
    def _build_summary_update_preview(self, analysis) -> str:
        headers = [
            'Files received',
            'Row Type',
            'Total quantity received',
            'Current Quantity In Stock',
            'New Quantity In Stock',
            'Current Quantity Dispatched',
            'New Quantity Dispatched',
            'Card change',
            'Changes Required'
        ]
        rows = Dashboard._build_summary_preview_rows(analysis)

        if not rows:
            return 'No workbook row updates required.'

        col_widths = [len(header) for header in headers]
        for row in rows:
            for idx, cell in enumerate(row):
                col_widths[idx] = max(col_widths[idx], len(str(cell)))

        separator = '-' * (sum(col_widths) + len(col_widths) * 3 + 1)
        preview_lines = [
            separator,
            ' | '.join(header.ljust(col_widths[idx]) for idx, header in enumerate(headers)),
            separator,
        ]

        for row in rows:
            preview_lines.append(
                ' | '.join(
                    str(cell).rjust(col_widths[idx]) if idx > 0 else str(cell).ljust(col_widths[idx])
                    for idx, cell in enumerate(row)
                )
            )

        preview_lines.extend([
            separator,
            '',
            'Do you want to apply these updates to the workbook?'
        ])

        return '\n'.join(preview_lines)

    def _refresh_dashboard_statistics(self, analysis) -> None:
        self.sim_orders_label.setText(f"SIM Orders: {analysis.sim_orders}")
        self.bank_orders_label.setText(f"Bank Orders: {analysis.dmcc_orders}")
        self.sim_cards_label.setText(f"SIM Cards: {analysis.sim_cards}")
        self.bank_cards_label.setText(f"Bank Cards: {analysis.dmcc_cards}")

    def _on_generate_pdf(self) -> None:
        """Handle generate PDF button click."""
        self.logger.info("Generate PDF clicked")

    def _on_audit_history(self) -> None:
        """Handle audit history button click."""
        self.logger.info("Audit history clicked")

    def _on_settings(self) -> None:
        """Handle settings button click."""
        self.logger.info("Settings clicked")

    def _on_about(self) -> None:
        """Handle about button click."""
        QMessageBox.information(
            self,
            "About CDRS",
            "Capitec Daily Reconciliation System\\nVersion 1.0.0\\n\\n"
            "A production-quality Windows desktop application for automated "
            "reconciliation of Capitec Daily Output Excel workbooks."
        )

    def _on_exit(self) -> None:
        """Handle exit button click."""
        self.close()

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        self.logger.info("Application closing")
        event.accept()
