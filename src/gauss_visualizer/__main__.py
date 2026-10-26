"""Launch the desktop application."""

import sys
import logging
from pathlib import Path

from PySide6.QtCore import QStandardPaths
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QMessageBox

from gauss_visualizer.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Gauss Studio")
    app.setStyle("Fusion")
    log_directory = Path(QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppLocalDataLocation
    ))
    log_directory.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=str(log_directory / "gauss_visualizer.log"), level=logging.ERROR,
                        format="%(asctime)s %(levelname)s %(message)s")

    def report_exception(exc_type: type[BaseException], exc_value: BaseException,
                         traceback: object) -> None:
        logging.error("Unhandled application exception", exc_info=(exc_type, exc_value, traceback))
        QMessageBox.critical(None, "Unexpected error",
                             f"An unexpected error occurred. Details were saved to gauss_visualizer.log.\n\n{exc_value}")

    sys.excepthook = report_exception
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
