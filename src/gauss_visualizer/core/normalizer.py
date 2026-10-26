"""Unicode and OCR normalization for equation text."""

from __future__ import annotations

import re


class TextNormalizer:
    """Normalize common mathematical Unicode forms and OCR digit forms."""

    _digit_map = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")

    @classmethod
    def normalize(cls, text: str, *, ocr: bool = False) -> str:
        text = text.translate(cls._digit_map)
        for source, target in (("−", "-"), ("–", "-"), ("×", "*"), ("·", "*"),
                               ("÷", "/"), ("٫", "."), ("،", ".")):
            text = text.replace(source, target)
        if ocr:
            text = re.sub(r"(?<=\d)[oO](?=\d|\s*[xyz])", "0", text)
            text = re.sub(r"(?<=[=+\- ]) [lI](?=\s*\d)", "1", text)
        return text
