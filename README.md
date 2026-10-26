<div align="center">
  <img src="assets/gauss_icon.png" alt="Gauss Studio icon" width="112" />
  <h1>Gauss Studio</h1>
  <p><strong>An exact, step-by-step visualizer for Gaussian elimination</strong></p>
  <p>Explore pivots, row operations, and solutions to systems of linear equations.</p>
</div>

---

## Overview

Gauss Studio is a dark-themed Windows desktop application for solving systems of linear equations with Gaussian and Gauss–Jordan elimination. It uses exact rational arithmetic, so intermediate row operations and final answers are represented as fractions rather than rounded decimal approximations.

## Features

- Solve systems with up to 20 equations and 20 variables.
- Enter equations directly or edit an augmented matrix.
- Choose the first nonzero pivot or the largest absolute pivot.
- Follow each row operation and inspect the matrix at every step.
- Navigate steps manually or play them automatically.
- Identify unique, infinite, and inconsistent systems, including rank and free-variable information.
- Import equations from text-based PDFs and use OCR for scanned PDFs and images.
- Review and edit extracted equations before using them.
- Export solution steps to PDF.

## Try the import samples

These files are included to exercise the import workflow:

- [Text-based sample PDF](sample_equations.pdf)
- [Image sample for OCR](sample_equations_ocr.png)

## Run from source

Requires Python 3.11 or newer. On Windows, run these commands from the repository directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m gauss_visualizer
```

The app opens with a sample system. Select **Solve** to view its solution, edit the equations or matrix to try another system, and use the navigation controls or arrow keys to review the row operations. The **File** menu exports the current solution walkthrough as a PDF.

## Importing images and PDFs

Text-based PDFs are read with PyMuPDF. Scanned PDFs and image files (`PNG`, `JPG`, `BMP`, `TIF`) are read with Tesseract OCR through `pytesseract`.

Tesseract OCR is optional and must be installed separately. The application looks for `tesseract.exe` on `PATH` and in common Windows installation folders. For a custom location, set `GAUSS_TESSERACT_PATH` to the full path of `tesseract.exe` before launching the app. For example:

```powershell
$env:GAUSS_TESSERACT_PATH = "C:\Program Files\Tesseract-OCR\tesseract.exe"
python -m gauss_visualizer
```

Each OCR operation has a 20-second timeout. Extracted equations are shown in an editable review window before they are added to the system.

## Build the Windows executable

After installing the development dependencies, run:

```powershell
./build_windows.ps1
```

The single-file executable is created at `dist/GaussianEliminationVisualizer.exe`. Tesseract is not bundled and must be installed separately to use OCR. Build output is excluded from Git; publish executable files as GitHub Release assets if needed.

## Run the tests

```powershell
python -m pytest
```

The test suite covers the exact solver, equation parser, solution analyzer, repeated imports, OCR timeouts, and UI recovery after clearing and solving again. GitHub Actions runs the suite on Windows for pushes and pull requests.

## Project structure

```text
src/gauss_visualizer/
  core/       Equation parsing, exact arithmetic, elimination, and analysis
  services/   Image/PDF import and solution PDF export
  ui/         PySide6 desktop interface and background import worker
assets/       Application icon
tests/        Automated tests
```

## Dependencies and licensing

The interface uses PySide6, PDF import uses PyMuPDF, image processing uses Pillow, and PDF export uses ReportLab. Tesseract OCR is an optional external dependency.

This repository does not currently include a project license. Choose and add a license before inviting others to reuse or redistribute the project. PyMuPDF is available under AGPL or commercial terms; review its licensing requirements before distributing the application or binaries. PySide6 also has LGPL and commercial licensing options.
