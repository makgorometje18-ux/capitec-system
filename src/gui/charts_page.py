"""
Charts Dashboard
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class ChartsPage(QWidget):
    def __init__(self):
        super().__init__()

        # Statistics - latest validation only (not cumulative)
        self.total_tests = 0
        self.pass_count = 0
        self.fail_count = 0
        self.pass_rate = 0.0

        self.setWindowTitle("Charts Dashboard")
        self.resize(1000, 700)

        layout = QVBoxLayout(self)

        # ==========================
        # Title
        # ==========================
        title = QLabel("Capitec Daily Reconciliation Analytics")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # ==========================
        # Latest Status
        # ==========================
        self.status_label = QLabel("No validation has been run yet.")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        layout.addSpacing(25)

        # ==========================
        # KPI Cards (latest validation only)
        # ==========================
        cards_layout = QHBoxLayout()

        value_font = QFont()
        value_font.setPointSize(14)
        value_font.setBold(True)

        def create_card(title, value):
            frame = QFrame()
            frame.setFrameShape(QFrame.Box)
            frame.setMinimumHeight(100)

            card_layout = QVBoxLayout(frame)

            title_label = QLabel(title)
            title_label.setAlignment(Qt.AlignCenter)

            value_label = QLabel(value)
            value_label.setAlignment(Qt.AlignCenter)
            value_label.setFont(value_font)

            card_layout.addWidget(title_label)
            card_layout.addWidget(value_label)

            return frame, value_label

        total_card, self.total_label = create_card("Total Tests", "0")
        pass_card, self.pass_label = create_card("PASS", "0")
        fail_card, self.fail_label = create_card("FAIL", "0")
        rate_card, self.rate_label = create_card("Pass Rate", "0.0%")

        cards_layout.addWidget(total_card)
        cards_layout.addWidget(pass_card)
        cards_layout.addWidget(fail_card)
        cards_layout.addWidget(rate_card)

        layout.addLayout(cards_layout)
        layout.addStretch()

    def update_statistics(self, passed: bool):
        """
        Update dashboard statistics - shows ONLY the latest validation.
        Does NOT accumulate across validations.
        """
        # Overwrite with latest validation only (reset = 1 latest test)
        self.total_tests = 1

        if passed:
            self.pass_count = 1
            self.fail_count = 0
            self.status_label.setText("Latest Validation: PASS")
        else:
            self.pass_count = 0
            self.fail_count = 1
            self.status_label.setText("Latest Validation: FAIL")

        self.total_label.setText(str(self.total_tests))
        self.pass_label.setText(str(self.pass_count))
        self.fail_label.setText(str(self.fail_count))

        # Pass rate is 100% if passed, 0% if failed (single validation)
        self.pass_rate = 100.0 if passed else 0.0
        self.rate_label.setText(f"{self.pass_rate:.1f}%")

    def reset_statistics(self):
        """Reset all KPI cards to zero. Preserves the widget itself."""
        self.total_tests = 0
        self.pass_count = 0
        self.fail_count = 0
        self.pass_rate = 0.0

        self.total_label.setText("0")
        self.pass_label.setText("0")
        self.fail_label.setText("0")
        self.rate_label.setText("0.0%")
        self.status_label.setText("No validation has been run yet.")