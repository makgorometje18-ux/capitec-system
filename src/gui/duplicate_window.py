"""
Duplicate Report Window - Displays found duplicate batch numbers.
"""

from typing import List
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from src.models.models import DuplicateRecord
from src.utils.logger import get_logger


class DuplicateReportWindow(QMainWindow):
    """
    Window for displaying duplicate batch number report.
    
    Shows a table of all duplicate batch numbers found
    during validation with details and suggested actions.
    """

    def __init__(self) -> None:
        """Initialize the Duplicate Report Window."""
        super().__init__()
        self.logger = get_logger()
        
        self.setWindowTitle("Duplicate Batch Numbers Report")
        self.setGeometry(150, 150, 800, 600)
        
        self._create_widgets()
        self._setup_layout()
        
        self.logger.info("DuplicateReportWindow initialized")

    def _create_widgets(self) -> None:
        """Create all widgets."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Batch Number",
            "Worksheet",
            "Row",
            "Cell",
            "Occurrences",
            "Type"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Close button
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)

    def _setup_layout(self) -> None:
        """Set up the layout."""
        layout = QVBoxLayout()
        layout.addWidget(self.table)
        layout.addWidget(self.close_button)
        
        central_widget = self.centralWidget()
        central_widget.setLayout(layout)

    def populate_duplicates(self, duplicates: List[DuplicateRecord]) -> None:
        """
        Populate the table with duplicate records.
        
        Args:
            duplicates: List of DuplicateRecord objects.
        """
        self.table.setRowCount(len(duplicates))
        
        for row, dup in enumerate(duplicates):
            self.table.setItem(row, 0, QTableWidgetItem(dup.batch_number))
            self.table.setItem(row, 1, QTableWidgetItem(dup.worksheet))
            self.table.setItem(row, 2, QTableWidgetItem(str(dup.row_number)))
            self.table.setItem(row, 3, QTableWidgetItem(dup.cell_reference))
            self.table.setItem(row, 4, QTableWidgetItem(str(dup.occurrences)))
            self.table.setItem(row, 5, QTableWidgetItem(dup.duplicate_type))
