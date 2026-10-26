<div align="center">
  <img src="assets/gauss_icon.png" alt="Gauss Studio application icon" width="112" />
  <h1>Gauss Studio</h1>
  <p><strong>Gaussian elimination, made exact and visual.</strong></p>
  <p>A desktop learning tool that turns every row operation into a step you can inspect.</p>
  <p>
    <a href="https://github.com/V7-Awad/gauss-studio/actions/workflows/tests.yml">
      <img src="https://github.com/V7-Awad/gauss-studio/actions/workflows/tests.yml/badge.svg?branch=main" alt="Windows CI status" />
    </a>
    <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white" alt="Python 3.11 or newer" />
    <img src="https://img.shields.io/badge/Platform-Windows-0078D4?logo=windows&logoColor=white" alt="Windows desktop application" />
  </p>
</div>

---

## What is Gauss Studio?

Gauss Studio is a dark-themed Windows desktop application for exploring systems of linear equations with Gaussian and Gauss–Jordan elimination. It pairs a visual augmented matrix with a readable explanation of each elementary row operation, making it useful for coursework, demonstrations, and checking hand-worked solutions.

The solver uses Python's `fractions.Fraction` throughout. Inputs such as `0.25` are converted to exact rational values, so row operations do not accumulate floating-point rounding error.

## Highlights

- **Exact arithmetic:** pivots, row operations, and final values remain rational numbers.
- **Two input styles:** write equations or fill the augmented matrix directly.
- **Visible algorithm:** inspect the initial matrix, forward elimination, REF, backward elimination, and RREF.
- **Pivot choices:** use the first nonzero pivot or choose the largest absolute pivot in each column.
- **Step navigation:** move through operations, jump to the first or last step, or use auto-play.
- **Readable output:** view fractions or toggle decimal display in the matrix.
- **Complete classification:** distinguish unique, infinite, and inconsistent systems; inspect rank, pivots, free variables, and homogeneous status.
- **Document import:** extract text from PDFs or use OCR on scans and images, then review and edit the detected equations.
- **PDF export:** save a solution walkthrough with its matrix snapshots.
- **Windows packaging:** build a single-file application with the included icon.

## A quick example

Enter this system in the equation editor:

```text
2x + y - z = 8
-3x - y + 2z = -11
-2x + y + 2z = -3
```

Select **Solve**. The walkthrough records each matrix snapshot and operation, then reports:

```text
x = 2, y = 3, z = -1
```

You can select any step in the list, use the navigation buttons or arrow keys, and change the playback speed. The matrix highlights the pivot, source and affected rows, changed cells, and contradictions where they occur.

## Supported equation syntax

Each equation must contain one equals sign. The parser accepts integer, decimal, and fractional coefficients, omitted coefficients such as `x`, unary signs, parentheses, and multiplication by a scalar.

```text
2x + 3y - z = 5
1/2 x + 0.25 y = 3/4
2(x + y) = 6
3x = 2x + 4 - y
```

Write explicit multiplication with `*` when needed, for example `2*x + 3*y = 5`. Nonlinear products such as `x*y` and division by variables are not supported. The editor supports up to 20 equations and 20 variables.

## Understanding the result

Gauss Studio reduces the augmented matrix to reduced row echelon form (RREF) and classifies the system:

| Result | Meaning |
| --- | --- |
| **Unique solution** | Every variable has a determined value. |
| **Infinitely many solutions** | At least one variable is free; the app displays a parametric form. |
| **No solution** | A contradiction appears, such as a zero coefficient row with a nonzero constant. |

The summary also reports the coefficient-matrix rank, the number of free variables, and whether the system is homogeneous.

## Import equations from a PDF or image

The import workflow supports text-based PDFs and scanned pages, plus PNG, JPG/JPEG, BMP, and TIF/TIFF images.

- Text-based PDF pages are read with PyMuPDF.
- Scanned PDFs and images use Tesseract OCR through `pytesseract`.
- Extracted lines are presented in an editable review dialog before they are added to the system.
- OCR runs in a background worker and has a 20-second timeout per page or image.

Tesseract is optional and must be installed separately. The application looks for `tesseract.exe` on `PATH` and in common Windows installation folders. To use a custom installation path in PowerShell:

```powershell
$env:GAUSS_TESSERACT_PATH = "C:\Program Files\Tesseract-OCR\tesseract.exe"
python -m gauss_visualizer
```

Sample files are included for trying both workflows:

- [Sample PDF with selectable text](sample_equations.pdf)
- [Sample equation image for OCR](sample_equations_ocr.png)

## Run from source

### Requirements

- Windows 10 or newer
- Python 3.11 or newer
- Tesseract OCR only if you plan to import scanned PDFs or images

### Setup

From the repository directory, create a virtual environment and install the development dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m gauss_visualizer
```

The application opens with a worked example. Edit the equations or switch to **Matrix grid**, then select **Solve**. Use the **File** menu to export the walkthrough as a PDF.

## Build a Windows executable

With the development dependencies installed, run:

```powershell
./build_windows.ps1
```

The one-file build is written to:

```text
dist/GaussianEliminationVisualizer.exe
```

Tesseract is not bundled. Install it separately to enable OCR in the packaged app. Build output is ignored by Git; attach release executables to a GitHub Release when distributing a build.

## Tests and continuous integration

Run the test suite locally:

```powershell
python -m pytest
```

The suite covers equation parsing, exact row operations, solution classification, repeated PDF/image imports, OCR timeout handling, and recovery after clearing and solving again. GitHub Actions runs the tests on Windows for pushes and pull requests.

## Project layout

```text
src/gauss_visualizer/
├── core/       Exact fractions, equation parsing, elimination, and analysis
├── services/   PDF/image import and solution PDF export
└── ui/         PySide6 interface, matrix visualization, and import worker
assets/         Application icons
tests/          Automated solver, parser, import, and UI recovery tests
```

The `core` package contains the parser, solver, and analyzer. It does not depend on the desktop UI or document/OCR services.

## Troubleshooting

### Image import says Tesseract was not found

Install Tesseract OCR and restart the app. If it is installed outside a common folder, set `GAUSS_TESSERACT_PATH` to its `tesseract.exe` path before launch.

### OCR takes too long or misreads an equation

Try a sharper, higher-contrast image with less surrounding text. OCR can confuse similar characters such as `x` and `×`; inspect and correct every line in the review dialog before accepting it.

### Find the application error log

Application errors are written to the operating system's per-user application data directory, so the app does not need write access to its installation folder.

## Dependencies and licensing

The application uses PySide6 Essentials for its interface, PyMuPDF for PDF text extraction, Pillow for image processing, `pytesseract` for the OCR bridge, and ReportLab for PDF export. Tesseract OCR itself is an optional external program.

This project does not yet include a license file. Without one, GitHub users may view the public source but do not receive explicit permission to reuse or redistribute it. Choose and add a project license before inviting contributions or redistribution. PyMuPDF is offered under AGPL or commercial terms, and PySide6 has LGPL and commercial licensing options; review those terms before distributing the packaged application.
