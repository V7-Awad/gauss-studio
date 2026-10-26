"""PDF export for a complete solver run."""

from __future__ import annotations

from pathlib import Path

from gauss_visualizer.core.fraction_utils import format_fraction
from gauss_visualizer.core.models import SolutionResult


def export_solution_pdf(result: SolutionResult, path: str | Path) -> None:
    """Write every matrix snapshot and explanation to a PDF report."""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    report = canvas.Canvas(str(path), pagesize=letter)
    _, height = letter
    for step in result.steps:
        y = height - 52
        report.setFont("Helvetica-Bold", 15)
        report.drawString(48, y, f"Step {step.index + 1}: {step.title}")
        y -= 24
        report.setFont("Helvetica", 10)
        report.drawString(48, y, step.explanation[:100])
        y -= 28
        for row in step.snapshot:
            label = "  ".join(format_fraction(value) for value in row[:-1]) + "  |  " + format_fraction(row[-1])
            report.drawString(60, y, label)
            y -= 18
        report.showPage()
    report.save()
