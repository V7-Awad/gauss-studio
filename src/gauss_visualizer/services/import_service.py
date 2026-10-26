"""Text and image extraction helpers for equation imports."""

from __future__ import annotations

from pathlib import Path
import os
import re
import shutil


SUPPORTED_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


def extract_equation_lines(path: str | Path, tesseract_cmd: str | None = None) -> tuple[list[str], object | None]:
    """Extract candidate equation lines and an optional first-page preview image."""
    source = Path(path)
    if source.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ValueError("Supported files: PDF, PNG, JPG, JPEG, BMP, TIF, TIFF.")
    preview = None
    if source.suffix.lower() == ".pdf":
        try:
            import pymupdf as fitz
        except ImportError as exc:
            raise RuntimeError("PDF import requires PyMuPDF. Install the project requirements.") from exc
        lines: list[str] = []
        import io
        from PIL import Image
        with fitz.open(source) as document:
            for page in document:
                pixmap = page.get_pixmap(matrix=fitz.Matrix(1.4, 1.4), alpha=False)
                with Image.open(io.BytesIO(pixmap.tobytes("png"))) as page_image:
                    if preview is None:
                        preview = page_image.copy()
                text = page.get_text("text")
                if text.strip():
                    lines.extend(text.splitlines())
                else:
                    pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                    with Image.open(io.BytesIO(pixmap.tobytes("png"))) as image:
                        lines.extend(_ocr(image, tesseract_cmd))
        if lines:
            return _clean_lines(lines), preview
        raise RuntimeError("No text or equations were found in this PDF.")
    from PIL import Image, ImageEnhance, ImageOps
    with Image.open(source) as image:
        preview = image.copy()
        prepared = ImageOps.autocontrast(ImageOps.grayscale(image))
        # Upscaling helps small screenshots, but makes already large equation text
        # blur and can cause Tesseract to duplicate symbols or misread digits.
        if max(image.size) < 1200:
            prepared = prepared.resize((image.width * 2, image.height * 2))
    prepared = ImageEnhance.Contrast(prepared).enhance(1.4)
    return _clean_lines(_ocr(prepared, tesseract_cmd)), preview


def _ocr(image: object, tesseract_cmd: str | None) -> list[str]:
    try:
        import pytesseract
    except ImportError as exc:
        raise RuntimeError("Image OCR requires pytesseract. Install the project requirements.") from exc
    tesseract_path = _find_tesseract(tesseract_cmd)
    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
    try:
        lines = pytesseract.image_to_string(image, config="--psm 6", timeout=20).splitlines()
        # OCR often changes a lowercase math variable into uppercase (e.g. x -> X).
        # Keep the common single-letter variables consistent across imported rows.
        return [
            re.sub(
                r"(?<![A-Za-z_])([XYZW])(\d*)(?=\s*(?:[+\-=*/)]|$))",
                lambda match: match.group(1).lower() + match.group(2),
                line,
            )
            for line in lines
        ]
    except pytesseract.pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError(
            "Tesseract OCR is not installed. Install Tesseract OCR, then restart the app. "
            "If it is installed in a custom folder, set GAUSS_TESSERACT_PATH to its tesseract.exe path."
        ) from exc
    except RuntimeError as exc:
        if "timeout" in str(exc).lower():
            raise RuntimeError("OCR took too long. Try a smaller or clearer image, then import again.") from exc
        raise


def _find_tesseract(explicit_path: str | None) -> str | None:
    """Find the OCR executable from explicit configuration, PATH, or common Windows locations."""
    configured = explicit_path or os.environ.get("GAUSS_TESSERACT_PATH")
    if configured:
        return configured
    discovered = shutil.which("tesseract")
    if discovered:
        return discovered
    if os.name == "nt":
        candidates = (
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Tesseract-OCR" / "tesseract.exe",
            Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Tesseract-OCR" / "tesseract.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Tesseract-OCR" / "tesseract.exe",
        )
        for candidate in candidates:
            if candidate.is_file():
                return str(candidate)
    return None


def _clean_lines(lines: list[str]) -> list[str]:
    candidates = [line.strip() for line in lines if "=" in line and line.strip()]
    if not candidates:
        return [line.strip() for line in lines if line.strip()]
    return candidates
