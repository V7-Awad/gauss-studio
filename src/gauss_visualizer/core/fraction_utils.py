"""Exact parsing and readable formatting for rational values."""

from __future__ import annotations

from fractions import Fraction


def parse_fraction(text: str) -> Fraction:
    """Parse integer, decimal, or fraction text without using floating point."""
    value = text.strip().replace("−", "-").replace(",", ".")
    if not value:
        raise ValueError("Enter a number.")
    try:
        if "/" in value:
            numerator, denominator = value.split("/", 1)
            return Fraction(int(numerator.strip()), int(denominator.strip()))
        return Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"Invalid number: {text!r}.") from exc


def format_fraction(value: Fraction) -> str:
    """Format an exact fraction in reduced form."""
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def format_decimal(value: Fraction, places: int = 4) -> str:
    """Format a fraction as a rounded decimal for optional display."""
    return f"{float(value):.{places}f}".rstrip("0").rstrip(".")
