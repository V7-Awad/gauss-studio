"""Background workers for slow document extraction."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from gauss_visualizer.services.import_service import extract_equation_lines


class ImportWorker(QThread):
    completed = Signal(list, object)
    failed = Signal(str)

    def __init__(self, path: str, tesseract_cmd: str = "", parent=None) -> None:
        super().__init__(parent)
        self.path = path
        self.tesseract_cmd = tesseract_cmd

    def run(self) -> None:
        try:
            lines, preview = extract_equation_lines(Path(self.path), self.tesseract_cmd or None)
            self.completed.emit(lines, preview)
        except Exception as exc:
            self.failed.emit(str(exc))
