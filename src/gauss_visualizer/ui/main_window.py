"""Main desktop window for equation entry and step-by-step solutions."""

from __future__ import annotations

import re
import sys
from fractions import Fraction
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QBrush, QColor, QIcon, QImage, QKeySequence, QPalette, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QDialog, QDialogButtonBox, QFileDialog,
    QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPushButton, QSpinBox, QSplitter, QTabWidget, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget, QListWidget, QCheckBox, QSlider, QScrollArea,
    QStyle,
)

from gauss_visualizer.core.fraction_utils import format_fraction, parse_fraction
from gauss_visualizer.core.models import SolutionKind
from gauss_visualizer.core.parser import EquationParser
from gauss_visualizer.core.solver import GaussSolver, PivotStrategy
from gauss_visualizer.services.export_service import export_solution_pdf
from gauss_visualizer.ui.matrix_view import MatrixView
from gauss_visualizer.ui.workers import ImportWorker


class ImportPreview(QDialog):
    """Editable import review so OCR results are never used without confirmation."""

    def __init__(self, lines: list[str], preview: object | None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Review imported equations")
        outer = QVBoxLayout(self)
        layout = QHBoxLayout()
        self.editors: list[QLineEdit] = []
        form = QFormLayout()
        for index, line in enumerate(lines):
            editor = QLineEdit(line)
            self.editors.append(editor)
            form.addRow(f"Equation {index + 1}", editor)
        layout.addLayout(form, 2)
        if preview is not None:
            image = preview.convert("RGB")
            data = image.tobytes("raw", "RGB")
            qimage = QImage(data, image.width, image.height, image.width * 3,
                            QImage.Format.Format_RGB888).copy()
            view = QLabel()
            view.setPixmap(QPixmap.fromImage(qimage).scaled(360, 440,
                            Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            layout.addWidget(view, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                   QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addLayout(layout)
        outer.addWidget(buttons)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Gauss Studio | Gaussian Elimination")
        self.setMinimumSize(1080, 700)
        self.resize(1280, 820)
        self.setWindowIcon(QIcon(str(self._asset_path("gauss_icon.png"))))
        self.result = None
        self.current_step = 0
        self.import_worker: ImportWorker | None = None
        self.play_timer = QTimer(self)
        self.play_timer.timeout.connect(self._auto_advance)
        self.parser = EquationParser()
        self._build_ui()

    @staticmethod
    def _asset_path(name: str) -> Path:
        bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[3]))
        return bundle_root / "assets" / name

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("appRoot")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(20, 14, 20, 18)
        layout.setSpacing(12)

        brand = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(QPixmap(str(self._asset_path("gauss_icon.png"))).scaled(
            44, 44, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        brand.addWidget(icon)
        brand_text = QVBoxLayout()
        title = QLabel("Gauss Studio")
        title.setObjectName("brandTitle")
        subtitle = QLabel("Exact linear algebra, explained one operation at a time")
        subtitle.setObjectName("brandSubtitle")
        brand_text.addWidget(title); brand_text.addWidget(subtitle)
        brand.addLayout(brand_text)
        brand.addStretch()
        badge = QLabel("FRACTION-EXACT  ·  STEP-BY-STEP")
        badge.setObjectName("brandBadge")
        brand.addWidget(badge)
        layout.addLayout(brand)

        settings_card = QFrame()
        settings_card.setObjectName("settingsCard")
        settings_card_layout = QHBoxLayout(settings_card)
        settings_card_layout.setContentsMargins(14, 8, 14, 8)
        settings_card_layout.setSpacing(10)
        dimensions = QHBoxLayout()
        self.m_spin = QSpinBox(); self.m_spin.setRange(1, 20); self.m_spin.setValue(3); self.m_spin.setFixedWidth(78)
        self.n_spin = QSpinBox(); self.n_spin.setRange(1, 20); self.n_spin.setValue(3); self.n_spin.setFixedWidth(78)
        number_font = self.m_spin.font()
        number_font.setPointSize(12)
        number_font.setBold(True)
        self.m_spin.setFont(number_font)
        self.n_spin.setFont(number_font)
        self.m_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.n_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dimensions.addWidget(QLabel("Equations")); dimensions.addWidget(self.m_spin)
        dimensions.addWidget(QLabel("Variables")); dimensions.addWidget(self.n_spin)
        dimensions.addStretch()
        self.strategy = QComboBoxCompat()
        self.strategy.addItems(["First nonzero pivot", "Largest absolute pivot"])
        self.strategy.setMinimumWidth(190)
        self._style_strategy_popup(dark=True)
        dimensions.addWidget(QLabel("Pivot strategy")); dimensions.addWidget(self.strategy)
        settings_card_layout.addLayout(dimensions)
        layout.addWidget(settings_card)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        left = QWidget(); left.setObjectName("inputPanel"); left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(14, 14, 14, 14); left_layout.setSpacing(10)
        input_title = QLabel("SYSTEM INPUT"); input_title.setObjectName("sectionTitle")
        input_subtitle = QLabel("Enter each equation or edit the augmented matrix.")
        input_subtitle.setObjectName("sectionSubtitle")
        left_layout.addWidget(input_title); left_layout.addWidget(input_subtitle)
        self.tabs = QTabWidget()
        self.equation_page = QWidget(); equation_layout = QVBoxLayout(self.equation_page)
        equation_layout.setContentsMargins(10, 12, 10, 8); equation_layout.setSpacing(8)
        self.equation_edits: list[QLineEdit] = []
        self.equation_rows: list[QWidget] = []
        for i in range(3):
            row_widget = QWidget(); row = QHBoxLayout(row_widget); row.setContentsMargins(0, 0, 0, 0)
            row.addWidget(QLabel(f"Eq {i + 1}"))
            edit = QLineEdit(["2x + y - z = 8", "-3x - y + 2z = -11", "-2x + y + 2z = -3"][i])
            edit.textChanged.connect(self._update_solve_state)
            row.addWidget(edit); equation_layout.addWidget(row_widget)
            self.equation_edits.append(edit); self.equation_rows.append(row_widget)
        equation_layout.addStretch()
        self.tabs.addTab(self.equation_page, "Equations")
        self.grid = QTableWidget(3, 4)
        self.grid.setHorizontalHeaderLabels(["x", "y", "z", "b"])
        self.grid.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.grid.cellChanged.connect(self._sync_grid_to_equations)
        self.tabs.addTab(self.grid, "Matrix grid")
        self.tabs.currentChanged.connect(self._tab_changed)
        left_layout.addWidget(self.tabs)
        actions = QHBoxLayout()
        self.import_button = QPushButton("Import image / PDF")
        self.import_button.clicked.connect(self._import_file)
        self.solve_button = QPushButton("Solve")
        self.solve_button.clicked.connect(self._solve)
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self._clear)
        self.import_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
        self.solve_button.setObjectName("solveButton")
        self.solve_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        actions.addWidget(self.import_button); actions.addWidget(self.solve_button); actions.addWidget(self.clear_button)
        left_layout.addLayout(actions)
        splitter.addWidget(left)
        right = QWidget(); right.setObjectName("viewerPanel"); right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(14, 14, 14, 14); right_layout.setSpacing(10)
        viewer_header = QHBoxLayout()
        viewer_titles = QVBoxLayout()
        viewer_title = QLabel("SOLUTION WALKTHROUGH"); viewer_title.setObjectName("sectionTitle")
        viewer_subtitle = QLabel("Review the pivot, row operation, and resulting matrix.")
        viewer_subtitle.setObjectName("sectionSubtitle")
        viewer_titles.addWidget(viewer_title); viewer_titles.addWidget(viewer_subtitle)
        viewer_header.addLayout(viewer_titles); viewer_header.addStretch()
        right_layout.addLayout(viewer_header)
        self.matrix = MatrixView()
        matrix_scroll = QScrollArea()
        matrix_scroll.setWidgetResizable(True)
        matrix_scroll.setWidget(self.matrix)
        right_layout.addWidget(matrix_scroll, 1)
        nav = QHBoxLayout()
        self.first_button = QPushButton("|◀ First")
        self.prev_button = QPushButton("◀ Previous")
        self.next_button = QPushButton("Next ▶")
        self.last_button = QPushButton("Last ▶|")
        self.step_label = QLabel("No solution steps yet")
        self.step_label.setObjectName("stepStatus")
        for button, callback in ((self.first_button, lambda: self._show_step(0)),
                                 (self.prev_button, lambda: self._show_step(self.current_step - 1)),
                                 (self.next_button, lambda: self._show_step(self.current_step + 1)),
                                 (self.last_button, lambda: self._show_step(len(self.result.steps) - 1 if self.result else 0))):
            button.clicked.connect(callback); nav.addWidget(button)
        nav.addWidget(self.step_label, 1)
        right_layout.addLayout(nav)
        self.result_label = QLabel("Enter equations to begin.")
        self.result_label.setObjectName("resultPanel")
        self.result_label.setWordWrap(True)
        right_layout.addWidget(self.result_label)
        self.step_list = QListWidget()
        self.step_list.setMinimumHeight(70)
        self.step_list.setMaximumHeight(90)
        self.step_list.setWordWrap(True)
        self.step_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.step_list.currentRowChanged.connect(self._show_step)
        right_layout.addWidget(self.step_list)
        options = QHBoxLayout()
        self.play_button = QPushButton("▶ Auto-play")
        self.play_button.clicked.connect(self._toggle_auto_play)
        self.speed = QSlider(Qt.Orientation.Horizontal); self.speed.setRange(200, 2000); self.speed.setValue(800)
        self.speed.valueChanged.connect(self.play_timer.setInterval)
        self.decimal_toggle = QCheckBox("Decimals")
        self.decimal_toggle.toggled.connect(self.matrix.set_decimal_display)
        options.addWidget(self.play_button); options.addWidget(QLabel("Speed")); options.addWidget(self.speed, 1)
        options.addWidget(self.decimal_toggle)
        right_layout.addLayout(options)
        splitter.addWidget(right); splitter.setSizes([430, 830])
        layout.addWidget(splitter, 1)
        self.setCentralWidget(root)
        menu = self.menuBar().addMenu("File")
        export_action = QAction("Export solution PDF…", self)
        export_action.triggered.connect(self._export_pdf)
        menu.addAction(export_action)
        self.next_action = QAction(self); self.next_action.setShortcut(QKeySequence(Qt.Key.Key_Right))
        self.next_action.triggered.connect(lambda: self._show_step(self.current_step + 1)); self.addAction(self.next_action)
        self.prev_action = QAction(self); self.prev_action.setShortcut(QKeySequence(Qt.Key.Key_Left))
        self.prev_action.triggered.connect(lambda: self._show_step(self.current_step - 1)); self.addAction(self.prev_action)
        self.home_action = QAction(self); self.home_action.setShortcut(QKeySequence.StandardKey.MoveToStartOfDocument)
        self.home_action.triggered.connect(lambda: self._show_step(0)); self.addAction(self.home_action)
        self.end_action = QAction(self); self.end_action.setShortcut(QKeySequence.StandardKey.MoveToEndOfDocument)
        self.end_action.triggered.connect(lambda: self._show_step(len(self.result.steps) - 1 if self.result else 0)); self.addAction(self.end_action)
        self.m_spin.valueChanged.connect(self._resize_equations)
        self.n_spin.valueChanged.connect(self._resize_grid)
        for button in (self.first_button, self.prev_button, self.next_button, self.last_button):
            button.setEnabled(False)
        self._update_solve_state()
        self._apply_dark_theme()

    def _resize_equations(self, count: int) -> None:
        while len(self.equation_edits) < count:
            index = len(self.equation_edits)
            row_widget = QWidget(); row = QHBoxLayout(row_widget); row.setContentsMargins(0, 0, 0, 0)
            row.addWidget(QLabel(f"Eq {index + 1}"))
            edit = QLineEdit(); edit.textChanged.connect(self._update_solve_state)
            row.addWidget(edit); self.equation_page.layout().insertWidget(index, row_widget)
            self.equation_edits.append(edit); self.equation_rows.append(row_widget)
        while len(self.equation_edits) > count:
            self.equation_edits.pop().deleteLater()
            self.equation_rows.pop().deleteLater()
        self.grid.setRowCount(count)
        self._resize_grid(self.n_spin.value())
        self._update_solve_state()

    def _resize_grid(self, count: int) -> None:
        self.grid.setColumnCount(count + 1)
        self.grid.setRowCount(self.m_spin.value())
        self.grid.setHorizontalHeaderLabels([*(f"x{i + 1}" for i in range(count)), "b"])

    def _tab_changed(self, index: int) -> None:
        if index == 1:
            try:
                matrix, names = self._parsed_equations()
            except ValueError:
                return
            self._fill_grid(matrix, names)
        else:
            self._sync_grid_to_equations()

    def _parsed_equations(self) -> tuple[list[list[Fraction]], tuple[str, ...]]:
        lines = [self.equation_edits[i].text() for i in range(self.m_spin.value())]
        names = self._variable_names(lines)
        matrix = []
        for i, line in enumerate(lines):
            parsed = self.parser.parse(line, self.n_spin.value(), names)
            if not parsed.success:
                raise ValueError(f"Eq {i + 1}: {parsed.error}")
            matrix.append([*parsed.coefficients, parsed.constant])
        return matrix, names

    def _fill_grid(self, matrix: list[list[Fraction]], names: tuple[str, ...]) -> None:
        self.grid.blockSignals(True)
        self.grid.setRowCount(len(matrix)); self.grid.setColumnCount(self.n_spin.value() + 1)
        self.grid.setHorizontalHeaderLabels([*names, "b"])
        for row, values in enumerate(matrix):
            for col, value in enumerate(values):
                self.grid.setItem(row, col, QTableWidgetItem(format_fraction(value)))
        self.grid.blockSignals(False)

    def _sync_grid_to_equations(self, *_: object) -> None:
        if self.tabs.currentIndex() != 1 or not hasattr(self, "equation_edits"):
            return
        for row in range(self.m_spin.value()):
            for col in range(self.n_spin.value() + 1):
                item = self.grid.item(row, col)
                valid = False
                if item is not None:
                    try:
                        parse_fraction(item.text())
                        valid = True
                    except ValueError:
                        pass
                if item is not None:
                    item.setBackground(QBrush(QColor("white" if valid else "#ffd9d9")))
                    item.setToolTip("" if valid else "Enter an integer, decimal, or fraction such as 3/4.")
        self._update_solve_state()
        for row in range(min(self.m_spin.value(), len(self.equation_edits))):
            cells = [self.grid.item(row, col) for col in range(self.n_spin.value() + 1)]
            if any(cell is None or not cell.text().strip() for cell in cells):
                continue
            try:
                values = [parse_fraction(cell.text()) for cell in cells if cell is not None]
            except ValueError:
                continue
            names = [self.grid.horizontalHeaderItem(c).text() for c in range(self.n_spin.value())]
            terms = [f"({format_fraction(value)})*{name}" for value, name in zip(values, names) if value]
            lhs = " + ".join(terms).replace("+ (-", "- (") or "0"
            self.equation_edits[row].setText(f"{lhs} = {format_fraction(values[-1])}")

    def _variable_names(self, lines: list[str]) -> tuple[str, ...]:
        names: list[str] = []
        for line in lines:
            for name in re.findall(r"[A-Za-z_]\w*", line):
                if name.lower() not in {"e"} and name not in names:
                    names.append(name)
        defaults = ("x", "y", "z", "w")
        while len(names) < self.n_spin.value():
            i = len(names)
            names.append(defaults[i] if i < len(defaults) else f"x{i + 1}")
        return tuple(names[:self.n_spin.value()])

    def _parsed_matrix(self) -> tuple[list[list[Fraction]], tuple[str, ...]]:
        if self.tabs.currentIndex() == 1:
            matrix = []
            for r in range(self.m_spin.value()):
                row = []
                for c in range(self.n_spin.value() + 1):
                    item = self.grid.item(r, c)
                    if item is None or not item.text().strip():
                        raise ValueError(f"Grid cell row {r + 1}, column {c + 1} is empty.")
                    row.append(parse_fraction(item.text()))
                matrix.append(row)
            names = tuple(self.grid.horizontalHeaderItem(c).text() for c in range(self.n_spin.value()))
            return matrix, names
        return self._parsed_equations()

    def _update_solve_state(self) -> None:
        if not hasattr(self, "solve_button"):
            return
        try:
            self._parsed_matrix()
            self.solve_button.setEnabled(True)
            self.solve_button.setToolTip("Solve this system")
            if self.tabs.currentIndex() == 0:
                for edit in self.equation_edits[:self.m_spin.value()]:
                    edit.setStyleSheet("")
                    edit.setToolTip("Valid equation")
        except ValueError as exc:
            self.solve_button.setEnabled(False)
            self.solve_button.setToolTip(str(exc))
            if self.tabs.currentIndex() == 0:
                lines = [self.equation_edits[i].text() for i in range(self.m_spin.value())]
                names = self._variable_names(lines)
                for index, edit in enumerate(self.equation_edits[:self.m_spin.value()]):
                    parsed = self.parser.parse(edit.text(), self.n_spin.value(), names)
                    edit.setStyleSheet("border: 1px solid #d33;" if not parsed.success else "")
                    edit.setToolTip(parsed.error or "Valid equation")

    def _solve(self) -> None:
        try:
            augmented, names = self._parsed_matrix()
            strategy = PivotStrategy.LARGEST_ABSOLUTE if self.strategy.currentIndex() else PivotStrategy.FIRST_NONZERO
            self.result = GaussSolver(strategy).solve(augmented)
            self.variable_names = names
            self.step_list.clear()
            for step in self.result.steps:
                self.step_list.addItem(f"{step.index + 1:02d}   {step.operation_label}")
            self._show_step(0)
            self._show_result()
        except Exception as exc:
            QMessageBox.warning(self, "Cannot solve", str(exc))

    def _show_step(self, index: int) -> None:
        if not self.result or not self.result.steps:
            return
        self.current_step = max(0, min(index, len(self.result.steps) - 1))
        step = self.result.steps[self.current_step]
        self.matrix.set_step(step, self.variable_names)
        self.step_list.blockSignals(True)
        self.step_list.setCurrentRow(self.current_step)
        self.step_list.blockSignals(False)
        self.step_label.setText(f"Step {self.current_step + 1} of {len(self.result.steps)} — {step.title}")
        self.prev_button.setEnabled(self.current_step > 0)
        self.first_button.setEnabled(self.current_step > 0)
        self.next_button.setEnabled(self.current_step < len(self.result.steps) - 1)
        self.last_button.setEnabled(self.current_step < len(self.result.steps) - 1)

    def _show_result(self) -> None:
        result = self.result
        names = self.variable_names
        if result.kind is SolutionKind.INCONSISTENT:
            message = "No solution: the equations are inconsistent."
        elif result.kind is SolutionKind.UNIQUE:
            values = ", ".join(f"{names[i]} = {format_fraction(value)}"
                                for i, value in enumerate(result.values) if value is not None)
            message = f"Unique solution: {values}"
        else:
            free = {col: f"t{i + 1}" for i, col in enumerate(result.free_vars)}
            expressions = []
            for col, (constant, coeffs) in enumerate(result.parametric):
                pieces = [format_fraction(constant)] if constant else []
                for j, coefficient in enumerate(coeffs):
                    if coefficient:
                        symbol = free[result.free_vars[j]]
                        pieces.append(f"{format_fraction(coefficient)}·{symbol}")
                expressions.append(f"{names[col]} = " + (" + ".join(pieces) if pieces else "0"))
            message = "Infinitely many solutions: " + ", ".join(expressions)
        self.result_label.setText(f"{message}\nRank = {result.rank}; free variables = {len(result.free_vars)}; "
                                  f"homogeneous = {'yes' if result.homogeneous else 'no'}")

    def _toggle_auto_play(self) -> None:
        if self.play_timer.isActive():
            self.play_timer.stop()
            self.play_button.setText("▶ Auto-play")
        else:
            if self.result is None:
                return
            self.play_timer.start(self.speed.value())
            self.play_button.setText("❚❚ Pause")

    def _auto_advance(self) -> None:
        if not self.result or self.current_step >= len(self.result.steps) - 1:
            self.play_timer.stop(); self.play_button.setText("▶ Auto-play")
            return
        self._show_step(self.current_step + 1)

    def _style_strategy_popup(self, dark: bool) -> None:
        view = self.strategy.view()
        background, foreground = ("#1c2738", "#e7edf7") if dark else ("#ffffff", "#18243a")
        border = "#40516a" if dark else "#d5deea"
        palette = view.palette()
        palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Base, QColor(background))
        palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Window, QColor(background))
        palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Text, QColor(foreground))
        palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.WindowText, QColor(foreground))
        palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Highlight, QColor("#3478dc"))
        palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        view.setPalette(palette)
        view.setAutoFillBackground(True)
        view.setStyleSheet(
            f"QAbstractItemView {{ background-color: {background}; color: {foreground}; "
            f"border: 1px solid {border}; selection-background-color: #3478dc; "
            "selection-color: #ffffff; outline: 0; padding: 4px; }"
            "QAbstractItemView::item { min-height: 26px; padding: 6px 10px; }"
            "QAbstractItemView::item:selected { background-color: #3478dc; color: #ffffff; }"
        )

    def _apply_dark_theme(self) -> None:
        self.setStyleSheet("""
                QWidget { font-family: 'Segoe UI'; font-size: 10pt; color: #e7edf7; }
                QMainWindow { background: #111827; }
                QFrame#settingsCard, QWidget#inputPanel, QWidget#viewerPanel,
                QTabWidget::pane { background: #1c2738; border: 1px solid #334258; border-radius: 12px; }
                QLabel#brandTitle { font-size: 17pt; font-weight: 700; color: #f4f7fc; }
                QLabel#brandSubtitle, QLabel#mutedLabel, QLabel#sectionSubtitle { color: #9aa9bd; }
                QLabel#sectionTitle, QLabel#stepStatus { color: #d9e5f7; font-weight: 700; }
                QLabel#brandBadge { background: #263a57; color: #aad0ff; border-radius: 9px; padding: 7px 11px; }
                QLabel#resultPanel { background: #20324b; border: 1px solid #344f70; border-radius: 9px; padding: 10px 12px; color: #d8eaff; font-weight: 600; }
                QSpinBox, QLineEdit, QComboBox { background: #151f2e; color: #edf2fa; border: 1px solid #40516a; border-radius: 7px; padding: 7px 10px; selection-background-color: #3478dc; }
                QSpinBox { padding-right: 24px; font-size: 12pt; font-weight: 600; }
                QSpinBox::up-button, QSpinBox::down-button { subcontrol-origin: border; subcontrol-position: right; width: 20px; background: #26364c; border-left: 1px solid #40516a; }
                QSpinBox::up-button { subcontrol-position: right top; border-top-right-radius: 6px; }
                QSpinBox::down-button { subcontrol-position: right bottom; border-top: 1px solid #40516a; border-bottom-right-radius: 6px; }
                QSpinBox::up-button:hover, QSpinBox::down-button:hover { background: #334965; }
                QComboBox { padding-right: 30px; }
                QComboBox::drop-down { subcontrol-origin: border; subcontrol-position: top right; width: 26px; background: #26364c; border-left: 1px solid #40516a; border-top-right-radius: 6px; border-bottom-right-radius: 6px; }
                QComboBox::drop-down:hover { background: #334965; }
                QComboBox QAbstractItemView { background: #1c2738; color: #e7edf7; border: 1px solid #40516a; selection-background-color: #3478dc; selection-color: #ffffff; outline: 0; padding: 4px; }
                QComboBox QAbstractItemView::item { min-height: 26px; padding: 6px 10px; }
                QPushButton { background: #263449; color: #e3ebf6; border: 1px solid #40516a; border-radius: 8px; padding: 8px 11px; font-weight: 600; }
                QPushButton:hover { background: #31435c; }
                QPushButton:disabled { color: #75839a; background: #202c3e; }
                QPushButton#solveButton { background: #3478dc; color: #fff; border: 1px solid #3478dc; padding: 9px 18px; font-weight: 700; }
                QTabBar::tab { background: #202c3e; color: #a8b7cb; padding: 8px 14px; border: 1px solid #334258; border-bottom: 0; border-top-left-radius: 7px; border-top-right-radius: 7px; }
                QTabBar::tab:selected { background: #1c2738; color: #a9ceff; font-weight: 700; }
                QTableWidget, QListWidget { background: #151f2e; color: #e7edf7; border: 1px solid #334258; border-radius: 8px; gridline-color: #2a384b; }
                QHeaderView::section { background: #243247; color: #bfccde; padding: 7px; border: 0; border-bottom: 1px solid #3a4b63; }
                QListWidget::item { padding: 7px 9px; border-bottom: 1px solid #28364a; }
                QListWidget::item:selected { background: #28466c; color: #e7f2ff; }
                QScrollArea { background: #172235; border: 1px solid #334258; border-radius: 10px; }
                QSlider::groove:horizontal { background: #334258; height: 5px; border-radius: 2px; }
                QSlider::handle:horizontal { background: #65a3ff; width: 14px; margin: -5px 0; border-radius: 7px; }
                QCheckBox { spacing: 7px; color: #b9c7da; }
            """)
        self._style_strategy_popup(True)
        self.matrix.set_dark_theme(True)

    def _import_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import equations", "",
                    "Equation sources (*.pdf *.png *.jpg *.jpeg *.bmp *.tif *.tiff)")
        if not path:
            return
        self.import_button.setEnabled(False); self.import_button.setText("Reading file…")
        self.import_worker = ImportWorker(path, parent=self)
        self.import_worker.completed.connect(self._preview_import)
        self.import_worker.failed.connect(self._import_failed)
        worker = self.import_worker
        worker.finished.connect(lambda worker=worker: self._import_finished(worker))
        self.import_worker.start()

    def _import_finished(self, worker: ImportWorker) -> None:
        if self.import_worker is worker:
            self.import_worker = None
            self.import_button.setEnabled(True)
            self.import_button.setText("Import image / PDF")
        worker.deleteLater()

    def _preview_import(self, lines: list[str], preview: object) -> None:
        dialog = ImportPreview(lines, preview, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            accepted = [editor.text() for editor in dialog.editors]
            if len(accepted) > 20:
                QMessageBox.warning(self, "Too many equations", "The current limit is 20 equations.")
                return
            self.m_spin.setValue(max(1, len(accepted)))
            # Count variable tokens directly. Boundary-based matching misses
            # variables written with an attached coefficient, such as ``2x``.
            detected = list(dict.fromkeys(
                name for line in accepted
                for name in re.findall(r"[A-Za-z_]\w*", line)
                if name.lower() != "e"
            ))
            self.n_spin.setValue(max(1, min(20, len(detected))))
            self._resize_equations(len(accepted))
            for edit, text in zip(self.equation_edits, accepted):
                edit.setText(text)
            self.tabs.setCurrentIndex(0)

    def _import_failed(self, message: str) -> None:
        QMessageBox.warning(self, "Import failed", message)

    def _export_pdf(self) -> None:
        if not self.result:
            QMessageBox.information(self, "No solution", "Solve a system before exporting.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export solution", "solution.pdf", "PDF (*.pdf)")
        if path:
            try:
                export_solution_pdf(self.result, path)
            except Exception as exc:
                QMessageBox.warning(self, "Export failed", str(exc))

    def _clear(self) -> None:
        if QMessageBox.question(self, "Clear inputs", "Clear all equations and matrix cells?") != QMessageBox.StandardButton.Yes:
            return
        for edit in self.equation_edits:
            edit.clear()
        self.grid.clearContents()
        self.play_timer.stop()
        self.play_button.setText("▶ Auto-play")
        self.result = None
        self.current_step = 0
        self.variable_names = ()
        self.step_list.clear()
        self.step_label.setText("No solution steps yet")
        for button in (self.first_button, self.prev_button, self.next_button, self.last_button):
            button.setEnabled(False)
        self.result_label.setText("Enter equations to begin.")
        self.matrix.step = None; self.matrix.update()
        self._update_solve_state()


from PySide6.QtWidgets import QComboBox


class QComboBoxCompat(QComboBox):
    """Named subclass retained as a seam for future settings wiring."""
