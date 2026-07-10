"""
Progress Dialog - Shows validation progress.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QHBoxLayout
)
from src.utils.logger import get_logger


class ProgressDialog(QDialog):
    """
    Dialog window for displaying validation progress.
    
    Shows current task, validation step, progress bar,
    and a cancel button (disabled for now).
    """

    def __init__(self) -> None:
        """Initialize the Progress Dialog."""
        super().__init__()
        self.logger = get_logger()
        
        self.setWindowTitle("Validation Progress")
        self.setGeometry(200, 200, 450, 180)
        self.setModal(True)
        
        self._create_widgets()
        self._setup_layout()
        
        self.logger.info("ProgressDialog initialized")

    def _create_widgets(self) -> None:
        """Create all widgets."""
        self.task_label = QLabel("Loading workbook...")
        self.step_label = QLabel("Step: Pending")
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.percentage_label = QLabel("0%")
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)

    def _setup_layout(self) -> None:
        """Set up the layout."""
        layout = QVBoxLayout()
        layout.addWidget(self.task_label)
        layout.addWidget(self.step_label)
        layout.addWidget(self.progress_bar)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.percentage_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.cancel_button)

        layout.addLayout(bottom_layout)
        self.setLayout(layout)

    def update_progress(self, value: int, task: str, step: str = "") -> None:
        """
        Update progress bar and task labels.
        
        Args:
            value: Progress percentage (0-100).
            task: Current task description.
            step: Current validation step description.
        """
        self.progress_bar.setValue(value)
        self.task_label.setText(task)
        self.step_label.setText(f"Step: {step}" if step else "Step: Pending")
        self.percentage_label.setText(f"{value}%")
