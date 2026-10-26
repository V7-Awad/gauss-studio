"""Custom-painted augmented matrix with operation highlights."""

from __future__ import annotations

from fractions import Fraction

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPolygon
from PySide6.QtWidgets import QWidget

from gauss_visualizer.core.fraction_utils import format_decimal, format_fraction
from gauss_visualizer.core.models import SolutionStep


class MatrixView(QWidget):
    """Draw a matrix using Qt painting rather than text output."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.step: SolutionStep | None = None
        self.variable_names: tuple[str, ...] = ()
        self.decimal_display = False
        self.dark_theme = False
        self.setMinimumSize(420, 300)

    def set_step(self, step: SolutionStep, variable_names: tuple[str, ...]) -> None:
        self.step = step
        self.variable_names = variable_names
        rows, cols = len(step.snapshot), len(step.snapshot[0])
        self.setMinimumSize(max(420, 170 + cols * 56), max(280, 130 + rows * 40))
        self.update()

    def set_decimal_display(self, enabled: bool) -> None:
        self.decimal_display = enabled
        self.update()

    def set_dark_theme(self, enabled: bool) -> None:
        self.dark_theme = enabled
        self.update()

    def _format(self, value: object) -> str:
        return format_decimal(value) if self.decimal_display else format_fraction(value)

    def _draw_value(self, painter: QPainter, x: int, y: int, width: int, height: int,
                    value: Fraction) -> None:
        if not self.decimal_display and value.denominator != 1:
            center_x = x + width // 2
            center_y = y + height // 2
            painter.drawText(x, center_y - 17, width, 17, Qt.AlignmentFlag.AlignCenter,
                             str(value.numerator))
            painter.drawLine(center_x - 15, center_y, center_x + 15, center_y)
            painter.drawText(x, center_y + 1, width, 17, Qt.AlignmentFlag.AlignCenter,
                             str(value.denominator))
        else:
            painter.drawText(x, y, width, height, Qt.AlignmentFlag.AlignCenter, self._format(value))

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        palette = {
            "canvas": "#172235" if self.dark_theme else "#fbfcff",
            "text": "#e7edf7" if self.dark_theme else "#172033",
            "muted": "#a8b6c9" if self.dark_theme else "#536174",
            "grid": "#d0d9e6" if self.dark_theme else "#374151",
            "pivot_row": "#3b3423" if self.dark_theme else "#fff7df",
            "source_row": "#1f3a32" if self.dark_theme else "#e3f5e8",
            "affected_row": "#223a57" if self.dark_theme else "#dceeff",
            "contradiction": "#4a2d36" if self.dark_theme else "#ffd9d9",
            "pivot_cell": "#74551d" if self.dark_theme else "#ffe09a",
            "pivot_border": "#ffc14d" if self.dark_theme else "#d08a00",
            "changed_border": "#62a4ff" if self.dark_theme else "#2684ff",
            "column_band": "#3e3521" if self.dark_theme else "#ffcc66",
        }
        painter.fillRect(self.rect(), QColor(palette["canvas"]))
        if self.step is None:
            painter.setPen(QColor(palette["muted"]))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Enter a system and select Solve")
            return
        matrix = self.step.snapshot
        rows, cols = len(matrix), len(matrix[0])
        left, top = 112.0, 70.0
        cell_w = min(110.0, max(56.0, (self.width() - 160.0) / cols))
        cell_h = min(64.0, max(38.0, (self.height() - 140.0) / rows))
        font_size = max(10, min(16, int(cell_h * 0.34)))
        painter.setFont(QFont("Consolas", font_size))
        h = self.step.highlight
        if h.pivot_col is not None:
            x = left + h.pivot_col * cell_w
            band = QColor(palette["column_band"])
            band.setAlpha(60 if not self.dark_theme else 75)
            painter.fillRect(int(x), int(top), int(cell_w), int(rows * cell_h), band)
        for r, row in enumerate(matrix):
            y = top + r * cell_h
            if r == h.pivot_row:
                painter.fillRect(int(left), int(y), int(cols * cell_w), int(cell_h), QColor(palette["pivot_row"]))
            if r in h.source_rows and r not in h.affected_rows:
                painter.fillRect(int(left), int(y), int(cols * cell_w), int(cell_h), QColor(palette["source_row"]))
            elif r in h.affected_rows:
                painter.fillRect(int(left), int(y), int(cols * cell_w), int(cell_h), QColor(palette["affected_row"]))
            if r == h.contradiction_row:
                painter.fillRect(int(left), int(y), int(cols * cell_w), int(cell_h), QColor(palette["contradiction"]))
            painter.setPen(QColor(palette["muted"]))
            painter.drawText(20, int(y + cell_h * .62), f"R{r + 1}")
            if r == h.pivot_row:
                painter.setPen(QColor(palette["pivot_border"]))
                painter.drawText(43, int(y + cell_h * .62), "◄ pivot")
            elif r in h.source_rows:
                painter.setPen(QColor("#7bc88c" if self.dark_theme else "#267a3b"))
                painter.drawText(43, int(y + cell_h * .62), "◄ source")
            for c, value in enumerate(row):
                x = left + c * cell_w
                if (r, c) in h.changed_cells:
                    painter.setPen(QPen(QColor(palette["changed_border"]), 2))
                    painter.drawRoundedRect(int(x + 4), int(y + 4), int(cell_w - 8), int(cell_h - 8), 5, 5)
                painter.setPen(QColor(palette["text"]))
                self._draw_value(painter, int(x), int(y), int(cell_w), int(cell_h), value)
        if h.pivot_row is not None and h.pivot_col is not None:
            x = left + h.pivot_col * cell_w
            y = top + h.pivot_row * cell_h
            painter.fillRect(int(x + 5), int(y + 5), int(cell_w - 10), int(cell_h - 10), QColor(palette["pivot_cell"]))
            painter.setPen(QPen(QColor(palette["pivot_border"]), 3))
            painter.drawRect(int(x + 5), int(y + 5), int(cell_w - 10), int(cell_h - 10))
            painter.setPen(QColor(palette["text"]))
            self._draw_value(painter, int(x), int(y), int(cell_w), int(cell_h),
                             matrix[h.pivot_row][h.pivot_col])
            arrow_x = int(x + cell_w / 2)
            arrow_y = int(top + rows * cell_h + 8)
            painter.setPen(QPen(QColor(palette["pivot_border"]), 2))
            painter.drawLine(arrow_x, arrow_y + 13, arrow_x, arrow_y + 2)
            painter.setBrush(QColor(palette["pivot_border"]))
            painter.drawPolygon(QPolygon([QPoint(arrow_x, arrow_y - 1),
                                          QPoint(arrow_x - 5, arrow_y + 6),
                                          QPoint(arrow_x + 5, arrow_y + 6)]))
            painter.setPen(QColor(palette["pivot_border"]))
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(arrow_x - 36, arrow_y + 20, "pivot column")
        painter.setPen(QPen(QColor(palette["grid"]), 2))
        painter.drawLine(int(left), int(top - 8), int(left), int(top + rows * cell_h + 8))
        painter.drawLine(int(left + cols * cell_w), int(top - 8), int(left + cols * cell_w),
                         int(top + rows * cell_h + 8))
        painter.setPen(QPen(QColor(palette["muted"]), 1, Qt.PenStyle.DashLine))
        painter.drawLine(int(left + (cols - 1) * cell_w), int(top - 8),
                         int(left + (cols - 1) * cell_w), int(top + rows * cell_h + 8))
        painter.setPen(QColor(palette["muted"]))
        for c in range(cols):
            name = self.variable_names[c] if c < len(self.variable_names) else "b"
            painter.drawText(int(left + c * cell_w), 42, int(cell_w), 24,
                             Qt.AlignmentFlag.AlignCenter, name)
        painter.setFont(QFont("Segoe UI", 10))
        painter.setPen(QColor(palette["text"]))
        painter.drawText(16, int(top + rows * cell_h + 40), self.step.operation_label)
        painter.setPen(QColor(palette["muted"]))
        painter.drawText(16, self.height() - 12, self.step.explanation[:120])
        legend_y = 18
        for index, (color, label) in enumerate((("#ffe09a", "Pivot"), ("#dceeff", "Changed row"),
                                                 ("#e3f5e8", "Source row"), ("#ffd9d9", "Contradiction"))):
            x = int(left + index * 74)
            painter.fillRect(x, legend_y, 10, 10, QColor(color))
            painter.setPen(QColor("#536174"))
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(x + 14, legend_y + 9, label)
