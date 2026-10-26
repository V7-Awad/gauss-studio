from pathlib import Path

import pymupdf
import pytesseract
from PIL import Image

from gauss_visualizer.services.import_service import extract_equation_lines


def test_pdf_text_import_can_be_repeated_without_leaking_document_handles(tmp_path: Path):
    source = tmp_path / "equations.pdf"
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), "2x + y = 5\nx - y = 1")
    document.save(source)
    document.close()

    for _ in range(5):
        lines, preview = extract_equation_lines(source)
        assert lines == ["2x + y = 5", "x - y = 1"]
        assert preview is not None
        preview.close()


def test_image_ocr_uses_timeout_and_normalizes_variables(tmp_path: Path, monkeypatch):
    source = tmp_path / "equations.png"
    Image.new("RGB", (100, 40), "white").save(source)
    calls = []

    def fake_ocr(image, **kwargs):
        calls.append(kwargs)
        return "2X + y = 5\nx - Y = 1"

    monkeypatch.setattr(pytesseract, "image_to_string", fake_ocr)
    for _ in range(3):
        lines, preview = extract_equation_lines(source)
        assert lines == ["2x + y = 5", "x - y = 1"]
        preview.close()

    assert len(calls) == 3
    assert all(call == {"config": "--psm 6", "timeout": 20} for call in calls)


def test_ocr_timeout_returns_actionable_error(tmp_path: Path, monkeypatch):
    source = tmp_path / "equations.png"
    Image.new("RGB", (100, 40), "white").save(source)

    def timeout(*args, **kwargs):
        raise RuntimeError("Tesseract process timeout")

    monkeypatch.setattr(pytesseract, "image_to_string", timeout)
    try:
        extract_equation_lines(source)
    except RuntimeError as exc:
        assert "took too long" in str(exc)
    else:
        raise AssertionError("Expected OCR timeout to be reported")
