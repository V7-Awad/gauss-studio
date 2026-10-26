import os


def test_clear_resets_solution_and_allows_another_solve(monkeypatch):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication, QMessageBox

    from gauss_visualizer.ui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )

    for _ in range(3):
        window._solve()
        assert window.result is not None
        assert window.step_list.count() > 0
        window.play_timer.start(1000)
        window._clear()
        assert window.result is None
        assert window.step_list.count() == 0
        assert not window.play_timer.isActive()
        assert window.matrix.step is None
        assert all(not button.isEnabled() for button in (
            window.first_button, window.prev_button, window.next_button, window.last_button
        ))
        assert not window.solve_button.isEnabled()
        for editor, value in zip(window.equation_edits, (
            "2x + y - z = 8", "-3x - y + 2z = -11", "-2x + y + 2z = -3"
        )):
            editor.setText(value)

    window.close()
    app.processEvents()
