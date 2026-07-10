"""
Audit History Window - Display validation audit log.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QComboBox, QDateEdit
)
from PySide6.QtCore import QDate
from src.utils.logger import get_logger


class AuditHistoryWindow(QMainWindow):
    """
    Window for displaying audit history.
    
    Shows a log of all validation runs with details
    like date, workbook, duration, results, and statistics.
    """

    def __init__(self) -> None:
        """Initialize the Audit History Window."""
        super().__init__()
        self.logger = get_logger()
        
        self.setWindowTitle("Audit History")
        self.setGeometry(100, 100, 1000, 600)
        
        self._create_widgets()
        self._setup_layout()
        
        self.logger.info("AuditHistoryWindow initialized")

    def _create_widgets(self) -> None:
        """Create all widgets."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Filter section
        self.filter_date_label = QLabel("Filter by Date:")
        self.filter_date_edit = QDateEdit()
        self.filter_date_edit.setDate(QDate.currentDate())
        
        self.filter_status_label = QLabel("Filter by Status:")
        self.filter_status_combo = QComboBox()
        self.filter_status_combo.addItems(["All", "Passed", "Failed", "Warnings"])
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Date",
            "Workbook",
            "Duration",
            "Errors",
            "Warnings",
            "Result",
            "Summary Updated"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Buttons
        self.export_pdf_button = QPushButton("Export PDF")
        self.export_excel_button = QPushButton("Export Excel")
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)

    def _setup_layout(self) -> None:
        """Set up the layout."""
        central_widget = self.centralWidget()
        main_layout = QVBoxLayout()
        
        # Filter layout
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(self.filter_date_label)
        filter_layout.addWidget(self.filter_date_edit)
        filter_layout.addWidget(self.filter_status_label)
        filter_layout.addWidget(self.filter_status_combo)
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)
        
        # Table
        main_layout.addWidget(self.table)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.export_pdf_button)
        buttons_layout.addWidget(self.export_excel_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.close_button)
        main_layout.addLayout(buttons_layout)
        
        central_widget.setLayout(main_layout)

    def populate_audit_log(self, records: list) -> None:
        """
        Populate the table with audit records.
        
        Args:
            records: List of audit log records.
        """
        self.table.setRowCount(len(records))
        
        for row, record in enumerate(records):
            # This is a placeholder - actual implementation would
            # populate with real data from the database
            pass
